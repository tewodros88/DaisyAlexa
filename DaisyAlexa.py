import logging
import sys
import serial
from random import randint
from datetime import datetime
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session
from twilio.rest import Client
from pymongo import MongoClient


account_sid = "AC2609d37a6f977d53f51357e0de9fd833" # Your Account SID from twilio.com/console
auth_token  = "656562c6b78c5d7fcd559e7f8483d6cc"   # Your Auth Token from twilio.com/console

client = Client(account_sid, auth_token)


MONGODB_URI = "mongodb://Teddy:password@ds253889.mlab.com:53889/records"
client = MongoClient(MONGODB_URI, connectTimeoutMS=30000)
db = client.get_default_database()
records = db.records


app = Flask(__name__)
ask = Ask(app, "/")
log = logging.getLogger()
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)
logging.getLogger("flask_ask").setLevel(logging.DEBUG)

def getRECORD(id_num):
    record = records.find_one({"id_num":id_num})
    return record

def pushRECORD(record):
    records.insert_one(record)

def updateRecord(record, updates):
    records.update_one({'_id': record['_id']},{
                              '$set': updates
                              }, upsert=False)

def scoreCalc(prev_score, new_score, count):
    overall = ((prev_score + new_score)/count)
    return overall
    
@ask.launch
def welcomemsg():

    welcome_msg = render_template('welcome')

    return question(welcome_msg)

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

Team5 = ['teddy', 'Vladimir', 'Jessie']

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
    response_list = [first, second, third]
    record = getRECORD(1)
    prev_score = record['score']
    count = record['count'] + 1
    
    if [first, second, third] == winning_numbers:
        msg = render_template('win')
        score = 1
        updates = {
            "score": score,
            "overall_performance": scoreCalc(prev_score, score, count),
            "count": count 
        }
        updateRecord(record, updates)
    else:
        msg = render_template('lose')
        score = (3 - len(list(set(winning_numbers) - set(response_list))))/3
        updates = {
            "score": score,
            "overall_performance": scoreCalc(prev_score, score, count),
            "count": count 
        }
        updateRecord(record, updates)

    return question(msg)

@ask.intent("CallIntent")
def call():

	call = client.calls.create(
		to="+12404785891", 
		from_="+12028043762",
	    url="http://demo.twilio.com/docs/voice.xml")
	print(call.sid)

	return question("Making call, Can I help you with anything else?").reprompt("May I please have a command?")

@ask.intent("TextIntent")
def text():

	message = client.messages.create(
		to="+12404785891", 
		from_="+12028043762",
		body="Hello from Daisy")
	print(message.sid)

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