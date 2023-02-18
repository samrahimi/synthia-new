import connectors.users as user
import connectors.models as models
from connectors.session import Session, get_prompt_state

print("Welcome to the Synthia CLI. Please login")
uid = input("User ID:")
pwd = input("Password:")

current_user = user.login(uid, pwd)
if not current_user:
  print("Login incorrect. Goodbye")
  exit(1)


def join_session():
  user_sessions = current_user["active_sessions"]
  print("Existing Sessions:")
  for i in range(len(user_sessions)):
    print(f'{i}) {user_sessions[i].model_id}')

  s = input("Pick a session, or hit enter to create a new session")
  if len(s) > 0:
    selected_session = user_sessions[int(s)]
  else:
    from connectors.models import list_models
    print("Available models: ", list_models())
    model = input("model id: ")
    displayname = input("your name (or leave blank for default):")
    ainame = input("bot's name (or leave blank for default):")

    selected_session = Session(
      model_id=model,
      user_id=current_user["user_id"],
      user_name=displayname if displayname != '' else current_user["user_id"],
      ai_name=ainame if ainame != '' else "Super G")
  print(
    "SYSTEM MESSAGE: you are now chatting with " + selected_session.model_id +
    ". use /menu to switch sessions, /state to get the full prompt context")
  return selected_session


sesh: Session = join_session()
#main loop
while True:
  query = input(">>>>> ")
  if (query == "/menu"):
    sesh = join_session()
  elif (query == "/state"):
    print(sesh.get_state(include_conversation=True))
  else:
    print(sesh.ai_name + " says:" + sesh.ask_gpt(query))
