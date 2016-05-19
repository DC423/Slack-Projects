#!/usr/bin/python
# Author: Stephen Hilt
# version: 0.0.0.0.0.0.0.1
import time
import json
import os
import urllib
import sys
import re
from datetime import datetime
from websocket import create_connection
from libnmap.process import NmapProcess
from libnmap.parser import NmapParser, NmapParserException

# Def to post messages to a slack channel
def post_slack(API,chid,message):
	url = "https://slack.com/api/chat.postMessage?token={}&channel={}&text={}&as_user=True&pretty=1".format(API,chid,message)
	u = urllib.urlopen(url)
	response = u.read()
	return response

# performs the Nmap scan this was taken from libnmap's examples
def do_scan(targets, options):
    parsed = None
    nmproc = NmapProcess(targets, options)
    rc = nmproc.run()
    if rc != 0:
        print("nmap scan failed: {0}".format(nmproc.stderr))
    print(type(nmproc.stdout))

    try:
        parsed = NmapParser.parse(nmproc.stdout)
    except NmapParserException as e:
        print("Exception raised while parsing scan: {0}".format(e.msg))

    return parsed


# print scan results from a nmap report, this was altered to not print to stdout from 
# libnmap's exampes
def print_scan(nmap_report):
    forreturn = ""
    forreturn = "Starting Nmap DC423 ( http://nmap.org ) at {}".format(nmap_report.started)

    for host in nmap_report.hosts:
        if len(host.hostnames):
            tmp_host = host.hostnames.pop()
        else:
            tmp_host = host.address

        forreturn = forreturn + "\n" + "Nmap scan report for {0} ({1})".format(
            tmp_host,
            host.address)
        forreturn = forreturn + "\n" + "Host is {0}.".format(host.status)
        forreturn = forreturn + "\n" + "  PORT     STATE         SERVICE"

        for serv in host.services:
            pserv = "{0:>5s}/{1:3s}  {2:12s}  {3}".format(
                    str(serv.port),
                    serv.protocol,
                    serv.state,
                    serv.service)
            if len(serv.banner):
                pserv += " ({0})".format(serv.banner)
            forreturn = forreturn + "\n" + pserv
    forreturn = forreturn + "\n" + nmap_report.summary
    return forreturn




# Var for the slack API
API = 'API_KEY_HERE'
# things you don't want to allow at all
notallowed = [";","&","localhost","script","ls","127.0.0.1","iflist","data-string","$","`"]
# list the channles, this will be used to find general
url = "https://slack.com/api/channels.list?token={}&pretty=1".format(API)
u = urllib.urlopen(url)
response = u.read()
response = json.loads(response)
channels = response['channels']
# in the list of channles, find the channel id of general
count = 0
while count < len(channels) - 1:
	if channels[count]['name'] == "general":
		chid = channels[count]['id']
		break
	count += 1

# start the RTM 
url = "https://slack.com/api/rtm.start?token={}&pretty=1".format(API)
u = urllib.urlopen(url)
response = u.read()
# parse results to determine the WebSocket url
rtm_result = json.loads(response)
#create the websocket connection
ws = create_connection(rtm_result['url'])	

# WHILE TRUE!!!

while True:
	# recieve from the websocket 
	result = ws.recv()
	# parse result from the websocket
	j_result = json.loads(result)
	# if its a hello message then sleep for a second
	if j_result['type'] == "hello":
		time.sleep(1)
	# if the type is a message, and its not a hidden message
	elif j_result['type'] == "message" and not j_result.has_key('hidden'):
		if chid == j_result['channel']: 
			# if 'run nmap' and not the USAGE statement is the message sent by websocket
			if "run nmap" in j_result['text'] and "USAGE" not in j_result['text']:
				# find the user nme based off the user id of who submitted the scan
				url = "https://slack.com/api/users.info?token={}&user={}&pretty=1".format(API,j_result['user'])
				u = urllib.urlopen(url)
				response = u.read()
				response = json.loads(response)
				user = response['user']
				username = user['name']
				# initilize count and nogo to 0
				count = 0
				nogo = 0
				# see if any not allowed strings are in the submitted command
				while count < len(notallowed):
					if notallowed[count] in j_result['text']:
						response = post_slack(API,chid, "Nice try... unsupported command")
						nogo = 1
					count += 1
				# if the command is over 3 words including "run nmap" then set nogo to 1
				if len(j_result['text'].split()) > 3:
					nogo = 1
				# if no go was set to 1 above then print "try again"
				if nogo == 1:
					response = post_slack(API,chid,"Try Again!!")
				# if only "run nmap" was entered then print usage statement
				elif len(j_result['text'].split()) == 2:
					resposne = post_slack(API,chid,"USAGE:run nmap <ip || domain>")
					response = post_slack(API,chid,"Try Again!!")
				# if non of the above are met then parse and perform scan
				else:
					# store the entered command into cmd
					cmd = j_result['text']
					# if http is in the result, its likely a domain name
					# slack adds <http://<domain>|domain>
					if "http" in cmd:
						# split on the | and strip the > 
						cmd = cmd.split("|")[1].replace(">","")
					else:
						# pattern to extract IP addresses
						pattern = r"((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)([ (\[]?(\.|dot)[ )\]]?(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3})"
						# extract IPs from the string, this puts them into a list
						ips = [each[0] for each in re.findall(pattern, cmd)]
						# we are only allowing a single IP, so reset cmd to just the IP
						cmd = ips[0]
					# print message of date timestamp, the domain/ip and the username who entered it
					# this can be redirected to a log 
					print str(datetime.now()) + " -- " + cmd + " ran by " + username
					# print message to slack channel that the nmap is starting 
					# this could be changed to respond to DM if you don't want to clutter up #general
					# by changing chid to j_result['user']
					response = post_slack(API,chid, "Running: nmap on target *`" + cmd + "`* ... This could take a while")
					# perform the scan via libnmap
					report = do_scan(str(cmd), "-sV -sT --open")
					# if the scan was a success print the results to slack channel
					# as above this can be changed to a dm by changing chid to j_result['user']
					if report:
          					response = post_slack(API,chid, "Result:\n```" + print_scan(report) + "```")
        				# else the scan produced no results (likely there was an error)
        				# change to DM by changing chid to j_result['user']
    					else:
        	  				response = post_slack(API,chid, "Result:\n`No Results Returned`")
          		# to remind everyon who just types nmap that Trinity uses Nmap
			elif "nmap" in j_result['text'] and "Running" not in j_result['text'] and "nmap.org" not in j_result['text'] and "USAGE" not in j_result['text']:
				      resposne = post_slack(API,chid,"Trinity uses Nmap")

		else: 
			time.sleep(1)


	
