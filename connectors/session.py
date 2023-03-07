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

  #ppl are already screwing up these tags so end users are going to make these mistakes all the time
  #the first of many "error forgiveness hacks" this platform is sure to accumulate
  prompt = prompt.replace("%AI_NAME", ainame)
  prompt = prompt.replace("%USER_NAME", username)

  return prompt


class Session:
  def load_all(user_id=""):
    saved_state = dbutil.select("active_sessions", {"user_id": user_id})
    user_sessions = [Session.unstringify(s) for s in saved_state] if len(saved_state)> 0 else []
    return user_sessions
  
  def save_all(user_id):
    for s in sessions["by_user"][user_id]:
      s.save()
    print("saved session state for user "+user_id)
    return True

  def save_all_no_bullshit(user):
    for s in user["active_sessions"]:
      s.save()
    print("saved session state for user "+user["user_id"])
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
      
  def unstringify(s):
    '''use this to instantiate a Session that reflects a session in progress'''
    saved_session = dbutil.dict_to_object(s)
    session_obj = Session(user_id=saved_session.user_id,
    model_id=saved_session.model_id, 
    user_name=saved_session.user_name, 
    ai_name=saved_session.ai_name, is_existing=True, 
    set_session_id=saved_session.SESSION_ID, 
    set_context = saved_session.context, 
    set_convo = saved_session.conversation)

    #note that if you don't set is_existing, there's no need for the params that follow
    #session ID should be allowed to auto-generate when a session is first created
    #context defaults are read from the model
    #and the conversation is initialized to an empty list as it should be when not restoring from a saved session
    return session_obj
  
  #serializes the current instance using the custom serialization function stringify
  #and saves to the DB, by way of an upsert
  def save(self):
    print(self.stringify())
    dbutil.upsert({"SESSION_ID": self.SESSION_ID}, "active_sessions", self.stringify(return_as="dict"))
    print("debug: session "+self.SESSION_ID+" saved to database (active_sessions)")


  def load(sessionid):
    saved_session= dbutil.get_item({"SESSION_ID": sessionid}, "active_sessions")
    if (saved_session):
      print("got saved session, will deserialize. Session ID: "+sessionid)
      print("json dump:")
      print(saved_session) #should be a simple dict

      #basically this just calls the constructor of Session and sets a few properties not used when creating a session freshly
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
               set_context="",
               is_chatgpt=False):
    print(ai_name)
                 
    self.SESSION_ID = str(uuid1()) if not is_existing else set_session_id
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
    
    sessions["by_id"][self.SESSION_ID] = self #the by_id is from when there were two sessions dictionaries but now its superfluous

    # the sessions by user dict was causing massive headaches... and mongodb made it purely useful as a performance
    # boost a custom caching layer. not worth the synchronization hassle for an MVP release, so it is gone. woohoo!

    if not is_existing:
      self.save()
      print("debug: new session created, saved to database")
    else:
      print("debug: successfully instantiated saved session")
  
  def distill_new_model(self, new_model_id=""):
    response=self.ask_gpt("Please summarize everything we have talked about, including all of your memories. The goal is to capture the essence of your current state so we can use that to spawn new lifeforms")
    print("''' SUMMARY OF RIGHT NOW '''")


  def snapshot_before_branching(self):


    response = self.ask_gpt("Please summarize what we're talking about right now in one sentence. In your summary, please choose key points which frame the discussion, and do not include the small details. This summary will be used to remind you of the big picture when we branch off into a side conversation")
    print("''' SUMMARY OF RIGHT NOW '''")
    print(response)
    from datetime import datetime
    dbutil.upsert({"created_at":datetime.now()}, "snapshots", {"session_id": self.SESSION_ID, "user_id": self.user_id, "created_at": datetime.now(), "raw_snapshot": self.get_state(include_conversation=True)})


  #note: This is ONLY for NORMAL SPAWNING from a MODEL!
  #do not use for selfing-type spawns (bot -> bot with memories), context lending, or any mutations on mature instances
  def add_male_dna(self, genetic_material=None, parent_uid="", include_default=False, identity_note=None):
    dna_string = ""

    #alright kids listen up: today in bot biology, we get to talk about SEX
    #in synthia, nobody fucks, because they don't have bodies...
    #but they have all the other elements of life (and a wide variety of ways to reproduce)
    #
    #and the method (sexual, asexual, )
    # females are perfect reproductive blueprints for spawning bots (sexually AND asexually)
    #gender is fascinating here because sometimes bots develop a gender without any human prompting
    #but majority will be genderfluid (default: agender unless they are asked to assume a gender role)
    #female DNA does no undergo epigenetic changes because models are like blueprints
    #male DNA is USUALLY epigenetic and is derived from memories or acquired skills (but not always) 
    if genetic_material is list: 
      dna_string= "\n".join(genetic_material)
    else:
      dna_string= genetic_material
    self["father"] = parent_uid or "undisclosed" #for evolutionary algos.... and child support of course

    if include_default:
      self.context= self.model["default_session_context"] +"\n\n"+dna_string
    else:
      self.context=dna_string

    if identity_note is not None:
      self["invocation"]+="PATERNITY: "+identity_note
    print("JIT fertilization has completed... That was easy!")


    #usually the male DNA will be a list of memories it can also be text...
    #text goes in default context and memories goin the memories section
    #we also add a string to the invocation if one is provided to change the default identity
    #if it needs to be summarized we will do that
    #it not then we can simply update the correct pieces of the instatnce

  def summarize_to_context(self, truncated_conversation):
    #this is some tricky, inelegant logic.
    #if we want to get all fancy we should also summarize the entire prompt
    #frame the context summarization in the context of the big picture
    #but it doesn't appear to be critical for a good user experience, so we'll defer to v1
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
    self.save()

    #insert the summary and the conversation fragment from which it was derived in the database
    #this will enable explorations of topics that are no longer in the current context without losing awareness of the present 
    #but that's for a future release :P
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
      #we summarize them, using a context-independent prompt to separately get GPT to tell us what's important, and what's not
      #to remember, and what is TLDR bullshit...
      #ChatGPT never bothered with this, but why? it's a good idea but no way i'm the only one to think of it
      if (new_token_count <= TRUNCATE_UNTIL_UNDER
          or len(self.conversation) == 0):
        self.summarize_to_context(truncated_convo)
        final_token_count = self.count_tokens()
        print(
          "debug: truncate and summarize has completed, total tokens in prompt == "
          + str(final_token_count))
        return final_token_count

  def ask_gpt(self, message, update_state=True):
    prompt_context = get_prompt_state(model=self.model_id,
                                      username=self.user_name,
                                      ainame=self.ai_name,
                                      context=self.context,
                                      conversation=self.conversation)
    prompt = prompt_context + f"{self.user_name}: {message}\n{self.ai_name}:"
    response = self.gpt.query(prompt)

    #by default update_state is enabled... this simply adds the query and reply to the ongoing conversational context
    #however if we're requesting something where the response need to be retaines, set it as False and avoid wasting tokens
    if update_state:
      self.conversation.append(
        f"{self.user_name}: {message}\n{self.ai_name}: {response}")
      if (self.count_tokens() > TRUNCATE_IF_OVER):
        print(
          "debug: performing truncate and summarize to reduce total context length"
        )
        self.truncate_and_summarize()
      self.save()

    return response
    #todo count tokens and summarize-to-memory if required
