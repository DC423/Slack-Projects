import os
import time
import random
import json
import sqlite3
from slackclient import SlackClient

# constants
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
BOT_NAME = 'triviabot'
BOT_ID = '#########'

# instantiate Slack client
slack_client = SlackClient(SLACK_BOT_TOKEN)

# instantiate SQLITE connector
conn = sqlite3.connect('triviabot.db')



# handle_command FUNCTION
def handle_command(command, chan):
    """
    Receives commands directed at the bot and determines if they are valid.
    If so, act. If not, tell the user what it needs.
    """
    global GLOB_BOT_CHANNEL
    global GLOB_TRIVIA_QUESTION
    global GLOB_TRIVIA_ANSWER
    global GLOB_GAME_STARTED
    if command.startswith('!help'):
        response = "Info:\n\n" + \
                    "   - There are almost 300,000 questions in here...\n" + \
                    "   - Some are bound to be wrong\n\n" + \
                    "Commands:\n\n" + \
                    "   - *!repeat* - repeats the last question\n" + \
                    "   - *!scoreboard* - shows the current high scoreboard" + \
        slack_client.api_call("chat.postMessage", channel=chan,
                              text=response, as_user=True)
    if GLOB_GAME_STARTED is True:
        if command.startswith('!repeat'):
            send_message("QUESTION: " + GLOB_TRIVIA_QUESTION, GLOB_BOT_CHANNEL)
        if command.startswith('!scoreboard'):
            send_message(generate_scoreboard(), GLOB_BOT_CHANNEL)
    else:
        if command.startswith('!start'):
            GLOB_GAME_STARTED = True
            response = "Its go time!"
            slack_client.api_call("chat.postMessage", channel=chan,
                                  text=response, as_user=True)
            GLOB_BOT_CHANNEL = chan



# send_message FUNCTION
def send_message(message, chan):
    """
    Receives commands directed at the bot and determines if they are valid.
    If so, act. If not, tell the user what it needs.
    """
    slack_client.api_call("chat.postMessage", channel=chan,
                          text=message, as_user=True)



