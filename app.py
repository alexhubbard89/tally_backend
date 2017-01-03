from __future__ import division
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify, Response
import pandas as pd
import numpy as np
import requests
import os
import sys
import json
import logging
import imp
reps_query = imp.load_source('module', 'python/reps_query.py')


app = Flask(__name__)
app.config.from_object(__name__)

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)


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


## Login testing
@app.route("/login", methods=["POST"])
def login():
    try:
        data = json.loads(request.data.decode())
        try:
            username = data['username']
        except:
            username = data['email']
        password = data['password']
    except:
        try:
            username = request.form['username']
        except:
            username = request.form['email']
        password = request.form['password']
    matched_credentials = reps_query.search_user(username, password)    
    if matched_credentials == True:
        user_data = reps_query.get_user_data(username)
        print user_data
        return jsonify(reselts=user_data.to_dict(orient='records'))
    else:
        error = "Wrong user name or password"
        print error
        return jsonify(reselts=None)

## Create New User
@app.route("/new_user", methods=["POST"])
def create_user():
    try:
        print 'trying first way'
        data = json.loads(request.data.decode())
        try:
            username = data['username']
        except:
            username = data['email']
        username = data['username']
        password = data['password']
        address = data['street']
        zip_code = data['zip_code']
    except:
        print 'trying second way'
        try:
            username = request.form['username']
        except:
            username = request.form['email']
        password = request.form['password']
        address = request.form['street']
        zip_code = request.form['zip_code']
    print zip_code
    df = reps_query.create_user_params(username, password, address, zip_code)
    user_made = reps_query.user_info_to_sql(df)

    if user_made == True:
        return jsonify(result=True)
    elif user_made == False:
        error = "oops! That user name already exists."
        return jsonify(result=False)
