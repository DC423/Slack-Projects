# Author: Stephen Hilt
# Updates: Changed some things to fix a few errors was getting now with more requests.
#
#!/usr/bin/python
import os
import json
import urllib
import requests
from slacker import Slacker
from random import randint
# setup slacker
API = 'API_GOES_HERE'
#API = os.environ.get('SLACK_TOKEN')
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
url = "http://foaas.com/{}/@{}/{}".format(command, users[fouser]['name'], users[otheruser]['name'])
header = {'Accept': 'application/json'}
response = requests.get(url,headers=header)
print(response.json())
# pares the json response
data = response.json()
# create two random numbers
num1 = randint(1,9)
num2 = randint(1,9)

if num1 < 3:
        # post the message to slack :)
        slack.chat.post_message('#general', "*_" + data['message'] + "_* ", username="FOAASbot", icon_emoji=":rage1:")
elif num1 > 3 and num1 <= 6:
        url = "http://api.icndb.com/jokes/random?firstName={}&lastName= ".format(users[fouser]['name'])
        u = urllib.urlopen(url)
        response = os.popen('curl -s {}'.format(url)).read()
        # response = u.read()
        # pares the json response
        data = json.loads(response)
        joke = data['value']['joke'].replace(" Norris","")
        slack.chat.post_message('#general', joke.replace("&quot;","\""), username="ChuckNorrisbot", icon_emoji=":chuck:")
elif num1 > 6:
        url = "http://api.whatdoestrumpthink.com/api/v1/quotes/personalized?q={}".format(users[fouser]['name'])
        data = requests.get(url).json()
        joke = data['message']
        slack.chat.post_message('#general', joke.replace("&quot;","\""), username="DonaldTrumpbot", icon_emoji=":drumpf:")

else:
        slack.chat.post_message('#general', users[fouser]['name'] + " You missed your FREE Windows 10 upgrade you now must pay! :-(", as_user=True)
url = "https://slack.com/api/im.close?token={}&user={}&pretty=1".format(API, users[fouser]['id'])
u = urllib.urlopen(url)
response = u.read()

