import openai
import tiktoken
from replit import db

class GPT:

  def count_tokens_in_prompt(string: str,
                             encoding_name: str = "p50k_base") -> int:
    """Returns the number of tokens in a text string. Note that the default encoding_name applies to davinci-3, davinci-2, chatgpt (a davinci-2 knockoff), and any of the code models. Older GPT3 variants like instruct or davinci 1, or any of the free GPTs like j6b, neo, should use gpt2 as the encoding_name"""
    print(
      "Starting the token count... if this takes forever, just short circuit this with a simple word count, divide by 2, and say fuck it in the name of being agile"
    )
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    print("Token count complete, value: " + str(num_tokens))
    return num_tokens

  def __init__(self,
               api_key=db["api_key"],
               model="text-davinci-003",
               prefix="",
               settings=None):
    if settings is not None:
      self.default_settings = settings
    else:
      self.default_settings = {
        "temperature": 0.85,
        "n": 1,
        "max_tokens": 3000,
        "stop": "*******"
      }

    self.model = model
    self.prefix = prefix
    openai.api_key = api_key

  def query(self, prompt, append_to_prefix=False, settings_override=None):
    completions = openai.Completion.create(
      model=self.model,
      #engine="code-davinci-002",
      prompt=prompt if self.prefix == "" else self.prefix + prompt,
      max_tokens=self.default_settings["max_tokens"],
      n=self.default_settings["n"],
      temperature=self.default_settings["temperature"],
      stop=self.default_settings["stop"])

    reply = completions.choices[0].text
    if append_to_prefix:
      self.prefix = prompt + reply + "\n"

    return reply


class ChatGPT:

  def __init__(self,
               api_key=db["api_key"],
               model="text-davinci-003",
               bootstrap="",
               memories="",
               instance_memories="",
               use_names=True,
               user_name="User",
               ai_name="Doctor G",
               settings=None,
               conversation=None):
    openai.api_key = api_key
    self.base_model = model
    self.user_name = user_name if user_name is not None else "User"
    self.ai_name = ai_name if ai_name is not None else "Doctor G"

    self.model = model
    self.bootstrap = bootstrap  #the zeroshot or few-shot invocation that is always at the beginning of a request to the davinci
    self.memories = memories  #this should be a summarized or bulleted tldr of the context from previous sessions
    self.zeroshot = f"{self.bootstrap}\n\n{self.memories}"
    if conversation is not None and len(conversation.messages) > 0:
      self.current_context = "\n\n".join(conversation.messges)
    else:
      self.current_context = ""  #the interaction W#ITHOUT the zeroshot (no boostrap or past memories)
    self.conversation = conversation
    self.use_names = use_names
    if settings is not None:
      self.default_settings = settings

    else:
      self.default_settings = {
        "temperature": 0.85,
        "n": 1,
        "stop": ["*****", "SYSTEM_MESSAGE:"],
        "max_tokens": 1024
      }
    print("Firing up. Model is " + self.model)

  def chat(self,
           query="",
           oneoff=False,
           gpt_name="",
           user_name="",
           delimiter="\n\n",
           use_chatgpt_delimiter=False):
    suffix = "<|im_end|>" if use_chatgpt_delimiter else ""

    if not oneoff:

      #TODO: check token length of self-prompt after updating the state
      #if it is too big, truncate it from behind (sounds hot)
      #take a chunk of old messages until you're under the limit
      #defined in instance settings, compress into a tldr,
      #add to memories, refresh the prompt
      if (self.use_names):
        #to keep the pattern username: message
        #                    gptname: response

        self.current_context = f"{self.current_context}{delimiter}{user_name}: {query}{suffix}{delimiter}{gpt_name}:"
        self.prompt = self.zeroshot + self.current_context
      else:
        #for code, etc, we don't want the movie script
        self.current_context = f"{self.current_context}{delimiter}{query}"
        self.prompt = self.zeroshot + self.current_context

      #print(self.prompt)
    else:
      self.current_context = query
      self.prompt = self.current_context
      print(self.prompt)

    completions = openai.Completion.create(
      model=self.model,
      #engine="code-davinci-002",
      prompt=self.prompt,
      max_tokens=self.default_settings["max_tokens"],
      n=self.default_settings["n"],
      temperature=self.default_settings["temperature"],
      stop=self.default_settings["stop"])
    reply = completions.choices[0].text
    self.current_context = self.current_context + reply + suffix
    if self.conversation is not None:
      self.conversation.append(query, reply, gpt_name, user_name)

    return reply.replace(suffix, "")  #don't show in the interface

  def get_state(self):
    return self.zeroshot + self.current_context

  def model_settings(
      self,
      basemodel="davinci-003",
      type="language",
      architecture="gpt.latest",
      api="openai.completions",
      purpose="knowledge, chatbot, issue_commands, format_commands, code_discussion, image_generation, text_generation, text_summarization, text_explanation, task_delegation, sysadmin",
      finetune_method="fewshot",
      finetune_architecture="prompt_examples",
      prompting_strategy="socratic",
      has_session_memory=True,
      has_session_recall=True,
      ground_truths_group="origin_story",
      maxlength_before_prune=2500,
      pruning_strategy="snapshot_remember_truncate",
      maxlength_in_ui=False,
      **kwargs):
    self.settings = kwargs
    return self.settings