# parse_slack_output FUNCTION
def parse_slack_output(slack_rtm_output):
    """
    Slack RTM API is an events firehose. Function returns None unless message is
    directed at the bot (based on its ID)
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output:
                # return text after the @ mention (strip whitespace)
                loaded_output = json.dumps(output)
                return output['text'].strip().lower(), output['channel']
    return None, None



# listen_for_answer FUNCTION
def listen_for_answer(answer):
    """
    Listens to the firehose for the correct answer
    """
    global GLOB_BOT_CHANNEL
    global GLOB_CURRENT_HINT
    global GLOB_QUESTION_TIME
    hint_count = 0
    while True:
        if int(round(time.time())) >= GLOB_QUESTION_TIME + 10 and hint_count == 0:
            send_message("HINT: " + partial_answer(GLOB_TRIVIA_ANSWER.lower()), GLOB_BOT_CHANNEL)
            hint_count = hint_count + 1
        if int(round(time.time())) >= GLOB_QUESTION_TIME + 20 and hint_count == 1:
            send_message("HINT: " + partial_answer(GLOB_TRIVIA_ANSWER.lower()), GLOB_BOT_CHANNEL)
            hint_count = hint_count + 1
        if int(round(time.time())) >= GLOB_QUESTION_TIME + 30 and hint_count == 2:
            send_message("SORRY! The answer was '" + GLOB_TRIVIA_ANSWER + "'. Next question in 10 seconds!", GLOB_BOT_CHANNEL)
            GLOB_CURRENT_HINT = ""
            time.sleep(10)
            return
        content = slack_client.rtm_read()
        if content and len(content) > 0:
            for output in content:
                if output and 'text' in output:
                    # return text after the @ mention (strip whitespace)
                    loaded_output = json.dumps(output)
                    if '!repeat' in output['text'] or '!help' in output['text'] or '!scoreboard' in output['text']:
                        handle_command(output['text'], GLOB_BOT_CHANNEL)
                    if output['text'].lower() == answer:
                        score = 0
                        if hint_count == 0:
                            score = add_score_to_user(get_username(output['user']), 10)
                        if hint_count == 1:
                            score = add_score_to_user(get_username(output['user']), 5)
                        if hint_count == 2:
                            score = add_score_to_user(get_username(output['user']), 3)
                        send_message("CORRECT " + get_username(output['user']) + \
                                     "!! The answer was '" + answer + \
                                     "'. You have " + str(score) + " points!", GLOB_BOT_CHANNEL)
                        GLOB_CURRENT_HINT = ""
                        return



# partial_answer FUNCTION
def partial_answer(answer):
    """
    Generates a hint by showing some letters in the answer and replacing others
    with '-'. The more times it is called, the more it reveals
    """
    global GLOB_CURRENT_HINT
    if (GLOB_CURRENT_HINT == ""):
        i = 0
        while i < len(answer):
            if i % 2 == 0:
                GLOB_CURRENT_HINT = GLOB_CURRENT_HINT + answer[i]
            else:
                GLOB_CURRENT_HINT = GLOB_CURRENT_HINT + '-'
            i = i + 1
    else:
        rand = random.randint(0, len(answer) - 1)
        while GLOB_CURRENT_HINT[rand] != '-':
            rand = random.randint(0, len(answer) - 1)
        hint_bs = bytearray(GLOB_CURRENT_HINT, 'utf8')
        hint_bs[rand] = answer[rand]
        GLOB_CURRENT_HINT = str(hint_bs)
    return GLOB_CURRENT_HINT



# get_username FUNCTION
def get_username(uid):
    """
    Gets the username of a player based on the user id that is contained in the
    message.
    """
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('id') == uid:
                return user['name']
    return "noname"



# add_score_to_user FUNCTION
def add_score_to_user(uid, points):
    """
    Either updates a player's entry on the scoreboard or adds them to the board
    if they are a new player
    """
    score = 0
    try:
        c = conn.cursor()
        cursor = conn.execute("select count(*) from scoreboard where user=?", (uid.strip(),))
        for row in cursor:
            count = row[0]
        if count > 0:
            cursor = conn.execute("select score from scoreboard where user=?", (uid.strip(),))
            for row in cursor:
                score = row[0]
            score = score + points
            c.execute("update scoreboard set score=? where user=?", (score, uid.strip()))
            conn.commit()
        else:
            score = score + points
            c.execute("insert into scoreboard (user, score) values (?, ?)", (uid.strip(), score))
            conn.commit()
    except sqlite3.Error:
        self.output_exc()
    return score



# generate_scoreboard FUNCTION
def generate_scoreboard():
    """
    Does a poor job of creating a TOp 10 list of players based on their all-time
    scores. This should be re-visited at another time to clean up the display of
    the scores.
    """
    scoreboard = ""
    try:
        cursor = conn.execute("select user, score from scoreboard ORDER BY score LIMIT 10")
        i = 1
        for row in cursor:
            scoreboard = scoreboard + str(i) + ". Player: " + str(row[0]) + " >>>>> " + str(row[1]) + "\n"
            i = i + 1
        return scoreboard
    except sqlite3.Error as er:
        print 'er: ', er.message



# MAIN FUNCTION
if __name__ == "__main__":
    """
    Main code loop
    """
    global GLOB_TRIVIA_QUESTION
    global GLOB_TRIVIA_ANSWER
    global GLOB_BOT_CHANNEL
    global GLOB_GAME_STARTED
    global GLOB_CURRENT_HINT
    global GLOB_QUESTION_TIME
    GLOB_BOT_CHANNEL = None
    GLOB_GAME_STARTED = False
    GLOB_CURRENT_HINT = ""
    READ_WEBSOCKET_DELAY = 0 # read delay (in seconds) from web firehose

    cursor = conn.execute("select COUNT(*) from trivia")
    for row in cursor:
        count = row[0]

    if slack_client.rtm_connect():
        print("LS-TRIVIA-BOT is running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel and command.startswith('!') :
                handle_command(command, channel)

            if GLOB_BOT_CHANNEL is not None:
                rndm = random.randint(0, count)
                cursor = conn.execute("select * from trivia where _id=" + str(rndm))
                for row in cursor:
                    question = str(row[1])
                    answer = str(row[2])
                GLOB_TRIVIA_QUESTION = question
                GLOB_TRIVIA_ANSWER = answer
                send_message("QUESTION: " + question, GLOB_BOT_CHANNEL)
                GLOB_QUESTION_TIME = int(round(time.time()))
                print "ANSWER: " + answer
                listen_for_answer(answer.lower())
    else:
        print("Connection failed. Check token or id")
