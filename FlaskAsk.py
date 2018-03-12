import logging
import time
import serial
from flask import Flask, render_template
from flask_ask import Ask, statement, question


app = Flask(__name__)
ask = Ask(app, "/")

log = logging.getLogger()
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)
logging.getLogger("flask_ask").setLevel(logging.DEBUG)

ser = serial.Serial('/dev/cu.usbmodem1411', 115200)

def passByte(b):
    print("Passing byte " + str(b))
    ser.write(bytes([int(b)]))

def halt():
    passByte(0)

def moveForward():
    passByte(1)

def turnRight():
    passByte(2)

def turnLeft():
    passByte(3)

def moveBackward():
    passByte(4)

@ask.launch
def welcomemsg():
    welcome_msg = render_template('welcome')
    return question(welcome_msg)

team5 = ['teddy', 'vlad', 'Jessie']

@ask.intent("FollowIntent")
def follow(firstname):
    if firstname in team5:
        msg = "Tracking for {}".format(firstname)
    elif firstname not in team5:
        msg = "I Can't follow {} he is not a member of Team 5".format(firstname)
        return question(msg).reprompt("May I please have another name?")
    return statement(msg)

@ask.intent("WhoToFollowIntent")
def what_is_my_name():
    return question("Who should I follow?").reprompt("May I please have a name?")

@ask.intent("MoveIntent")
def move(direction):
    if direction == 'left':
        turnLeft()
        msg = "moving left"
    elif direction == 'right':
        turnRight()
        msg = "moving right"
    elif direction == 'forward':
        moveForward()
        msg = "moving forward"
    elif direction == 'backward':
        moveBackward()
        msg = "moving backward"
    elif direction == 'move':
        return question("In what direction?").reprompt("Can you please give a direction?")
    return statement(msg)

@ask.intent("AMAZON.StopIntent")
def stop():
    halt()
    return statement("Stopping")


if __name__ == '__main__':
    app.run(debug=True)