import connectors.utils as dbutil

from connectors.gpt import GPT
from uuid import uuid1
import json


#don't say anything, i know. its my party and i'll cry if i want to

from connectors.settings import DEFAULT_USER_NAME, DEFAULT_AI_NAME, headers, summarization_model, summarization_settings, TRUNCATE_IF_OVER, TRUNCATE_UNTIL_UNDER

#load sessions
#sessions =  dbutil.get_or_create("active_sessions", table_name="app_state", default_value=dict(by_id={}, by_user={}))
sessions = dict(by_id={}, by_user={})
from connectors.models import get_model
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
  data = get_model(model)
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
  def refresh_all(user_id):
    saved_state = filter(lambda x: x["user_id"] == user_id, dbutil.select_all("active_sessions", get_values=True))
    user_sessions = [Session.unstringify(s) for s in saved_state]
    return user_sessions
  
  def save_all(user_id):
    for s in sessions["by_user"][user_id]:
      s.save()
    print("saved session state for user "+user_id)
    return True

  def stringify(self, return_as="dict"):
    '''
    returns a snapshot of the session, suitable for saving to a db or sending over the network
    use return_as="str" and get a string of json back, otherwise you get a simple dict
    '''
    serializable_session=dict(SESSION_ID=self.SESSION_ID, user_id=self.user_id, model_id=self.model_id, user_name=self.user_name, ai_name=self.ai_name, conversation=self.conversation, context= self.context, settings=self.settings, prompt_state = self.get_state())
    if return_as == "dict":
      return serializable_session
    else:
      return json.dumps(serializable_session)
      
  def unstringify(saved_session):
    '''use this to instantiate a Session that reflects a session in progress'''
    session_obj = Session(user_id=saved_session.user_id,
    model_id=saved_session.model_id, 
    user_name=saved_session.user_name, 
    ai_name=saved_session.ai_name, is_existing=True, 
    set_session_id=saved_session.SESSION_ID, 
    set_context = saved_session.context, 
    set_convo = saved_session.conversation)

    #note that if you don't set is_existing, there's no need for the params that follow, the session initializes to empty 
    #defaults and a fresh sessionid... but if you're loading from a DB, you want those values to reflect the state that was saved
    #and is_existing flag tells the constructor to look at these values (it could have been built without that flag but i'm lazy)
    return session_obj
  
  #serializes the current instance using the custom serialization function stringify
  #and saves to the DB, inserting if never saved before or updating if already in the DB
  #the DB utility expects to receive dicts, lists, and primitive values, and internally performs JSON (de)serialization when 
  #persisting or retrieving data, so there's no need to return_as json and deal with that shit ourselves
  #does stringify / unstringify work properly? not sure because i moved fast, broke things, and left everything publicly mutable 
  #in my classes, and with no type checking enforced... it let me get this thing done quick, but this will need to change for the 1.0
  #release. However tonight is "get the mvp online come hell or high water" night, as in, the hard part's done, it mostly works
  #and a simple UI can be thrown together and attached by way of REST API in the next 4 hours or so... good thing because we are OUT 
  #of money... I bootstrapped this and I've been eating tuna from a can the past 3 days! But as Mr. Kinsella always said in that movie
  #and I've always believed about game-changing apps, "if you build it they will come" - the users, and therefore the investors
  #or maybe even just paying customers from day one. May the force be with Synthia Labs...
  def save(self):
    dbutil.upsert(self.SESSION_ID, "active_sessions", self.stringify(return_as="dict"))
    print("debug: session "+self.SESSION_ID+" saved to database (active_sessions)")
    print("json dump below")
    print(self.stringify(return_as="str"))


  def load(sessionid):
    saved_session= dbutil.get_item(sessionid, "active_sessions")
    if (saved_session):
      print("got saved session, will deserialize. Session ID: "+sessionid)
      print("json dump:")
      print(saved_session) #should be a simple dict

      #basically this just calls the constructor of Session and sets a few properties using the info in the DB copy
      #which has all the data, without the code... using session_id_override lets you manually set session ID instead of 
      #getting a randomly created one on object creation. which then lets you, say, update stale copies of the session in memory
      #instead of creating duplicates. There's something wrong with the architecture but that can be fixed for 1.0
      return Session.unstringify(saved_session)
    else:
      print("error, session not found with id "+ sessionid+" - did you remember to save?")
      return False


  def __init__(self,
               model_id='',
               user_id='',
               user_name="User",
               ai_name="GPT",
               is_existing = False,
               set_session_id=0,
               set_convo=[],
               set_context=""):
    print(ai_name)
                 
    self.SESSION_ID = uuid1() if not is_existing else set_session_id
    self.model_id = model_id
    self.model = get_model(model_id)
    self.user_id = user_id
    self.user_name = user_name
    self.ai_name = ai_name
    self.conversation = [] if not is_existing else set_convo
    self.settings = self.model["openai_settings"]
    if not is_existing: 
      self.context = self.model["default_session_context"] or ""
    else:
      self.context = set_context or ""

    #this is the simplified gpt class, that does not know about users, sessions, or conversations
    #it just does prompts and completions
    self.gpt = GPT(model=self.model["openai_settings"]["model"],
                   settings=self.settings)

    #insert into the dictionary of sessions and, if a user_id was specified, into the sessions by user dictionary. This is all gonna go away when the database logic is implemented...
    
    sessions["by_id"][self.SESSION_ID] = self #its a dict key so we can just update the value no problem
    if not is_existing:

      #if user has no sessions, create an empty list to hold them
      if not user_id in sessions["by_user"]:
        sessions["by_user"][user_id] = []

      #then add the current session to the list, magically updating all references to this list such as the user["sessions"]...
      sessions["by_user"][user_id].append(self)

    if is_existing:
      #check if its already in memory
      if user_id in sessions["by_user"]:
        existing_sesh = len([s for s in sessions["by_user"][user_id] if s.SESSION_ID == self.SESSION_ID]) > 0
        if existing_sesh:
          #do nothing... updating the main sessions dict should also update the reference here
          print("found in memory copy of session "+self.SESSION_ID+" attached to user, updated main sessions dict")
      else:
        if not user_id in sessions["by_user"]:
          sessions["by_user"][user_id] = []

        sessions["by_user"][user_id].append(self)
        print("added session "+self.SESSION_ID+" to user sessions")


    else:
      print("session restored from db, pls add to in memory session dicts after setting SESSION_ID")
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
    from datetime import datetime
    date_string = datetime.now().strftime("%d %B %Y")
    #append the summarized convo to the context (the session-level long term memory of the bot)
    self.context += "\n\n*** Memory added at " + date_string+ " ***\n" + summary
    #todo: we should implement a classifier and pick out whatever in the convo should be added to the model's training examples, instead of being session context.
    return summary

  def get_state(self, include_conversation=False):
    #print(self.ai_name)
    return get_prompt_state(
      model=self.model_id,
      username=self.user_name,
      ainame=self.ai_name,
      context=self.context,
      conversation = self.conversation if include_conversation else []
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
