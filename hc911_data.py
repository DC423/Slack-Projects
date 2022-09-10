#!/usr/bin/python
from pprint import pprint
from time import strftime
import requests
import datetime
import time
import sys
import os
import re
import sqlite3

# also post to sqllite.db 
def post_sqlite(time, type, event, responder, area, address):
    conn = sqlite3.connect('LOCATION TO DB')
    c = conn.cursor()
    c.execute('INSERT INTO events (time, type, event, responder, area, address) VALUES (?,?,?,?,?,?)', (time, type, event, responder, area, address))
    conn.commit()
    conn.close()
    
#Used to post to slack
def post_slack(API,chid,message,username,icon):
    url = "https://slack.com/api/chat.postMessage?token={}&channel={}&text={}&username={}&icon_emoji={}&pretty=1".format(API,chid,message,username,icon)
    u = urllib.urlopen(url)
    response = u.read()
    return response
  
#Change a list to a string, might need to do this a few times 
def listToString(s):
    # initialize an empty string
    str1 = " "
    # return string 
    return (str1.join(s))



#URL AND API SETUP
#New Website as of 2022-09-06
url = "https://hc911server.com/api/calls"
#use your slack token here
API  = 'TOKEN_GOES_HERE'

#GET the website from requests
response = requests.get(url)

#Get 24 hour time for Hour of the current time
hour = strftime("%H")
# minute minus 5, the time between 'created_str' and current time is around a 5min delta
min = int(strftime("%M")) -5
# if after the -5 we have a negative number then we need to make this the previous hour
if min < 0:
        min = 60 - abs(min)
        hour = str(int(hour) - 1)
min = "{0:0=2d}".format(min)
# Look at the response from the GET requests
for dic in response.json():
        # pull the creation time and save it as time 
        time = dic['creation']
        # new time is the changing the date, and time (T) is the seperator 
        newtime = time.split("T")[1]
        # year will be saved as n_year 
        n_year = time.split("T")[0]
        # hour will be saved as n_hour 
        n_hour = newtime.split(":")[0]
        # minutes will be saved as n_min
        n_min = newtime.split(":")[1]
        # seconds will be saved as n_seconds 
        n_seconds = newtime.split(":")[2].split(".")[0]
        # create a time variable to use for the messages 
        time = n_year + " " + n_hour + ":" + n_min + ":" + n_seconds
        # save type_description as type 
        type = dic['type_description']
        # save the status as event
        event = dic['status']
        # save the jurisdiction as responder 
        responder = dic['jurisdiction']
        # save the cross streets as area 
        area = dic['crossstreets']
        # save location as address 
        address = dic['location'] 
 
        # IF the time in hours and minuts match the 5 mins ago hour and min then
        if(n_hour == str(hour)and n_min == str(min)): 
            # set the message to send to slack
            message = (time  + " - _*" + type + "*_ - " + event + " - " + responder + " - _*" + area + " (" + address + ")*_")
            # Change the icon to match the responder for slack
            if "FD" in responder: 
                icon = ":fire_engine:"
                botname = "hc911_FD"
            elif "EMS" in responder:
                icon = ":ambulance:"
                botname = "hc911_EMS"
            else: 
                icon = ":police_car:"
                botname = "hc911_PD"
            # send message to slack, change the channel name to where you want to send it 
            post_slack(API,'CHANNEL NAME OR ID', message, responder, icon)
            # insert the event into the SQLite3 database 
            post_sqlite(time, type, event, responder, area, address)
            # print message to go for the logs
            print "HC911 MESSAGE -- {}".format(address)
