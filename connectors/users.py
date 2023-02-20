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
  dbutils.upsert("admin", "users", initial_users["admin"])
  dbutils.upsert("sammy", "users", initial_users["sammy"])


def get_user(user_id, include_sessions=False):
  user= dbutils.get_item(user_id, "users")
  if user == False:
    return False


  if (include_sessions):
    user["active_sessions"] = Session.refresh_all(user_id)
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
    dbutils.upsert(user_id, "users", user_info)
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
    if not first_time:
      user_sessions = load_state(user_id) #deserializes the user's saved sessions and attaches to sessions["by_user"] in memory if they exist
    else:
      starter_session = Session(model_id='super_gpt',
                                user_id=user_id,
                                user_name=user["name"],
                                ai_name="Super GPT")
      starter_session.context += "\n\nNOTE: %USER_NAME% just signed up for Synthia, so Please give him the appropriate congratulations when you reply to their first message!\n\n"
      starter_session.save()

    #Sessions automatically get added to the sessions["by_user"] dict when the constructor is called, so we can now simply compose a user object that's actually userful and send it back to whoever feels like stringifying the sessions list...
    user["active_sessions"] = sessions["by_user"][user_id]
    print("login complete. "+str(len(user["active_sessions"]))+" sessions loaded")
    LOGGED_IN_USERS[user_id] = user
    return LOGGED_IN_USERS[user_id]

def save_state(user_id):
  return Session.save_all(user_id)
def load_state(user_id):
  return Session.refresh_all(user_id)
  #use this if you want sessions for a user other than the logged in user
def serialize_user(user):
  cloned_user = dbutils.deep_copy(user)
  cloned_user["active_sessions"]= [s.stringify() for s in cloned_user["active_sessions"]]
  #if we did this right, the result is a user as a straight up dict, with their info and their sessions as plain json-like data
  #and if deep_copy did its thing, the result of this call can be modified without mutating the user stored in LOGGED_IN_USERS or the sessions it references
  #deep_copy was written by gpt and is rather opaque so let's see...
  return cloned_user
