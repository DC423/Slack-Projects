#!/usr/bin/python
# Author: Stephen Hilt
# Purpose: Run shodan host commands
#   within slack. this will look up
#   details of one host at a time. 
#######################################
import time
import json
import os
import urllib
import sys
import re
import shodan
from datetime import datetime
from websocket import create_connection

def post_slack(API,chid,message):
	url = "https://slack.com/api/chat.postMessage?token={}&channel={}&text={}&as_user=True&pretty=1".format(API,chid,message)
	u = urllib.urlopen(url)
	response = u.read()
	return response

def get_api_key():
	SHODAN_CONFIG_DIR = '~/.shodan/'
	shodan_dir = os.path.expanduser(SHODAN_CONFIG_DIR)
	keyfile = shodan_dir + '/api_key'
	# If the file doesn't yet exist let the user know that they need to
	# initialize the shodan cli
	# Make sure it is a read-only file
	os.chmod(keyfile, 0o600)
	with open(keyfile, 'r') as fin:
		return fin.read().strip()

def shodan_host(ip):
	# Make this your API Key from accounts.shodan.io
	API_KEY = get_api_key()
	#API_KEY = "YOUR KEY HERE"

	# Input validation for one argument (IP address)
  	# Pull the first argument for the IP address 
	# to look up the history of
	# Setup the API to communicate to
	api = shodan.Shodan(API_KEY)
	# pull the information about the host, and the history 
	# this is done by setting the history to True
	host = api.host(str(ip))
	# Display raw results, this is where more parsing 
	# could be done depending on your output needs
	# General info
        forreturn = ""
	if len(host['hostnames']) > 0:
		forreturn = forreturn + '{:25s}{}\n'.format('Hostnames:', ';'.join(host['hostnames']))
        if 'city' in host and host['city']:
		forreturn = forreturn + '{:25s}{}\n'.format('City:', host['city'])
	if 'country_name' in host and host['country_name']:
		forreturn = forreturn + '{:25s}{}\n'.format('Country:', host['country_name'])
        if 'os' in host and host['os']:
       		forreturn = forreturn + '{:25s}{}\n'.format('Operating System:', host['os'])
	if 'org' in host and host['org']:
		forreturn = forreturn + '{:25s}{}\n'.format('Organization:', host['org'])
       		forreturn = forreturn + '{:25s}{}\n'.format('Number of open ports:', len(host['ports']))

       	# Output the vulnerabilities the host has
        if 'vulns' in host and len(host['vulns']) > 0:
		vulns = []
		for vuln in host['vulns']:
			if vuln.startswith('!'):
				continue
               		if vuln.upper() == 'CVE-2014-0160':
               			vulns.append('Heartbleed')
               		else:
               			vulns.append(vuln)

		if len(vulns) > 0:
               		forreturn = forreturn + '{:25s}\n'.format('Vulnerabilities:')

               		for vuln in vulns:
               			forreturn = forreturn + (vuln + '\t')
                		forreturn = forreturn + '\n'
       	forreturn = forreturn + '\n'

       	forreturn = forreturn + 'Ports:\n'
       	for banner in sorted(host['data'], key=lambda k: k['port']):
		product = ''
		version = ''
		if 'product' in banner:
			product = banner['product']
		if 'version' in banner:
			version = '({})'.format(banner['version'])
		
		forreturn = forreturn + '{:>7d} '.format(banner['port'])
           	forreturn = forreturn + "{} {}\n".format(banner.get('product', ''), version)

            	if 'ssl' in banner:
                	if 'versions' in banner['ssl']:
               			forreturn = forreturn + '\t\t|-- SSL Versions: {}\n'.format(', '.join([version for version in sorted(banner['ssl']['versions']) if not version.startswith('-')]))
                	if 'dhparams' in banner['ssl']:
                		forreturn = forreturn + '\t\t|-- Diffie-Hellman Parameters:'
                		forreturn = forreturn + '\t{:15s}{}\n\t\t\t{:15s}{}'.format('Bits:', banner['ssl']['dhparams']['bits'], 'Generator:', banner['ssl']['dhparams']['generator'])
                	if 'fingerprint' in banner['ssl']['dhparams']:
                       		forreturn = forreturn + '\n\t\t\t{:15s}{}\n'.format('Fingerprint:', banner['ssl']['dhparams']['fingerprint'])
                	if 'cert' in banner['ssl']:
                		if 'issued' in banner['ssl']['cert']:
                      			forreturn = forreturn + '\t\t|-- Cert Issued: {}\n'.format(banner['ssl']['cert']['issued'])
                		if 'expires' in banner['ssl']['cert']:
					forreturn = forreturn + '\t\t|-- Cert Expires: {}\n'.format(banner['ssl']['cert']['expires'])
                   		if 'subject' in banner['ssl']['cert']:
					if 'CN' in banner['ssl']['cert']['subject']:
						forreturn = forreturn + '\t\t|-- Cert Commmon Name: {}\n'.format(banner['ssl']['cert']['subject']['CN'])
					if 'emailAddress' in banner['ssl']['cert']['subject']:
	         	       			forreturn = forreturn + '\t\t|-- Cert Email Address: {}\n'.format(banner['ssl']['cert']['subject']['emailAddress'])

            	start = banner['data'].find('Fingerprint: ')
        	if start > 0:
				start += len('Fingerprint: ')
	               		fingerprint = banner['data'][start:start+47]
        	       		forreturn = forreturn + '\t\t|--\n\t\t|-- SSH Fingerprint: {}\n'.format(fingerprint)
	
	
	return forreturn




