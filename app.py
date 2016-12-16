from __future__ import division
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify, Response
import pandas as pd
import numpy as np
import requests
import os
import psycopg2
import urlparse


app = Flask(__name__)
app.config.from_object(__name__)

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
        return render_template('login.html')
    else:
        return render_template('login.html')



if __name__ == '__main__':
    app.run(debug=True)