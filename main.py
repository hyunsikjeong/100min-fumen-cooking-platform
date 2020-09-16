from flask import Flask
from flask import render_template, request

from datetime import datetime
import dateutil.parser
import random
import json

app = Flask(__name__)

css_param = format(random.getrandbits(64), '016x')
settings = json.load(open('settings.json', 'r'))

EMPTY_SONG_INFO = {
    "name": "???",
    "genre": "???",
    "artist": "???",
    "image": "/static/unknown_song.png",
    "recommender": "???",
    "dl": "/hidden"
}

@app.route('/')
def main():
    deadline_str = settings["application_deadline"] 
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
        return render_template('songs.html', css_param=css_param, songs=songs)
    
    else:
        return render_template('songs_empty.html', css_param=css_param, song_reveal=song_reveal_str)

@app.route('/am')
def am_list():
    token = request.args.get('token', '')
    if token == settings['admin_token']:
        return render_template('am_list.html', css_param=css_param)
    else:
        return render_template('empty.html', css_param=css_param, nav_val=4)

@app.route('/pm')
def pm_list():
    token = request.args.get('token', '')
    if token == settings['admin_token']:
        return render_template('pm_list.html', css_param=css_param)
    else:
        return render_template('empty.html', css_param=css_param, nav_val=5)