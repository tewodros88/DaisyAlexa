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
import io
import time

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
exercise_records = db.exercise_records


app = Flask(__name__)
ask = Ask(app, "/")
log = logging.getLogger()
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)
logging.getLogger("flask_ask").setLevel(logging.DEBUG)


def clear_session_attributes():
    if 'user' in session.attributes:
        currUser = session.attributes['user']
        session.attributes.clear()
        session.attributes['user'] = currUser
    else:
        session.attributes.clear()

def get_MEMORY_RECORD(name):
    record = memory_records.find_one({"user":name})
    return record

def push_MEMORY_RECORD(record):
    memory_records.insert_one(record)

def update_MEMORY_RECORD(record, updates):
    memory_records.update_one({'_id': record['_id']},{
        '$set': updates
        }, upsert=False)

def get_EXERCISE_RECORD(name):
    record = exercise_records.find_one({"user":name})
    return record

def push_EXERCISE_RECORD(record):
    exercise_records.insert_one(record)

def update_EXERCISE_RECORD(record, updates):
    exercise_records.update_one({'_id': record['_id']},{
        '$set': updates
        }, upsert=False)

def scoreCalc(overall_score, count):
    overall = ((overall_score)/count)
    return overall

def getMatches(win,res):
    numMatch = 0

    for i in range(len(win)):
        if win[i] == res[i]:
            numMatch = numMatch + 1
    return numMatch

def SendMail(mem_plot, ex_plot):
    msg = MIMEMultipart()
    msg['Subject'] = 'Daisy Analytics'
    msg['From'] = 'tewodrostesting@gmail.com'
    msg['To'] = 'tewodrostesting@gmail.com'

    text = MIMEText("Plots of Collected Data for " + session.attributes['user'])
    msg.attach(text)
    if mem_plot is not None:
        mem_plot_img = MIMEImage(mem_plot)
        mem_plot_img.add_header('Content-Disposition', 'attachment', filename="MemoryGraph.png")
        msg.attach(mem_plot_img)
    if ex_plot is not None:
        ex_plot_img = MIMEImage(ex_plot)
        ex_plot_img.add_header('Content-Disposition', 'attachment', filename="ExerciseGraph.png")
        msg.attach(ex_plot_img)


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
    clear_session_attributes()
    if direction == 'move':
        return question("In what direction?").reprompt("Can you please give a direction?")

    if connected:
        alexa_neuron.update([('state', 'moving'), ('name', None), ('direction', direction)])

    return question("Moving {}. Can I help you with anything else?".format(direction))


Team5 = ['Jessie', 'teddy', 'Vladimir']

@ask.intent("FollowIntent")

def follow(firstname):
    clear_session_attributes()
    if firstname in Team5:
        msg = "Tracking for {}. Can I help you with anything else?".format(firstname)
    elif firstname == 'follow' or firstname is None:
        if 'user' in session.attributes:
            firstname = session.attributes['user']
            msg = "Tracking for {}. Can I help you with anything else?".format(firstname)
        else:
            return question("Who should I follow?").reprompt("May I please have a name?")
    elif firstname not in Team5:
        if connected:
            alexa_neuron.update([('state', 'tracking'), ('name', firstname), ('direction', None)])
        msg = "I Can't follow {} he is not a member of Team 5".format(firstname)
        return question(msg).reprompt("May I please have another name?")

    if connected:
        alexa_neuron.update([('state', 'tracking'), ('name', firstname), ('direction', None), ('user', firstname)])

    session.attributes['user'] = firstname

    return question(msg)


@ask.intent("MemoryGameIntent")

def game():
    clear_session_attributes()
    numbers = [randint(0, 9) for _ in range(5)]
    round_msg = render_template('round', numbers=numbers)
    session.attributes['numbers'] = numbers[::-1]  # reverse

    if connected:
        alexa_neuron.update([('state', 'idle'), ('name', None), ('direction', None)])

    return question(round_msg)


@ask.intent("AnswerIntent", convert={'first': int, 'second': int, 'third': int, 'fourth': int, 'fifth': int})

