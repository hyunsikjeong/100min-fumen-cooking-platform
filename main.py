from flask import Flask
from flask import render_template, request, redirect, flash, g

from datetime import datetime
import dateutil.parser
import random
from hashlib import sha256
import json
import os
import secrets
import sqlite3

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './upload'
app.secret_key = secrets.token_urlsafe(32)

css_param = format(random.getrandbits(64), '016x')
settings = json.load(open('settings.json', 'r'))
people_list = json.load(open('people.json', 'r', encoding='utf8'))

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('./database.db')
    return db

def query_db(query, args=(), one=False, commit=False):
    db = get_db()
    cur = db.execute(query, args)
    rv = cur.fetchall()
    if commit:
        db.commit()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def update_db(person, filename):
    query_db("DELETE FROM timestamps WHERE person == ?", [person], commit=True)
    query_db("INSERT INTO timestamps VALUES (?, ?, ?)", [
        person,
        filename,
        datetime.now().isoformat()
    ], commit=True)

def get_db_data():
    return query_db("SELECT * from timestamps")

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

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

def get_user_token(person, token):
    return sha256((token + person).encode('utf8')).hexdigest()[:10]

def check_user_token(people, token, user_token):
    for idx, person in enumerate(people):
        if get_user_token(person, token) == user_token:
            return (idx, person)
    return None

def check_and_get_extension(filename):
    if '.' not in filename:
        return None
    extension = filename.rsplit('.', 1)[1].lower()
    if extension in ['zip', 'rar', '7z', 'bms', 'bme', 'bml']:
        return extension
    return None

@app.route('/am', methods=['GET', 'POST'])
@app.route('/pm', methods=['GET', 'POST'])
def am_pm_list():
    # Get people list
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

    # Handle uploaded files
    if request.method == 'POST':
        uploadable = (token == settings['admin_token'] or start <= now < end)
        if not uploadable:
            flash('Time is out')
            return redirect(request.url)
        # Empty files
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if not file or file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        user_token = request.form['token'].strip()
        res = check_user_token(people, settings['admin_token'], user_token)
        if not res:
            flash('Wrong token value. Please check again.')
            return redirect(request.url)

        extension = check_and_get_extension(file.filename)
        if extension:
            idx, person = res
            filename = '{}_{}.{}'.format(idx, person, extension)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            update_db(person, filename)
            flash('Uploaded!')
        else:
            flash('Wrong extension: only zip, rar, 7z, bms, bme, bml are allowed')

        return redirect(request.url)

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

    data = get_db_data()
    time_dict = dict(map(lambda x: (x[0], x[2]), data))
    print(time_dict)
    lis = []
    for i in range(len(people)):
        person, song = people[i], songs[i]
        # NOTE: Super inefficient way
        if person in time_dict:
            last_time = dateutil.parser.isoparse(time_dict[person]).replace(tzinfo=start.tzinfo)
            last_time = str(last_time - start)
            if '.' in last_time:
                last_time = last_time.split('.')[0]
            lis.append((person, song, last_time))
        else:
            lis.append((person, song, "X"))

    return render_template('am_pm_list.html',
        css_param=css_param,
        lis = lis,
        reveal_state=reveal_state,
        deadline=deadline,
        nav_val=nav_val
    )

@app.route('/hidden')
def hidden():
    return render_template('hidden.html')

@app.route('/token')
def view_tokens():
    token = request.args.get('token', '')
    if token != settings['admin_token']:
        return None
    people = people_list["am"] + people_list["pm"]
    res = [ (person, get_user_token(person, token)) for person in people ]
    return render_template('token.html', res=res)

@app.route('/clear_db')
def clear_db():
    token = request.args.get('token', '')
    if token != settings['admin_token']:
        return None
    query_db("DELETE FROM timestamps WHERE 1 == 1", commit=True)
    return redirect('/')
