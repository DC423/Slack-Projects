# Slack Trivia Bot

This is my take on an IRC trivia bot but for Slack. Built in Python (this is my
first Python program). It has roughly 255,000 questions and answers as well as
a scoreboard system, all of which is stored in a sqlite database.

## Installation
- Install Python2.7
- Install pip
- Install slackclient (pip install slackclient)
- Create API token for new Slack BOT_ID
- Export API token as environment variable (export SLACK_BOT_TOKEN='your slack token pasted here')
- Edit print_bot_id.py: (Set BOT_NAME on line 4 to whatever you named your bot in Slack)
- Copy the ID for the bot to triviabot.py (Set BOT_ID on line 11)
- Initialize triviabot (python triviabot.py)
- Start triviabot (in the Slack channel, type '!start')

## Contributing
1. Fork it, please.
2. Create your branch: 'git checkout -b new-feature-name'
3. Commit your changes: 'git commit -am 'add some new feature''
4. Push to the branch: 'git push origin new-feature-name'
5. Submit a pull request

## Features
- Basic command structure
  - !start : starts the triviabot with the game.
  - !help : shows some basic information and the commands that can be used
  - !repeat : repeats the last question
  - !scoreboard : shows the top 10 entries of all time for the trivia game

## History
2016/12/27 >> v1.0 >> Initial build of the triviabot

## License
CC BY-NC-SA
https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode
