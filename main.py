from flask import Flask
from flask import render_template, request

import random
import json

app = Flask(__name__)

css_param = format(random.getrandbits(64), '016x')
settings = json.load(open('settings.json', 'r'))

@app.route('/')
def main():
    deadline = settings["application_deadline"]
    return render_template('main.html', css_param=css_param, deadline=deadline)

@app.route('/rule')
def rule():
    return render_template('rule.html', css_param=css_param)

@app.route('/songs', methods=['GET'])
def songs():
    token = request.args.get('token', '')
    if token == settings['admin_token']:
        return render_template('songs.html', css_param=css_param)
    else:
        return render_template('empty.html', css_param=css_param, nav_val=3)

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