#this gives every new  user about 100 roundtrip interactions with the premium models that use openai's most expensive base models
#100000 credits costs Synthia lab 2 bucks in openai fees and we'll charge 5
#as we optimize the architecture, interacting with the models will use less credits!
TRIAL_CREDITS_ON_SIGNUP = 100000
LOGGED_IN_USERS = {}
from connectors.session import Session, sessions
initial_users = {
  "admin": {
    "user_id": "admin",
    "name": "Sam Rahimi",
    "access_level": "root",
    "email": "sam@synthialabs.com",
    "password": "5yigcs4e",
    "credits": 10000000
  },
  "sammy": {
    "user_id": "sammy",
    "name": "Sam R (Personal Account)",
    "access_level": "user",
    "email": "samrahimi420@gmail.com",
    "password": "120714",
    "credits": 10000000
  }
}

import connectors.utils as dbutils


def add_initial_users():
  dbutils.upsert({"user_id":"admin"}, "users", initial_users["admin"])
  dbutils.upsert({"user_id":"sammy"}, "users", initial_users["sammy"])

def get_user(user_id, include_sessions=False):
  user= dbutils.get_item({"user_id":user_id}, "users")
  if user == None:
    return False


  if (include_sessions):
    user["active_sessions"] = Session.load_all(user_id)
  user["is_logged_in"] = is_logged_in(user_id)
  return user

def signup(user_id="",
           name="",
           access_level="user",
           email="",
           password="",
           credits=TRIAL_CREDITS_ON_SIGNUP,
           **kwargs):
  user_info = {"user_id": user_id, "name": name, "access_level": access_level, "email": email, "password": password, "credits": credits, "extended_profile": kwargs}
  print(user_info)
  if (get_user(user_id) == False):
    dbutils.upsert({"user_id":user_id}, "users", user_info)
    return login(user_id=user_id, password = password, first_time=True)
    print("user created")
  else:
    print("Error: User exists. Try another user_id")
    return None



def is_logged_in(user_id):
  return (user_id in LOGGED_IN_USERS)


#horribly insecure, for obvious reasons unless a cookie or token that is something other than the user id is enforced by the API... but it'll get us the user with their sessions which will get us up and running
def get_logged_in_user(user_id):
  if is_logged_in(user_id):
    return LOGGED_IN_USERS[user_id]
  else:
    return False


def login(user_id, password, first_time=False):
  user = get_user(user_id)
  if not user or (user["password"] != password):
    return False
  else:
    if first_time:
      starter_session = Session(model_id='super_gpt',
                                user_id=user_id,
                                user_name=user["name"],
                                ai_name="Super GPT")
      starter_session.context += "\n\nNOTE: %USER_NAME% just signed up for Synthia, so Please give him the appropriate congratulations when you reply to their first message!\n\n"
      starter_session.save()

    user_sessions = load_state(user_id) 
    #Sessions automatically get added to the sessions["by_user"] dict when the constructor is called, so we can now simply compose a user object that's actually userful and send it back to whoever feels like stringifying the sessions list...
    user["active_sessions"] = user_sessions
    print("login complete. "+str(len(user["active_sessions"]))+" sessions loaded")
    LOGGED_IN_USERS[user_id] = user
    return LOGGED_IN_USERS[user_id]

#don't call this unless you have a live user object... 
#otherwise if you load a user with get_user just to do this you'll nuke the in memory sessions and replace with
#the previously saved version, which you will then resave. 
#like a goddamn circle jerk, or that moron in ancient greece who was sentenced to push a rock uphill for all eternity
#see, this is why i can't work in silicon valley anymore. in 2008 it was cool, boys could be boys
#the engineering lab was like the engineering lounge when I went to college
#girls were totally welcome to be engineers. sexual harassment wasn't really a thing..
#it was like "oh, i'm going to hit on her at the work party"
#next day, she's like "omg you had WAY too many beer last night"
#i'm like "I know... the boss saw me doing lines of coke and he gave me $100 to take a taxi back to sf and followed me to make sure i didn't drive"
#girl: "so where's your car now?"
#me: "oh, its here... I gave the taxi 20 bucks to circle the block and drove anyway"
#girl: "so where's the other 80?"
#me: "oh, i got more coke and went to a better party"
#girl: "oh too bad, i went home with your colleague who you hate"
#me: FML. i bet that guy 20 bucks that's i'd get to bang you instead, brb, i need to hit the atm
#this was for a startup that i left with unvested options and that went IPO later
#10 years later, dating new girl: 
#girl: my kids are so addicted to roblox... you made that game?
#me: ya, me and 5 guys, I wish i hadn't quit, i'd be rich now
#me: but i couldn't stand that asshole guy who kept breaking my code to get the promotion
#girl: (yells at son) you didn't do your chores
#kid: let me just finish killing these guys in roblox
#me: (walks into living room) holy shit, what system is this
#kid: xbox x
#me: wait... THIS is roblox
#kid: ya its like the most popular game in my school (as he shoots people in 4k on a big screen tv). wanna play?
#me: nah, i suck at roblox, i just wrote the code
#FML
def save_state(user):
  return Session.save_all_no_bullshit(user)

def load_state(user_id):
  return Session.load_all(user_id)
  #use this if you want sessions for a user other than the logged in user
def serialize_user(user):
  cloned_user = dbutils.deep_copy(user)
  del cloned_user["active_sessions"] #they don't clone right
  del cloned_user["_id"] #that ObjectID shit from mongo doesn't serialize well so we use our own index columns
  sessions=[]
  for s in user["active_sessions"]:
    sessions.append(s.stringify())
  cloned_user["active_sessions"]= sessions #the serialized session list
  #if we did this right, the result is a user as a straight up dict, with userinfo and a list of sessions...
  return cloned_user
