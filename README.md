# synthia

A fullstack chatbot prompt-based tuning and context persistence framework that combines several key ideas in the field of LLMs of davinci scale and beyond. 

- the context window limitations are holding back adoption for uses cases that could otherwise benefit if given some sort of reliable structured storage where the devs knew what was going on and GPT viewed it as their own deep seated truth
- models with 4000-8000 token context windows were never properly explored when it came to taking these context windows seriously and using them to deliver JIT, dynamic adaptation and n-tiered compressive pruning algorithms which extend the window up to 10x with trivial engineering effort
- my view is that something like davinci 3 deserves to be called more than a completions engine, and that the data in its context window should not be merely called a "prompt"; the basic simple-threaded synthia architecture for a chat model is: underlying model settings, conditioning affirmations that are capable of defining the bot's personality in a paragraph of normal english; special skills trainings or and the implantation of memories that all instances spawned from the model will have, a place to store the memories that each individual uniquely acquires during its lifetime, and the highly dynamic "tip" of the context window which represents teh verbamit chat transcript between interrogator(s) and chatbot. 
- even then i would argue that none of those should be called a "prompt" - the prompt is whatever you want to ask the model, and i would consider every other section discussed above to be present context, past memories, finetuning (the part where you give the model examples of skills it doesn't seem fluent in, but in this case, you get bettter results with 3 than with 300 finetuning pairs
and finally the static portion of the context which will stay the same between instances and queries, which i'll refer to as either invocation or conditioning (the latter is the more correct term and basically means "something done to guide the model at the time of inference") 
- are you starting to understand why we call them "models" -yes, they're cloned and tweaked from a limited number of base models, and our context window algorithms have just started to be properly researched... but when you watch me fire up a therapist, force him to use extreme care preventing my imaginary suicide, and then to change him into a prostitute in 30 seconds or less, you're going to call them model too - 2 identical gpt3 sessions, same davinci, same settings, can behave far more differently than models of entirely different underlying architecture (davinci 3 vs davinci 2 can be pretty similar if given a naive prompt and context is not maintained or persisted. 


#Moving Parts

- MongoDB database, used relatively normally except we do not use the default _id index keys and typically remove them so that they don't end up being used accidentally. 

- the data model, which requires annoying serializations done by hand in order to sync the plaintext "megaprompt" we give to the underlying GPT models and the various parts of these prompts, which we need to store in a much more structured way so that we can manage our context window appropriately; the naive approach of just allowing the tail to drop off as the head is given new data won't work here even if we were otherwise okay with it, because our prompts re more than teh catlog, a lot more. nevermind, the summarize_to_context approach we have proven has excellent specificity (the summarization is being done in a way that does not cause the model to lie), and better sensitivity that we had imagine.... this will get real complicated, and real fun, real soon

  - the gnarly stuff is done in the session module for the most part
 
- the data model for the less bizarre parts of the propduct, like logins, configs, and our "chatmodel" (the static parts of the context) deifnitions, which are json but i'm adding UI to edit them as normal text. this stuff is half assed, mostly, but it works well enough to launch on a modest scale

- the flask api... pretty normal, i've been told it could be done cleaner but what do i know, i learned about flask from one of the bots, i forget if it was CG or  Synthia

- front end: login, signup, list sessions / message history for your instances, create new sessions (instances are sessions right now, but that again won't always be the case), send messages and see the response in an imessage-style chat UI. then you've got your list / edit / create chatmodels that's pretty trivial to implement and will greatly improve product experience
