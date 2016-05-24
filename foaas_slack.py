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
	if "away" in  presence['presence'] and "bot" not in users[fouser]['name']:
		break	

api_im_open = "https://slack.com/api/im.open?token={}&user={}&pretty=1".format(API, users[fouser]['id'])
u = urllib.urlopen(api_im_open)
response = u.read()
user_im = json.loads(response)
im_id = user_im['channel']['id']

# select the other use that the message will come from
otheruser = randint(0, numUsers -1)
# set up the url request
url = "\'http://foaas.com/{}/@{}/{}\' -H \'Accept: application/json\'".format(command, users[fouser]['name'], users[otheruser]['name'])
response = os.popen('curl -s {}'.format(url)).read()
# pares the json response
data = json.loads(response)

num1 = randint(1,6)
# if number is less than 3 than tell the user to F&#* off
if num1 < 3:
	# post the message to slack :)
	slack.chat.post_message('#general', "*_" + data['message'] + "_* ", username="FOAASbot", icon_emoji=":rage1:")
#	slack.chat.post_message(im_id, "*_" + data['message'] + "_* " + data['subtitle'], username="FOAASbot", icon_emoji=":rage1:")
# if number is greater than 3, then chuck noris joke the user.
elif num1 > 3:
	url = "http://api.icndb.com/jokes/random?firstName={}&lastName= ".format(users[fouser]['name'])
	u = urllib.urlopen(url)
	response = os.popen('curl -s {}'.format(url)).read()
	# response = u.read()
	# pares the json response
	data = json.loads(response)
	joke = data['value']['joke'].replace(" Norris","")
	slack.chat.post_message('#general', joke.replace("&quot;","\""), username="ChuckNorrisbot", icon_emoji=":chuck:")
#	slack.chat.post_message(im_id, data['value']['joke'].replace(" Norris",""), username="ChuckNorrisbot", icon_emoji=":chuck:")
# else if the number is 3, then FREE Windows 10 Upgrade!!
else: 
	slack.chat.post_message('#general', users[fouser]['name'] + " Your FREE Windows 10 upgrade is ready!", as_user=True)
url = "https://slack.com/api/im.close?token={}&user={}&pretty=1".format(API, users[fouser]['id'])
u = urllib.urlopen(url)
response = u.read()
