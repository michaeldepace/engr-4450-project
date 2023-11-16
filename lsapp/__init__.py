from flask import (Flask, render_template, Response, Blueprint, flash, g, redirect, request, url_for)
# from flask_socketio import SocketIO, emit
import os
from datetime import datetime
from werkzeug.exceptions import HTTPException


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
#from flask_cors import CORS

# socketio = SocketIO()
# clients = {}

def create_app(debug=True, main=True):
    app = Flask(__name__)
    #CORS(app, origins=['http://localhost:5000', 'http://127.0.0.1:5000/'])
    #DEPLOYMENT CODE - GITHUB SECRETS 
    # app.config.from_mapping(
    #     SECRET_KEY='abracadaniel', #neccessary to run app
    #     DB_API_URL = os.environ["DB_API_URL"], #supabase api url gh secret
    #     DB_API_KEY = os.environ["DB_API_KEY"], #supabase api key gh secret
    #     #AWS_ACCESS_KEY = os.environ["AWS_ACCESS_KEY"], #aws access key gh secret
    #     #AWS_SECRET_KEY = os.environ["AWS_SECRET_KEY"] #aws secret key gh secret
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
    app.config['UPLOAD_EXTENSIONS'] = ['mp4']
    app.config["MAX_CONTENT_PATH"] = 30 * 1000 * 1000 # 30 megabyte upload limit

    app.config['S3_BUCKET_NAME'] = "engr-4450-fp"
    app.config['S3_LOCATION'] = 'https://engr-4450-fp.s3.us-east-2.amazonaws.com/'

    #if main:
        #socketio.init_app(app, cors_allowed_origins=['http://127.0.0.1:5000'], manage_session=False)
        #socketio.init_app(app, cors_allowed_origins=['http://127.0.0.1:5000', 'https://engr-4450-fp-74ee1ca5fd3f.herokuapp.com/'], manage_session=False)

    #else:
        #socketio.init_app(None, async_mode='threading', manage_session=False)

    from . import db
    from . import s3

    from . import auth
    app.register_blueprint(auth.bp)

    from . import live
    app.register_blueprint(live.bp)
    
    app.add_url_rule('/', endpoint='index')


    # handle application errors
    @app.errorhandler(404)
    def not_found_error(er):
        message = "This page doesn't exist silly :/"
        return render_template('error/error.html', msg=message)

    @app.errorhandler(500)
    def internal_error(er):
        message = "There's an error on our end ¯\_(ツ)_/¯"
        return render_template('error/error.html', msg=message)

    @app.errorhandler(HTTPException)
    def generic_error(er):
        message = "There's an error on our end ¯\_(ツ)_/¯"
        return render_template('error/error.html', msg=message)

    # @app.after_request
    # def after_request(response: Response) -> Response:
    #     #response.access_control_allow_credentials = True
    #     response.access_control_allow_credentials = True
    #     response.headers['Access-Control-Allow-Origin'] = '*'
    #     response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    #     response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Requested-With"
    #     return response
    
    return app