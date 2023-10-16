from flask import Flask, render_template, Response
from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from flask_socketio import SocketIO, emit
from flask_cors import CORS, cross_origin
import os
from flask import Flask, Response
from flask_socketio import SocketIO, join_room, leave_room
#import eventlet
#from config import config
from flask_cors import CORS, cross_origin
from datetime import datetime
from flask_session import Session
#from flask_apscheduler import APScheduler


from dotenv import load_dotenv
load_dotenv() #for local secret management with .env file

socketio = SocketIO()
clients = {}

def create_app(debug=True, main=True):#config_name='dubug', main=True):
    # if config_name is None:
    #     config_name = os.environ.get('FLACK_CONFIG', 'development') #not using this right now 
    
    app = Flask(__name__)
    #CORS(app)
    #app.config.from_object(config[config_name])

    #DEPLOYMENT CODE - GITHUB SECRETS 
    # app.config.from_mapping(
    #     db_api_url = os.environ["DB_API_URL"], #supabase api url gh secret
    #     db_api_key = os.environ["DB_API_KEY"] #supabase api key gh secret
    # )

    #DEVELOPMENT CODE - LOCAL SECRETS
    app.config.from_mapping(
       SECRET_KEY='dev', #neccessary to run app
       DB_API_URL = os.getenv("DB_API_URL"), #local secret management wtih .env file
       DB_API_KEY = os.getenv("DB_API_KEY") #local secret management wtih .env file
    )


    app.config["UPLOAD_FOLDER"] = 'video_upload'
    app.config['UPLOAD_EXTENSIONS'] = ['.mp4']
    app.config["MAX_CONTENT_PATH"] = 30 * 1000 * 1000 # 30 megabyte upload limit

    if main:
        socketio.init_app(app, cors_allowed_origins=['http://127.0.0.1:5000'], manage_session=False)
    else:
        socketio.init_app(None, async_mode='threading', manage_session=False)

    from . import db
    #db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import live
    app.register_blueprint(live.bp)
    
    app.add_url_rule('/', endpoint='index')

    @app.after_request
    def after_request(response: Response) -> Response:
        response.access_control_allow_credentials = True
        # response.access_control_allow_origin="*"
        return response

    @socketio.on('client_connecting')
    def client_connecting(msg): #client sends message that they connected
        timestamp = datetime.now().strftime("%d%m%Y%H%M%S%f")
        client_data = [msg['user_id'], msg['user_name'], timestamp]
        clients[request.sid] = client_data
        print("client is connecting", client_data)
        print(clients)

        #filter out duplicate users (waiting for one client session to go away)

        emit('update_clients',  {'data':clients}, broadcast=True)
        return

    @socketio.on('disconnect')
    def on_disconnect():
        #print("client disconnected", request.sid)
        #if session.get('user_id') is not None:
        clients.pop(request.sid)
        print(clients)
        #emit update clients list for all users
        emit('update_clients',  {'data':clients}, broadcast=True)
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

    