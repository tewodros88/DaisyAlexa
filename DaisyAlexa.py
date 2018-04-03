import sys
import time
import serial

from flask import Flask, render_template
from flask_ask import Ask, statement, question
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
    
def disconnected(client):
    print('Disconnected from Adafruit IO!')
    sys.exit(1)

def message(client, feed_id, payload):

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

@ask.intent("FollowIntent")
def follow(firstname):
    if firstname in Team5:
        msg = "Tracking for {}".format(firstname)
    elif firstname == 'follow':
    	return question("Who should I follow?").reprompt("May I please have a name?")
    elif firstname not in Team5:
        msg = "I Can't follow {} he is not a member of Team 5".format(firstname)
        return question(msg).reprompt("May I please have another name?")
    return statement(msg)

@ask.intent("CallIntent")
def call(firstname):
	msg = "Hello this is Daisy"
	client.publish('daisy-call', msg)



while True:
    time.sleep(10)

if __name__ == "__main__":
    main()
