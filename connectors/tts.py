# Python program to show
# how to convert text to speech
import pyttsx3
  
# Initialize the converter
converter = pyttsx3.init()
  
# Set properties before adding
# Things to say
  
# Sets speed percent 
# Can be more than 100
converter.setProperty('rate', 150)
# Set volume 0-1
converter.setProperty('volume', 0.7)
  
# Queue the entered text 
# There will be a pause between
# each one like a pause in 
# a sentence
converter.say("Hello GeeksforGeeks")
converter.say("I'm also a geek")
  
# Empties the say() queue
# Program will not continue
# until all speech is done talking
converter.runAndWait()