def answer(first, second, third, fourth, fifth):
    if 'numbers' not in session.attributes:
        return question("Not in memory game session. Can I help you with anything else?")

    winning_numbers = session.attributes['numbers']
    response_list = [first, second, third, fourth, fifth]

    if 'user' not in session.attributes:
        msg = render_template('not_tracking')
        if [first, second, third, fourth, fifth] == winning_numbers:
            msg = msg + ' ' + render_template('win')
        else:
            msg = msg + ' ' + render_template('lose')
        return question(msg)

    record = get_MEMORY_RECORD(session.attributes['user'])
    if record is None:
        newRecord = {
            "user": session.attributes['user'],
            "id_num": Team5.index(session.attributes['user']),
            "count": 0,
            "overall_score": 0,
            "overall_performance": 0,
            "score": 0,
            "data": []
        }
        push_MEMORY_RECORD(newRecord)

    if [first, second, third, fourth, fifth] == winning_numbers:
        record = get_MEMORY_RECORD(session.attributes['user'])
        count = record['count'] + 1
        msg = render_template('win')
        score = 1
        record.setdefault("data",[]).append(score*100)
        overall_score = sum(record["data"])

        updates = {
                "score": score,
                "overall_score": overall_score,
                "overall_performance": scoreCalc(overall_score, count),
                "count": count,
                "data": record["data"]
        }
        update_MEMORY_RECORD(record, updates)
    else:
        record = get_MEMORY_RECORD(session.attributes['user'])
        count = record['count'] + 1
        msg = render_template('lose')
        score = (getMatches(winning_numbers, response_list)/5)
        record.setdefault("data",[]).append(score*100)
        overall_score = sum(record["data"])
        updates = {
                "score": score,
                "overall_score": overall_score,
                "overall_performance": scoreCalc(overall_score, count),
                "count": count,
                "data": record["data"]
        }
        update_MEMORY_RECORD(record, updates)


    clear_session_attributes()

    return question(msg)


@ask.intent("MemPerformanceIntent")

def memPerformance():
    clear_session_attributes()

    if 'user' not in session.attributes:
        return question("Not tracking anyone right now. Can I help you with anything else?")

    record = get_MEMORY_RECORD(session.attributes['user'])

    if record is None:
        return question("There are no records for this user. Can I help you with anything else?")

    OverallScore = record['overall_performance']

    return question("Your overall score is {} percent. Can I help you with anything else?".format('%.2f'%(OverallScore)))


@ask.intent("PlotIntent")

def plot():
    clear_session_attributes()

    if 'user' not in session.attributes:
        return question("Not tracking anyone right now. Can I help you with anything else?")

    mem_record = get_MEMORY_RECORD(session.attributes['user'])
    ex_record = get_EXERCISE_RECORD(session.attributes['user'])

    if mem_record is None and ex_record is None:
        return question("There are no records for this user. Can I help you with anything else?")

    mem_plot = None
    ex_plot = None

    if mem_record is not None:
        count = mem_record['count'] + 1
        data = mem_record['data']

        xaxis = list(range(1, count))
        yaxis = data
        y_mean = [mem_record['overall_performance']]*len(xaxis)

        fig, ax = plt.subplots()
        data_line = ax.plot(xaxis,yaxis, label='Data', marker='o')
        mean_line = ax.plot(xaxis,y_mean, label='Mean', linestyle='--')


        ax.set(xlabel='Number of times played (#)', ylabel='Percentage Score (%)',
                title='Memory Game Performance Analytics')
        legend = ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        mem_img = io.BytesIO()

        plt.savefig(mem_img, format="png", bbox_extra_artists=(legend,), bbox_inches='tight')
        mem_img.seek(0)

        plt.close(fig)

        mem_plot = mem_img.getvalue()
        mem_img.close()

    if ex_record is not None:
        count = ex_record['count'] + 1
        data = ex_record['data']

        xaxis = list(range(1, count))
        yaxis = data
        y_mean = [ex_record['overall_performance']]*len(xaxis)

        fig, ax = plt.subplots()
        data_line = ax.plot(xaxis,yaxis, label='Data', marker='o')
        mean_line = ax.plot(xaxis,y_mean, label='Mean', linestyle='--')


        ax.set(xlabel='Number of times exercised (#)', ylabel='Repetitions (#)',
                title='Exercise Performance Analytics')
        legend = ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        ex_img = io.BytesIO()

        plt.savefig(ex_img, format="png", bbox_extra_artists=(legend,), bbox_inches='tight')
        ex_img.seek(0)

        plt.close(fig)

        ex_plot = ex_img.getvalue()
        ex_img.close()

    SendMail(mem_plot, ex_plot)


    return question("Emailing data, Can I help you with anything else?").reprompt("May I please have a command?")


