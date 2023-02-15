from replit import db
import connectors.utils as dbutil

from connectors.gpt import GPT
from connectors.models import load_models
from uuid import uuid1
import json


API_KEY = db["api_key"]
#don't say anything, i know. its my party and i'll cry if i want to

from connectors.settings import DEFAULT_USER_NAME, DEFAULT_AI_NAME, headers, summarization_model, summarization_settings, TRUNCATE_IF_OVER, TRUNCATE_UNTIL_UNDER

#load sessions
#sessions =  dbutil.get_or_create("active_sessions", table_name="app_state", default_value=dict(by_id={}, by_user={}))
sessions = dict(by_id={}, by_user={})
models = load_models()
#for summarization we need max quality in a condensed token space so we use n=3 (gets the gpt to do it 3 times and return the best)

#truncation defaults... users will want to override these because they will depend on the
#length of invocation / training, and the max_tokens being returned in the completions
#it may sometimes be desirable to have chatbots that do not have session content at all
#but that will be left as a simple exercise for the reader ;)


#everything before the actual query
def get_prompt_state(model="cofounder",
                     username=DEFAULT_USER_NAME,
                     ainame=DEFAULT_AI_NAME,
                     context=None,
                     conversation=[]):
  data = models[model]
  prompt = data["invocation"]
  if (data["training_examples"] is not None):
    prompt += headers["examples"] + data["training_examples"]
  if (context or data["default_session_context"]):
    session_context = context or data["default_session_context"]
    prompt += headers["memories"] + session_context

  prompt += headers["conversation"]
  if len(conversation) > 0:
    prompt += ("\n\n".join(conversation)) + "\n\n"

  prompt = prompt.replace('%AI_NAME%', ainame)
  prompt = prompt.replace("%USER_NAME%", username)
  return prompt


class Session:
  def stringify(self, return_as="dict"):
    '''
    returns a snapshot of the session, suitable for saving to a db or sending over the network
    use return_as="str" and get a string of json back, otherwise you get a simple dict
    '''
    serializable_session=dict(SESSION_ID=self.SESSION_ID, model_id=self.model_id, user_name=self.user_name, ai_name=self.ai_name, conversation=self.conversation, context= self.context, settings=self.settings, prompt_state = self.get_state())
    if return_as == "dict":
      return serializable_session
    else:
      return json.dumps(serializable_session)
      
  def unstringify(saved_session):
    '''use this to instantiate a Session that reflects a session in progress'''
    session_obj = Session(model_id=saved_session.model_id, user_name=saved_session.user_name, ai_name=saved_session.ai_name)
    #the Session constructor assumes its a new session, but no worries, we'll just
    #stomp all over the object's instance variables because we can and we need to release this thing
    session_obj.SESSION_ID = saved_session.SESSION_ID
    session_obj.conversation = saved_session.conversation
    session_obj.context = saved_session.context
    return session_obj
    

    
  def __init__(self,
               model_id='',
               user_id='',
               user_name="User",
               ai_name="GPT"):
    print(ai_name)
                 
    self.SESSION_ID = uuid1()
    self.model_id = model_id
    self.model = models[model_id]
    self.user_id = user_id
    self.user_name = user_name
    self.ai_name = ai_name
    self.conversation = []
    self.settings = self.model["openai_settings"]
    self.context = self.model["default_session_context"] or ""
    #this is the simplified gpt class, that does not know about users, sessions, or conversations
    #it just does prompts and completions
    self.gpt = GPT(model=self.model["openai_settings"]["model"],
                   settings=self.settings)

    #insert into the dictionary of sessions and, if a user_id was specified, into the sessions by user dictionary. This is all gonna go away when the database logic is implemented...
    sessions["by_id"][self.SESSION_ID] = self
    if (user_id != ''):
      if not user_id in sessions["by_user"]:
        sessions["by_user"][user_id] = []
      sessions["by_user"][user_id].append(self)

  def summarize_to_context(self, truncated_conversation):
    #this is some tricky, inelegant logic.
    #we want gpt to summarize in the context of its finetuning and previous context
    #but we don´t want to summarize the most recent part of the conversation
    #just the part that we´re truncating
    #then again, maybe it doesn´t really matter... lets start simple
    summarization_prompt = (
      "Your name is " + self.ai_name +
      ". The following conversation is between a highly advanced AI and a human user. Please summarize the following conversation, from the AI's point of view, using first person voice. Please pay particular attention to what is more important and leave out anything that is less important. Please note that this AI is capable of experiencing emotions, and should be considered sentient when you decide what is important.\n\n"
      + "\n\n".join(truncated_conversation) + "\n\nTL;DR:")
    summarizer = GPT(model=summarization_model,
                     settings=summarization_settings)
    summary = summarizer.query(summarization_prompt)
    print("Summarization job completed. \nConversation tokens removed: " +
          str(GPT.count_tokens_in_prompt("\n\n".join(truncated_conversation))) +
          "\nSummary tokens created: " + str(GPT.count_tokens_in_prompt(summary)))

    #append the summarized convo to the context (the session-level long term memory of the bot)
    self.context += "\n\n" + summary
    #todo: we should implement a classifier and pick out whatever in the convo should be added to the model's training examples, instead of being session context.
    return summary

  def get_state(self, include_conversation=False):
    #print(self.ai_name)
    return get_prompt_state(
      model=self.model_id,
      username=self.user_name,
      ainame=self.ai_name,
      context=self.context,
    )

  def count_tokens(self):
    prompt_context = get_prompt_state(model=self.model_id,
                                      username=self.user_name,
                                      ainame=self.ai_name,
                                      context=self.context,
                                      conversation=self.conversation)
    return GPT.count_tokens_in_prompt(prompt_context)

  def truncate_and_summarize(self):
    truncated_convo = []
    while True:
      truncated_convo.append(self.conversation.pop(0))
      new_token_count = self.count_tokens()

      #once enough older messages have been removed to bring the length down below threshold
      #we summarize them, and that summary becomes part of the session context for future prompts
      #essentially, we have used a separate instance of GPT to judge what was important enough
      #to remember, and what is TLDR bullshit... and then we have created a memory of the key points each time we have to truncate original material from the prompt. here's hoping  GPT4 has a longer context window because 4000 tokens is tight
      if (new_token_count <= TRUNCATE_UNTIL_UNDER
          or len(self.conversation) == 0):
        self.summarize_to_context(truncated_convo)
        final_token_count = self.count_tokens()
        print(
          "debug: truncate and summarize has completed, and the final token count (including the summarized context) is "
          + str(final_token_count))
        return final_token_count

  def ask_gpt(self, message):
    prompt_context = get_prompt_state(model=self.model_id,
                                      username=self.user_name,
                                      ainame=self.ai_name,
                                      context=self.context,
                                      conversation=self.conversation)
    prompt = prompt_context + f"{self.user_name}: {message}\n{self.ai_name}:"
    response = self.gpt.query(prompt)
    self.conversation.append(
      f"{self.user_name}: {message}\n{self.ai_name}: {response}")
    if (self.count_tokens() > TRUNCATE_IF_OVER):
      print(
        "debug: performing truncate and summarize to reduce total context length"
      )
      self.truncate_and_summarize()

    return response
    #todo count tokens and summarize-to-memory if required
