from flask import (Flask, render_template, Response, Blueprint, flash, g, redirect, request, url_for)
from flask_socketio import SocketIO, emit
import os
from datetime import datetime


#from flask_cors import CORS, cross_origin

#from flask import Flask, Response
#from flask_socketio import SocketIO, join_room, leave_room
#import eventlet
#from config import config
#from flask_cors import CORS, cross_origin

#from flask_session import Session
#from flask_apscheduler import APScheduler


from dotenv import load_dotenv
load_dotenv() #for local secret management with .env file

socketio = SocketIO()
clients = {}

def create_app(debug=True, main=True):
    app = Flask(__name__)

    #DEPLOYMENT CODE - GITHUB SECRETS 
    # app.config.from_mapping(
    #     DB_API_URL = os.environ["DB_API_URL"], #supabase api url gh secret
    #     DB_API_KEY = os.environ["DB_API_KEY"], #supabase api key gh secret
    #     AWS_ACCESS_KEY = os.environ["AWS_ACCESS_KEY"], #aws access key gh secret
    #     AWS_SECRET_KEY = os.environ["AWS_SECRET_KEY"] #aws secret key gh secret
    # )

    #DEVELOPMENT CODE - LOCAL SECRETS
    app.config.from_mapping(
       SECRET_KEY='dev', #neccessary to run app
       DB_API_URL = os.getenv("DB_API_URL"), #local secret management wtih .env file
       DB_API_KEY = os.getenv("DB_API_KEY"), #local secret management wtih .env file
       AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY"), #local secret management wtih .env file
       AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY") #local secret management wtih .env file
    )

    app.config["UPLOAD_FOLDER"] = 'video_upload' #get rid of this
    app.config['UPLOAD_EXTENSIONS'] = ['.mp4']
    app.config["MAX_CONTENT_PATH"] = 30 * 1000 * 1000 # 30 megabyte upload limit

    app.config['S3_BUCKET_NAME'] = "engr-4450-fp"
    app.config['S3_LOCATION'] = 'https://engr-4450-fp.s3.us-east-2.amazonaws.com/'

    if main:
        #socketio.init_app(app, cors_allowed_origins=['http://127.0.0.1:5000'], manage_session=False)
        socketio.init_app(app, cors_allowed_origins=['http://127.0.0.1:5000', 'https://xp98kbcd-5000.use.devtunnels.ms/'], manage_session=False)
    else:
        socketio.init_app(None, async_mode='threading', manage_session=False)

    from . import db
    # from . import s3

    from . import auth
    app.register_blueprint(auth.bp)

    from . import live
    app.register_blueprint(live.bp)
    
    app.add_url_rule('/', endpoint='index')

    @app.after_request
    def after_request(response: Response) -> Response:
        response.access_control_allow_credentials = True
        return response

    @socketio.on('client_connecting')
    def client_connecting(msg): #client sends message that they connected
        timestamp = datetime.now().strftime("%d%m%Y%H%M%S%f")
        client_data = [msg['user_id'], msg['user_name'], timestamp] #user id, user name, when they connected

        for key,val in clients.items():#filter out duplicate users (waiting for one client session to go away)
            if msg['user_id'] == val[0]:
                clients.pop(key)
                break
        clients[request.sid] = client_data
        emit('update_clients',  {'data':clients}, broadcast=True)
        return

    @socketio.on('disconnect')
    def on_disconnect():
        clients.pop(request.sid)
        emit('update_clients',  {'data':clients}, broadcast=True) #emit update clients list for all users
        return
    
    return app

    

    
    #socketio = SocketIO(app)


    # if test_config is None:
    #     # load the instance config, if it exists, when not testing
    #     app.config.from_pyfile('config.py', silent=True)
    # else:
    #     # load the test config if passed in
    #     app.config.from_mapping(test_config)

    #ensure the instance folder exists
    # try:
    #     os.makedirs(app.instance_path)
    # except OSError:
    #     pass

    

    #@socketio.on('connect')
    #def tst_connect():
        #clients.append(session.get('user_id'))
        #print("----------- User Connected: ", session.get('user_id'))
        #emit('after connect',  {'data':'Lets dance'})
        #print(clients)
        # print('client connected', request.sid, session.get('user_id'))
        # print("client connected", session.get('user_id'))
        # if session.get('user_id') is not None:
        #     timestamp = datetime.now().strftime("%d%m%Y%H%M%S%f")
        #     client_data = [session.get('user_id'), timestamp]
            

        #     clients[request.sid] = client_data
        #     print(clients)
        # emit('client_connected', {'data': "test test test"}, broadcast=True)
     #   return