Currently the python backend only supports openai completions models, not the new chat models. GPT4 at the moment is ONLY a chat model, and then we have 
GPT3.5turbo which is half decent and incredibly cheap.

So instead of messing with horribly bad python code (i'm new to that language - i'm a JS guy), I'm adding APIs for chat models and for non-conversational use cases of any model (i.e. a simple template-style one off prompt response, or a pipeline of such). This is going to be a microservice, maybe a micro frontend if the Webinator works as planned.

What's that you ask? It's like Alexa if Alexa was the best web dev you've ever worked with. She gonna finish this app because my carpal tunnel is extremely severe and I can no longer type