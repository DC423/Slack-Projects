#!/usr/bin/python
import os
import json
import urllib
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
	u = urllib.urlopen(url)
	response = u.read()
	presence = json.loads(response)
	# if presense is active, and its not a bot we have our victim
	if "active" in  presence['presence'] and "bot" not in users[fouser]['name']:
		break	
# use the slack API to query open an IM to the user to send them the message later
url = "https://slack.com/api/im.open?token={}&user={}&pretty=1".format(API, users[fouser]['id'])
u = urllib.urlopen(url)
response = u.read()
user_im = json.loads(response)
im_id = user_im['channel']['id']

# select the other use that the message will come from
otheruser = randint(0, numUsers -1)
# set up the url request and send it into curl
url = "\'http://foaas.com/{}/@{}/{}\' -H \'Accept: application/json\'".format(command, users[fouser]['name'], users[otheruser]['name'])
response = os.popen('curl -s {}'.format(url)).read()
# pares the json response
data = json.loads(response)
# Roulette style 
num1 = randint(1,6)
num2 = randint(1,6)
# If numbers are equal do something offinsive 
if num1 == num2:
	print "test"
	# post the message to slack :)
	slack.chat.post_message('#general', "*_" + data['message'] + "_* " + data['subtitle'], username="FOAASbot", icon_emoji=":rage1:")
	slack.chat.post_message(im_id, "*_" + data['message'] + "_* " + data['subtitle'], username="FOAASbot", icon_emoji=":rage1:")
else:
	# User the username in a positive Chuck Norris esq joke
	url = "http://api.icndb.com/jokes/random?firstName={}&lastName= ".format(users[fouser]['name'])
	u = urllib.urlopen(url)
	response = u.read()
	# pares the json response
	data = json.loads(response)
	slack.chat.post_message(im_id, data['value']['joke'].replace(" Norris",""), username="ChuckNorrisbot", icon_emoji=":chuck:")
	slack.chat.post_message('#general', data['value']['joke'].replace(" Norris",""), username="ChuckNorrisbot", icon_emoji=":chuck:")
# close the IM message
url = "https://slack.com/api/im.close?token={}&user={}&pretty=1".format(API, users[fouser]['id'])
u = urllib.urlopen(url)
response = u.read()
