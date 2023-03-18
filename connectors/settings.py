#all the constants and defaults 
DEFAULT_USER_NAME = "User"
DEFAULT_AI_NAME = "GPT"
headers = {
  "examples": "\n***** EXAMPLES *****\n",
  "memories": "\n***** SESSION CONTEXT *****\n",
  "conversation": "\n***** BEGIN CURRENT SESSION *****\n"
}
summarization_settings = {
  "temperature": 0.85,
  "n": 3,
  "max_tokens": 250,
  "stop": "*******"
}
summarization_model = "text-davinci-003"
TRUNCATE_IF_OVER = 2500
TRUNCATE_UNTIL_UNDER = 1500
