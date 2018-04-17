import logging
from flask import Flask, render_template
from flask_ask import Ask, statement, question


app = Flask(__name__)
ask = Ask(app, "/")

log = logging.getLogger()
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)
logging.getLogger("flask_ask").setLevel(logging.DEBUG)


@ask.launch
def welcomemsg():
    welcome_msg = render_template('welcome')
    return question(welcome_msg)

Team5 = ['teddy', 'Vladimir', 'Jessie']

@ask.intent("FollowIntent")
def follow(firstname):
    if firstname in Team5:
        msg = "Tracking for {}. do you need anymore help".format(firstname)
    elif firstname == 'follow':
    	return question("Who should I follow?").reprompt("May I please have a name?")
    elif firstname not in Team5:
        msg = "I Can't follow {} he is not a member of Team 5".format(firstname)
        return question(msg).reprompt("May I please have another name?")
    return question(msg).reprompt("Can I please have a response?")

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
    return statement(msg)

@ask.intent("YesIntent")
def yes():
    return question("How can I help you?").reprompt("Can I please have a response?")

@ask.intent("NoIntent")
def no():
    return statement("Ok. Goodbye")

@ask.intent("AMAZON.StopIntent")
def stop():
    return statement("Stopping")

if __name__ == '__main__':
    app.run(debug=True)