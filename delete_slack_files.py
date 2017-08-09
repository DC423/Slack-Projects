# DC423 Code to Remove ALL files from a user 
# This can be altered to do it with time constraints but for now
# Nuke all files from Slack :) 
import requests
import sys

if len(sys.argv) < 2:
	print "Provide a username" 
	sys.exit()

#API KEY HERE
token = ''
#Take argument as the username 
user = sys.argv[1]
# SET Userid to NULL
userid = 'NULL'
# url to get user listing
userurl = 'https://slack.com/api/users.list?token={}&pretty=1'.format(token)
# get user listing
u = requests.get(userurl).json()
# find the username in the listing 
for usr in u['members']:
	if usr['name'] == user:
		userid = usr['id']
    
# If user was not found, Exit
if userid == 'NULL':
	sys.exit()

# Number of days
days = 30
# list all files from user (only 100 at a time) 
urllist = 'https://slack.com/api/files.list?token={}&count=100&ts_from={}&user={}&pretty=1'.format(token, userid, days)
data = requests.get(urllist).json()
# if there was files then parse the files and delete them 
while data['ok'] == True:	
  # for all the files in the list
	for file in data['files']:
	    fileid = file['id']
	    filename = file['name']
	    urldelete = 'https://slack.com/api/files.delete?token={}&file={}&pretty=1'.format(token,fileid)
	    deletefile = requests.get(urldelete).json()
	    print filename + " - Deleted: " + str(deletefile['ok'])
  # get more files
	data = requests.get(urllist).json()
	
