!/usr/bin/python
import sys
import os
from random import randint
import urllib
import json


def post_slack(API,chid,message,username,icon):
    url = "https://slack.com/api/chat.postMessage?token={}&channel={}&text={}&username={}&icon_emoji={}&pretty=1".format(API,chid,message,username,icon)
    u = urllib.urlopen(url)
    response = u.read()
    return response



#Configuration
API = "TOKEN_HERE"
#This is for Hamilton County TN, change based off your zone
url = "https://api.weather.gov/zones/forecast/TNZ099/forecast"
# this is set to general, change to what ever channel you want it to go to. 
chid = '#general'

# read the weather forcast from NWS
u = urllib.urlopen(url)
response = u.read()
data = json.loads(response)

#initilize counter
count = 0
# while the counter is less than the number of recors for weather
while count < len(data['periods']):
    # use the name field for the message to send as the 'user'
    name = data['periods'][count]['name']
    # content of the actual message 
    message = data['periods'][count]['detailedForecast']
    # set icons for full effects 
    if "Partly sunny" in message:
         icon = ":partly_sunny:"
    elif "Mostly cloudy" in message:
         icon = ":barely_sunny:"
    elif "Mostly clear" in message:
         icon = ":mostly_sunny:"
    elif "thunderstorms" in message:
         icon = ":thunder_cloud_and_rain:"
    elif "showers" in message:
         icon = ":rain_cloud:"
    else:
         icon = ":sunny:"
    # post message to slack
    post_slack(API, chid, message, name, icon)
    # increment the counter!
    count = count + 1
