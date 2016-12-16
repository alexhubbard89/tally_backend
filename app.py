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
    ## app.run is to run with flask
    #app.run(debug=True)

    """I should learn why to use tornado and 
    if it's worth it for us to switch. The
    code below is to connect to tornado."""
    from tornado.wsgi import WSGIContainer
    from tornado.httpserver import HTTPServer
    from tornado.ioloop import IOLoop
    import tornado.options

    tornado.options.parse_command_line()
    http_server = HTTPServer(WSGIContainer(app))
    port = int(os.environ.get("PORT", 5000))
    http_server.listen(port=port, address='127.0.0.1')
    tornado.web.Application(debug=True)
    IOLoop.instance().start()