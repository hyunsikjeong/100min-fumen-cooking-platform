from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route('/')
def main():
    return render_template('main.html')

@app.route('/rule')
def rule():
    return render_template('rule.html')

@app.route('/songs')
def songs():
    return render_template('songs.html')

@app.route('/am')
def am_list():
    return render_template('am_list.html')

@app.route('/pm')
def pm_list():
    return render_template('pm_list.html')