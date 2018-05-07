#!/usr/bin/env python3

import logging
import sys
from random import randint
from datetime import datetime
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session
from twilio.rest import Client
from pymongo import MongoClient
from multiprocessing.managers import SyncManager
from queue import Empty

import argparse
class NeuronManager(SyncManager):
    pass
connected = True
alexa_neuron = None
NeuronManager.register('get_alexa_neuron')
manager = NeuronManager(address=('', 4081), authkey=b'daisy')
try:
    manager.connect()
    alexa_neuron = manager.get_alexa_neuron()
    print("Alexa conncted to neuron manager.")
except ConnectionRefusedError:
    print("Alexa not connected to neuron manager.")
    connected = False

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import matplotlib.pyplot as plt

account_sid = "AC2609d37a6f977d53f51357e0de9fd833" # Your Account SID from twilio.com/console
auth_token  = "656562c6b78c5d7fcd559e7f8483d6cc"   # Your Auth Token from twilio.com/console

twilioclient = Client(account_sid, auth_token)


MONGODB_URI = "mongodb://Teddy:password@ds253889.mlab.com:53889/records"
client = MongoClient(MONGODB_URI, connectTimeoutMS=30000)
db = client.get_default_database()
memory_records = db.memory_records


app = Flask(__name__)
ask = Ask(app, "/")
log = logging.getLogger()
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)
logging.getLogger("flask_ask").setLevel(logging.DEBUG)


def get_MEMORY_RECORD(id_num):
    record = memory_records.find_one({"id_num":id_num})
    return record

def push_MEMORY_RECORD(record):
    memory_records.insert_one(record)

def update_MEMORY_RECORD(record, updates):
    memory_records.update_one({'_id': record['_id']},{
        '$set': updates
        }, upsert=False)

def scoreCalc(overall_score, new_score, count):
    overall = ((overall_score)/count)
    return overall

def getMatches(win,res):
    numMatch = 0

    for i in range(len(win)):
        if win[i] == res[i]:
            numMatch = numMatch + 1
    return numMatch

def SendMail(ImgFileName):
    img_data = open(ImgFileName, 'rb').read()
    msg = MIMEMultipart()
    msg['Subject'] = 'Daisy Analytics'
    msg['From'] = 'tewodrostesting@gmail.com'
    msg['To'] = 'tewodrostesting@gmail.com'

    text = MIMEText("Plot for Memory Game")
    msg.attach(text)
    image = MIMEImage(img_data, name=os.path.basename(ImgFileName))
    msg.attach(image)

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login("tewodrostesting@gmail.com", "Team5enee408i")
    s.sendmail('tewodrostesting@gmail.com', 'tewodrostesting@gmail.com', msg.as_string())
    s.quit()

@ask.launch

def welcomemsg():

    welcome_msg = render_template('welcome')
    if connected:
        alexa_neuron.update([('state', 'idle'), ('name', None), ('direction', None)])
    return question(welcome_msg)


@ask.intent("MoveIntent")

def move(direction):

    if direction == 'move':
        return question("In what direction?").reprompt("Can you please give a direction?")

    if connected:
        alexa_neuron.update([('state', 'moving'), ('name', None), ('direction', direction)])

    return question("Moving {}. Can I help you with anything else?".format(direction))


Team5 = ['teddy', 'Vladimir', 'Jessie']

@ask.intent("FollowIntent")

def follow(firstname):

    if firstname in Team5:
        msg = "Tracking for {}. Can I help you with anything else?".format(firstname)
    elif firstname == 'follow':
        return question("Who should I follow?").reprompt("May I please have a name?")
    elif firstname not in Team5:
        if connected:
            alexa_neuron.update([('state', 'tracking'), ('name', firstname), ('direction', None)])
        msg = "I Can't follow {} he is not a member of Team 5".format(firstname)
        return question(msg).reprompt("May I please have another name?")

    if connected:
        alexa_neuron.update([('state', 'tracking'), ('name', firstname), ('direction', None)])

    session.attributes['name'] = firstname

    return question(msg)


@ask.intent("MemoryGameIntent")

def game():

    numbers = [randint(0, 9) for _ in range(5)]
    round_msg = render_template('round', numbers=numbers)
    session.attributes['numbers'] = numbers[::-1]  # reverse

    if connected:
        alexa_neuron.update([('state', 'idle'), ('name', None), ('direction', None)])

    return question(round_msg)


