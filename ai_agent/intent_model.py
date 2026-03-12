import json
import random

with open("ai_agent/training_data.json") as file:
    data = json.load(file)


def get_response(message):

    message = message.lower()

    for intent in data["intents"]:

        for pattern in intent["patterns"]:

            if pattern in message:

                return random.choice(intent["responses"])

    return "I am still learning cricket. Please ask about batting, bowling or fitness."