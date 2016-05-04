#!/usr/bin/python
import os
import json
from slacker import Slacker
from random import randint
# setup slacker
API = 'API_GOES_HERE'
slack = Slacker(API)
# list of commands that support from and to
commands = ["off","you","donut","shakespeare","linus","king","chainsaw","outside","madison","nugget","yoda","caniuse","bus","xmas","bday","shutup"]
# select the command to use
command = commands[randint(0, len(commands)-1)]
# get the list of slack users and select members 
response = slack.users.list()
users = response.body['members']
# get the number of members
numUsers = len(users)
# select the user you want to randomly tell to FO
while True:
        fouser = randint(0, numUsers -1)
        url = "https://slack.com/api/users.getPresence?token={}&user={}&pretty=1".format(API, users[fouser]['id'])
        response = os.popen('curl -s {}'.format(url)).read()
        lastOnline = json.loads(response)
        epoch = int(time.time())
        # this should limit it to users online, or have been online in the last 5 min
        if epoch > lastOnline['last_activity'] - 300:
                break
# select the other use that the message will come from
otheruser = randint(0, numUsers -1)
# set up the url request and send it into curl
url = "\'http://foaas.com/{}/@{}/{}\' -H \'Accept: application/json\'".format(command, users[fouser]['name'], users[otheruser]['name'])
response = os.popen('curl -s {}'.format(url)).read()
# pares the json response
data = json.loads(response)
# select two random numbers
num1 = randint(1,10)
num2 = randint(1,10)
# if those numbers equal each other then post FO mesage
if num1 == num2:
        # post the message to slack :)
        slack.chat.post_message('#general', "*_" + data['message'] + "_* " + data['subtitle'], username="FOAASbot", icon_emoji=":rage1:")
# if not spread the love
else:
        slack.chat.post_message('#general', ":heart_eyes_cat:", username="FOAASbot", icon_emoji=":rage1:")