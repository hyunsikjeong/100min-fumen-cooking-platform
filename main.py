from flask import Flask
from flask import render_template

import random

app = Flask(__name__)

css_param = format(random.getrandbits(64), '016x')

@app.route('/')
def main():
    return render_template('main.html', css_param=css_param)

@app.route('/rule')
def rule():
    return render_template('rule.html', css_param=css_param)

@app.route('/songs')
def songs():
    return render_template('songs.html', css_param=css_param)

@app.route('/am')
def am_list():
    return render_template('am_list.html', css_param=css_param)

@app.route('/pm')
def pm_list():
    return render_template('pm_list.html', css_param=css_param)