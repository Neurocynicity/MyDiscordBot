import re
import random

# drawing prompts
people = []
situations = [] # Scenarios will have %p replaced with a random person.  An example scenario would be "%p hitting the griddy"

def ReplacePeopleInSituations(inputStr : str):
    
    for found in re.findall("%p", inputStr):

        inputStr = re.sub(found, random.choice(people), inputStr, 1)

    return inputStr

def GenerateDrawPrompt():

    promptStr = random.choice(situations)

    return ReplacePeopleInSituations(promptStr)
