from __future__ import division
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify, Response
import pandas as pd
import numpy as np
import requests
import os
import psycopg2
import urlparse
import sys
import logging
import imp
reps_query = imp.load_source('module', 'python/reps_query.py')


app = Flask(__name__)
app.config.from_object(__name__)

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

try:
    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(os.environ["HEROKU_POSTGRESQL_BROWN_URL"])

    connection = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
except:
    print "back up db"
    urlparse.uses_netloc.append("postgres")
    creds = pd.read_json('db_creds.json').loc[0,'creds']

    connection = psycopg2.connect(
        database=creds['database'],
        user=creds['user'],
        password=creds['password'],
        host=creds['host'],
        port=creds['port']
    )



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']
        matched_credentials = reps_query.search_user(username, password)    
        if matched_credentials == True:
            user_data = reps_query.get_user_data(username)
            print user_data
            return render_template('login_yes.html', user_data=user_data)
        else:
            error = "Wrong user name or password"
            return render_template('login.html', error=error)
    else:
        return render_template('login.html')



if __name__ == '__main__':
    app.run(debug=True)