#this gives every new  user about 100 roundtrip interactions with the premium models that use openai's most expensive base models
#100000 credits costs Synthia lab 2 bucks in openai fees and we'll charge 5
#as we optimize the architecture, interacting with the models will use less credits!
TRIAL_CREDITS_ON_SIGNUP = 100000
LOGGED_IN_USERS = {}

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


def get_user(user_id):
  return dbutils.get_item(user_id, "users")


def signup(user_id="",
           name="",
           access_level="user",
           email="",
           password="",
           credits=TRIAL_CREDITS_ON_SIGNUP,
           **kwargs):
  user_info = kwargs
  print(user_info)
  if (get_user(user_id)):
    return False
  else:
    return dbutils.upsert(user_id, "users", user_info)


def is_logged_in(user_id):
  return (user_id in LOGGED_IN_USERS)


#horribly insecure, for obvious reasons unless a cookie or token that is something other than the user id is enforced by the API... but it'll get us the user with their sessions which will get us up and running
def get_logged_in_user(user_id):
  if is_logged_in(user_id):
    return LOGGED_IN_USERS[user_id]
  else:
    return False


def login(user_id, password):
  user = get_user(user_id)
  if not user or (user["password"] != password):
    return False
  else:
    from connectors.session import Session, sessions
    if user_id not in sessions["by_user"]:
      starter_session = Session(model_id='super_gpt',
                                user_id=user_id,
                                user_name=user["name"],
                                ai_name="Super GPT")
      starter_session.context += "\n\nNOTE: %USER_NAME% just signed up for Synthia, so Please give him the appropriate congratulations when you reply to their first message!\n\n"

    #Sessions automatically get added to the sessions["by_user"] dict when the constructor is called, so we can now simply compose a user object that's actually userful and send it back to whoever feels like stringifying the sessions list...
    user["active_sessions"] = sessions["by_user"][user_id]
    print(user["active_sessions"][0].SESSION_ID)
    LOGGED_IN_USERS[user_id] = user
    return LOGGED_IN_USERS[user_id] 
