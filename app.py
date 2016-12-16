from __future__ import division
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify, Response
import pandas as pd
import numpy as np
import requests
import os


app = Flask(__name__)
app.config.from_object(__name__)




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