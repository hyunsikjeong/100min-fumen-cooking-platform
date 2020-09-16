from flask import Flask
from flask import render_template, request

from datetime import datetime
import dateutil.parser
import random
from hashlib import sha256
import json

app = Flask(__name__)

css_param = format(random.getrandbits(64), '016x')
settings = json.load(open('settings.json', 'r'))
people_list = json.load(open('people.json', 'r', encoding='utf8'))

EMPTY_SONG_INFO = {
    "name": "???",
    "genre": "???",
    "artist": "???",
    "image": "/static/song_not_released.png",
    "recommender": "???",
    "dl": "/hidden"
}

@app.route('/')
def main():
    deadline_str = settings["application_deadline"]
    deadline = dateutil.parser.isoparse(deadline_str)
    now = datetime.now(deadline.tzinfo)

    if now >= deadline:
        deadline_str = None

    return render_template('main.html', css_param=css_param, deadline=deadline_str)

@app.route('/rule')
def rule():
    return render_template('rule.html', css_param=css_param)

@app.route('/songs', methods=['GET'])
def songs():
    song_reveal_str = settings["song_reveal"]
    song_reveal = dateutil.parser.isoparse(song_reveal_str)
    now = datetime.now(song_reveal.tzinfo)

    token = request.args.get('token', '')
    if token == settings['admin_token'] or now >= song_reveal:
        songs = json.load(open('songs.json', 'r'))
        if len(songs) < 100:
            songs += [EMPTY_SONG_INFO] * (100 - len(songs))
        song_reveal_str = None
    else:
        songs = [ EMPTY_SONG_INFO for _ in range(100) ]

    return render_template('songs.html',
        css_param=css_param,
        songs=songs,
        song_reveal=song_reveal_str
    )

@app.route('/am')
@app.route('/pm')
def am_pm_list():
    rule = request.url_rule
    if 'am' in rule.rule:
        start_str = settings["am_start"]
        end_str = settings["am_end"]
        people = people_list["am"]
        nav_val = 4
    elif 'pm' in rule.rule:
        start_str = settings["pm_start"]
        end_str = settings["pm_end"]
        people = people_list["pm"]
        nav_val = 5
    else:
        return None

    start = dateutil.parser.isoparse(start_str)
    end = dateutil.parser.isoparse(end_str)
    now = datetime.now(start.tzinfo)

    token = request.args.get('token', '')
    if token == settings['admin_token']:
        reveal_state = 3
        deadline = None
        songs = json.load(open('songs.json', 'r'))
    elif start <= now < end:
        reveal_state = 1
        deadline = end
        songs = json.load(open('songs.json', 'r'))
    elif now < start:
        reveal_state = 0
        deadline = start
        songs = [ EMPTY_SONG_INFO for _ in range(len(people)) ]
    else:
        reveal_state = 2
        deadline = None
        songs = json.load(open('songs.json', 'r'))

    # This loop is just for debugging in local
    if len(songs) < len(people):
        songs += songs * ((len(people) - 1) // len(songs))

    random.seed(int(sha256(token.encode()).hexdigest(), 16))
    random.shuffle(songs)
    lis = list(zip(people, songs[:len(people)]))

    return render_template('am_pm_list.html',
        css_param=css_param,
        lis = lis,
        reveal_state=reveal_state,
        deadline=deadline,
        nav_val=nav_val
    )
