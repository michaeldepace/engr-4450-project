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

    if main:
        socketio.init_app(app, cors_allowed_origins=['http://127.0.0.1:5000'])
    else:
        socketio.init_app(None, async_mode='threading')

    # def scheduleTask():
    #     emit('after connect',  {'data':'Lets dance'})

    @app.after_request
    def after_request(response: Response) -> Response:
        response.access_control_allow_credentials = True
        # response.access_control_allow_origin="*"
        print('test test test')
        return response

    

    # scheduler = APScheduler()
    # scheduler.add_job(id = 'Scheduled Task', func=scheduleTask, trigger="interval", seconds=3)
    # scheduler.start()

    # @socketio.on('joined')
    # def joined(msg):
    #     print('\n\na client joined\n\n')

    # @socketio.on('left')
    # def joined(msg):
    #     print('\n\n-------------------------a client left\n\n')


    @socketio.on('disconnect')
    def on_disconnect():
        print("--------------- client disconnected", request.sid)
        if session.get('user_id') is not None:
            clients.pop(request.sid)
        print(clients)
        return


    @socketio.on('connect')
    def test_connect():
        #clients.append(session.get('user_id'))
        #print("----------- User Connected: ", session.get('user_id'))
        #emit('after connect',  {'data':'Lets dance'})
        #print(clients)
        print('client connected', request.sid)

        if session.get('user_id') is not None:
            client = None
            timestamp = datetime.now()

            clients[request.sid] = [session.get('user_id'), timestamp]

            emit('client_connected', {'data': 'test'})

        
        print(clients)
        return

    @socketio.on('test')
    def test():
        print("--------------- test message ")
        #print(clients)


    def check_connection(msg):
        socketio.emit()
        return

    @socketio.on('verified_connection')
    def verified_connection(msg):
        return


















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

    from . import db
    #db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import live
    app.register_blueprint(live.bp)
    
    app.add_url_rule('/', endpoint='index')

    return app