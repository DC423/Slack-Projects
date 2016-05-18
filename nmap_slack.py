#!/usr/bin/python
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


# print scan results from a nmap report
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

notallowed = [";","&","localhost","script","ls","127.0.0.1","iflist","data-string","$","`"]

url = "https://slack.com/api/channels.list?token={}&pretty=1".format(API)
u = urllib.urlopen(url)
response = u.read()
response = json.loads(response)
channels = response['channels']

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
			
			if "run nmap" in j_result['text'] and "USAGE" not in j_result['text']:
				url = "https://slack.com/api/users.info?token={}&user={}&pretty=1".format(API,j_result['user'])
                        	u = urllib.urlopen(url)
                        	response = u.read()
                        	response = json.loads(response)
                        	user = response['user']
                        	username = user['name']
				count = 0
				nogo = 0
				if username == "giminy" or username == "mtoecker" or username == "mikem2314" or username == "synackpwn":
					nogo = 1
				while count < len(notallowed):
					if notallowed[count] in j_result['text']:
						response = post_slack(API,chid, "Nice try... unsupported command")
						nogo = 1
					count += 1
				if len(j_result['text'].split()) > 3:
					nogo = 1

				if nogo == 1:
					response = post_slack(API,chid,"Try Again!!")
				elif len(j_result['text'].split()) == 2:
           	               		resposne = post_slack(API,chid,"USAGE:run nmap <ip || domain>")
        	 	       		response = post_slack(API,chid,"Try Again!!")
				else:
					cmd = j_result['text']
					if "http" in cmd:
						cmd = cmd.split("|")[1].replace(">","")
					
					else:
						pattern = r"((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)([ (\[]?(\.|dot)[ )\]]?(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3})"
						ips = [each[0] for each in re.findall(pattern, cmd)]
						cmd = ips[0]
					print str(datetime.now()) + " -- " + cmd + " ran by " + username
					response = post_slack(API,chid, "Running: nmap on target *`" + cmd + "`* ... This could take a while")
					report = do_scan(str(cmd), "-sV")
					if report:
        					response = post_slack(API,chid, "Result:\n```" + print_scan(report) + "```")
    					else:
        					response = post_slack(API,chid, "Result:\n`No Results Returned`")
			elif "nmap" in j_result['text'] and "Running" not in j_result['text'] and "nmap.org" not in j_result['text'] and "USAGE" not in j_result['text']:
				resposne = post_slack(API,chid,"Trinity uses Nmap")

		else: 
			time.sleep(1)


	