@ask.intent("AnswerIntent", convert={'first': int, 'second': int, 'third': int, 'fourth': int, 'fifth': int})

def answer(first, second, third, fourth, fifth):

    winning_numbers = session.attributes['numbers']
    response_list = [first, second, third, fourth, fifth]
    record = get_MEMORY_RECORD(1)
    count = record['count'] + 1

    if [first, second, third, fourth, fifth] == winning_numbers:
        msg = render_template('win')
        score = 1
        overall_score = record['overall_score'] + score
        record.setdefault("data",[]).append(score*100)

        updates = {
                "score": score,
                "overall_score": overall_score,
                "overall_performance": scoreCalc(overall_score, score, count),
                "count": count,
                "data": record["data"]
        }
        update_MEMORY_RECORD(record, updates)
    else:
        msg = render_template('lose')
        score = (getMatches(winning_numbers, response_list)/5)
        overall_score = record['overall_score'] + score
        record.setdefault("data",[]).append(score*100)
        updates = {
                "score": score,
                "overall_score": overall_score,
                "overall_performance": scoreCalc(overall_score, score, count),
                "count": count,
                "data": record["data"]
        }
        update_MEMORY_RECORD(record, updates)

    return question(msg)


@ask.intent("MemPerformanceIntent")

def performance():

    record = get_MEMORY_RECORD(1)
    OverallScore = record['overall_performance']*100

    return question("Your overall score is {} percent. Would you me to help you with anything else?".format('%.2f'%(OverallScore)))


@ask.intent("PlotIntent")

def plot():

    record = get_MEMORY_RECORD(1)
    count = record['count'] + 1
    data = record['data']

    xaxis = list(range(1, count))
    yaxis = data
    y_mean = [record['overall_performance']*100]*len(xaxis)

    fig, ax = plt.subplots()
    data_line = ax.plot(xaxis,yaxis, label='Data', marker='o')
    mean_line = ax.plot(xaxis,y_mean, label='Mean', linestyle='--')


    ax.set(xlabel='Number of times played (#)', ylabel='Percentage Score (%)',
            title='Memory Game Performance Analytics')
    legend = ax.legend(loc='upper right')

    plt.savefig('MemoryGraph.png')
    SendMail('MemoryGraph.png')

    return question("Emailing data, Can I help you with anything else?").reprompt("May I please have a command?")


@ask.intent("StartExerciseIntent")

def start_exercise():
    session.attributes['exercise'] = 'STARTING'
    return question("Starting exercise session, when you are ready say start.").reprompt("Are you ready now?")

@ask.intent("ExerciseIntent")

def exercise():
    if 'exercise' not in session.attributes or session.attributes['exercise'] != 'STARTING':
        return question("Not in exercise session. Can I help you with anything else?")
    session.attributes['exercise'] = 'IN_PROCESS'
    return question("Start Exercising now.")

@ask.intent("StopExerciseIntent")
def exercise():
    if 'exercise' not in session.attributes or session.attributes['exercise'] != 'IN_PROCESS':
        return question("Not in exercise session. Can I help you with anything else?")
    return question("You did {} squats. Session has been saved. Can I help you with anything else?".format(0)).reprompt("May I please have a command?")

@ask.intent("CallIntent")

def call():
    call = twilioclient.calls.create(
            to="+12404785891",
            from_="+12028043762",
            url="http://demo.twilio.com/docs/voice.xml")
    print(call.sid)
    return question("Making call, Can I help you with anything else?").reprompt("May I please have a command?")


@ask.intent("TextIntent")

def text():

    message = twilioclient.messages.create(
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
    if connected:
        alexa_neuron.update([('state', 'idle'), ('name', None), ('direction', None)])
    return statement("Stopping")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Start Flask-Ask")
    parser.add_argument("--set-ip",
            dest="ip",
            default="localhost",
            help="Specify the IP address to use for initialization")
    parser.add_argument("--set-port",
            dest="port",
            default="5000",
            help="Specify the port to use for initialization")
    args = parser.parse_args()
    app.run(args.ip, int(args.port), debug=True, threaded=True)
