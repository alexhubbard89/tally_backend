from __future__ import division
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify, Response
import pandas as pd
import numpy as np
import requests
import os
import psycopg2
import urlparse
# import imp
# reps_query = imp.load_source('module', 'python/reps_query.py')


app = Flask(__name__)
app.config.from_object(__name__)

try:
    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(os.environ["HEROKU_POSTGRESQL_BROWN_URL"])

    conn = psycopg2.connect(
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


def hash_password(password, version=1, salt=None):
    import hashlib, uuid
    if version == 1:
        if salt == None:
            salt = uuid.uuid4().hex[:16]
        hashed = salt + hashlib.sha1( salt + password).hexdigest()
        # generated hash is 56 chars long
        return hashed
    # incorrect version ?
    return None

def test_password(password, hashed, version=1):
    import hashlib, uuid
    if version == 1:
        salt = hashed[:16]
        rehashed = hash_password(password, version, salt)
        return rehashed == hashed
    return False

"""Check if passwords match for login process"""
def search_user_name(user_name):
    sql_command = """
    select password from  user_tbl
    where user_name = '{}'""".format(user_name)

    user_results = pd.read_sql_query(sql_command, connection)
    return user_results

def search_user(user_name, password):
    try:
        password_found = search_user_name(user_name).loc[0, 'password']
        pw_match = test_password(password, password_found, version=1)
        if pw_match == True:
            return True
        elif pw_match == False:
            return False
    except KeyError:
        return "user does not exist"


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']
        matched_credentials = search_user(username, password)    
        if matched_credentials == True:
            return render_template('login_yes.html')
        else:
            error = "Wrong user name or password"
            return render_template('login.html', error=error)
    else:
        return render_template('login.html')



if __name__ == '__main__':
    app.run(debug=True)