# Var for the slack API
API = 'YOUR_SLACK_API_HERE'

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
			
			if "run shodan" in j_result['text'] and "USAGE" not in j_result['text']:
			  # lookup the user who issued the command
				url = "https://slack.com/api/users.info?token={}&user={}&pretty=1".format(API,j_result['user'])
        			u = urllib.urlopen(url)
        			response = u.read()
        			response = json.loads(response)
        			user = response['user']
        			username = user['name']
				 # set nogo to 0
				nogo = 0
				# get the IP address from the string
				cmd = j_result['text'].split(" ")[2]	
				# test to see if there are more than 3 strings passed in
				if len(j_result['text'].split()) > 3:
					nogo = 1
				# if http is in the text, then a domain name was entered
        			elif "http" in j_result['text']:
					nogo = 1
				# if there is a / in the command CIDR was passed in
				elif "/" in j_result['text']:
					nogo = 1
				# if there are less than 4 octets then not a valid IP was entered
				elif len(cmd.split(".")) < 4:
					nogo = 1
				# if any of the octest are > 255 then not a valid IP was entered
				elif any(int(octet) > 255 for octet in cmd.split(".")):
					nogo = 1
				# if anything above was met, then print usage statement
				if nogo == 1:
					resposne = post_slack(API,chid,"USAGE:run shodan <ip>")
					response = post_slack(API,chid,"Try Again!!")
				# if there only two vars then "run shodan" was entered so print usage
				elif len(j_result['text'].split()) == 2:
					resposne = post_slack(API,chid,"USAGE:run shodan <ip>")
				# else all is good and move forward with looking up the IP passed
				else:
					print str(datetime.now()) + " -- " + cmd + " ran by " + username
					response = post_slack(API,chid, "Looking up Host in Shodan *`" + cmd + "`* ... This could take a while")
        				try:
						result = shodan_host(cmd)
						response = post_slack(API,chid, "Result:\n```" + result + "\n https://www.shodan.io/host/{}```".format(cmd))
					except:
						respones = post_slack(API,chid, "Shodan Error: Please verify valid IP address or no data exists for host") 
			elif "shodan" in j_result['text'] and "Running" not in j_result['text'] and "shodan.io" not in j_result['text'] and "USAGE" not in j_result['text']:
				time.sleep(1)
		else: 
			time.sleep(1)

