import logging
import sys
import time
import serial
from random import randint
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session
# Import Adafruit IO MQTT client.
from Adafruit_IO import MQTTClient

app = Flask(__name__)
ask = Ask(app, "/")

log = logging.getLogger()
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)
logging.getLogger("flask_ask").setLevel(logging.DEBUG)

ADAFRUIT_IO_KEY      = '317bca24bd7a4e89ba35110c24190573'
ADAFRUIT_IO_USERNAME = 'tewodros'  

def connected(client):
    print('Connected to Adafruit IO!  Listening for Daisy changes...')
    client.subscribe('daisy-call')
    client.subscribe('daisy-text')
    
def disconnected(client):
    print('Disconnected from Adafruit IO!')
    sys.exit(1)

def message(client, feed_id, payload):
    print('Feed {0} received new value: {1}'.format(feed_id, payload))

# Create an MQTT client instance.
client = MQTTClient(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

client.on_connect    = connected
client.on_disconnect = disconnected
client.on_message    = message

client.connect()
client.loop_background()

@ask.launch
def welcomemsg():
    welcome_msg = render_template('welcome')
    return question(welcome_msg)

Team5 = ['teddy', 'Vladimir', 'Jessie']

@ask.intent("MoveIntent")
def move(direction):
    if direction == 'left':
        msg = "moving left"
    elif direction == 'right':
        msg = "moving right"
    elif direction == 'forward':
        msg = "moving forward"
    elif direction == 'backward':
        msg = "moving backward"
    elif direction == 'move':
        return question("In what direction?").reprompt("Can you please give a direction?")
    return question("Moving {}. Can I help you with anything else?".format(direction))

@ask.intent("FollowIntent")
def follow(firstname):
    if firstname in Team5:
        msg = "Tracking for {}. Can I help you with anything else?".format(firstname)
    elif firstname == 'follow':
    	return question("Who should I follow?").reprompt("May I please have a name?")
    elif firstname not in Team5:
        msg = "I Can't follow {} he is not a member of Team 5".format(firstname)
        return question(msg).reprompt("May I please have another name?")
    return question(msg)

@ask.intent("MemoryGameIntent")
def game():

    numbers = [randint(0, 9) for _ in range(3)]
    round_msg = render_template('round', numbers=numbers)
    session.attributes['numbers'] = numbers[::-1]  # reverse

    return question(round_msg)

@ask.intent("AnswerIntent", convert={'first': int, 'second': int, 'third': int})

def answer(first, second, third):
    winning_numbers = session.attributes['numbers']
    if [first, second, third] == winning_numbers:
        msg = render_template('win')
    else:

        msg = render_template('lose')
    return statement(msg)

@ask.intent("CallIntent")
def call():
    client.publish('daisy-call', 1)
    return question("Making call, Can I help you with anything else?").reprompt("May I please have a command?")

@ask.intent("TextIntent")
def call():
    client.publish('daisy-text', 1)
    return question("Sending text, Can I help you with anything else?").reprompt("May I please have a command?")

@ask.intent("YesIntent")
def yes():
    return question("What would you like to do?").reprompt("May I please have a command?")

@ask.intent("NoIntent")
def no():
    return statement("Ok. goodbye")

@ask.intent("AMAZON.StopIntent")
def stop():
    return statement("Stopping")
    
if __name__ == '__main__':
    app.run(debug=True)