@ask.intent("StartExerciseIntent")

def start_exercise():
    clear_session_attributes()

    if 'user' not in session.attributes:
        return question("Who is exercising?")
    if connected:
        alexa_neuron.update([('state', 'idle'),
            ('name', None),
            ('direction', None)])
        time.sleep(2)
        alexa_neuron.update([('state', 'idle'),
            ('name', session.attributes['user']),
            ('direction', None),
            ('count', 0)])

    session.attributes['exercise'] = 'STARTING'
    return question("Starting exercise session. Please step in front of and face Daisy. When you are ready say start.")

@ask.intent("ExerciseIntent")

def exercise():
    if 'exercise' not in session.attributes or session.attributes['exercise'] != 'STARTING':
        return question("Not in exercise session. Can I help you with anything else?")

    if connected:
        alexa_neuron.update([('state', 'exercise'),
            ('name', session.attributes['user']),
            ('direction', None)])
        tracked = alexa_neuron.get('tracking')
        if tracked is not None and not tracked:
            return question("Please step in front of and face Daisy. Say start when you are ready.")


    session.attributes['exercise'] = 'IN_PROCESS'
    return question("Start Exercising now.")

@ask.intent("StopExerciseIntent")

def stop_exercise():
    if 'exercise' not in session.attributes or session.attributes['exercise'] != 'IN_PROCESS':
        return question("Not in exercise session. Can I help you with anything else?")
    squat_count = 0
    if connected:
        squat_count = alexa_neuron.get('count') / 2
        alexa_neuron.pop('count', None)
        alexa_neuron.update([('state', 'idle'),
            ('name', None),
            ('direction', None)])
        record = get_EXERCISE_RECORD(session.attributes['user'])
        newRecord = False
        if record is None:
            newRecord = True
            record = {
                "user": session.attributes['user'],
                "id_num": Team5.index(session.attributes['user']),
                "count": 0,
                "overall_count": 0,
                "overall_performance": 0,
                "data": []
            }

        count = record['count'] + 1
        record.setdefault("data",[]).append(squat_count)
        overall_score = sum(record["data"])

        updates = {
            "overall_count": overall_score,
            "overall_performance": scoreCalc(overall_score, count),
            "count": count,
            "data": record["data"]
        }

        if newRecord:
            mergedRecord = {**record, **updates}
            push_EXERCISE_RECORD(mergedRecord)
        else:
            update_EXERCISE_RECORD(record, updates)


    clear_session_attributes()
    return question("You did {} squats. Session Data has been saved. Can I help you with anything else?"
            .format('%.2f'%(squat_count)))

@ask.intent("CallIntent")

def call():
    clear_session_attributes()

    call = twilioclient.calls.create(
            to="+12404785891",
            from_="+12028043762",
            url="http://demo.twilio.com/docs/voice.xml")
    print(call.sid)
    return question("Making call, Can I help you with anything else?").reprompt("May I please have a command?")

@ask.intent("TextIntent")

def text():
    clear_session_attributes()

    message = twilioclient.messages.create(
            to="+12404785891",
            from_="+12028043762",
            body="Hello from Daisy")
    print(message.sid)
    return question("Sending text, Can I help you with anything else?").reprompt("May I please have a command?")


@ask.intent("YesIntent")

def yes():
    clear_session_attributes()

    return question("What would you like to do?").reprompt("May I please have a command?")


@ask.intent("NoIntent")

def no():
    clear_session_attributes()

    return statement("Ok. goodbye")


@ask.intent("AMAZON.StopIntent")

def stop():
    clear_session_attributes()

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
    app.run(args.ip, int(args.port), debug=True)
