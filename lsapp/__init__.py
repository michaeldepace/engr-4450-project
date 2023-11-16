from flask import (Flask, render_template, Response, Blueprint, flash, g, redirect, request, url_for)
import os
from datetime import datetime
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv
load_dotenv() #used for local secret management with .env file

# configures and generates a running flask application instance 
def create_app(debug=True, main=True):
    app = Flask(__name__)
    #CORS(app, origins=['http://localhost:5000', 'http://127.0.0.1:5000/'])
    
    # grabbing environment secret keys
    app.config.from_mapping(
       SECRET_KEY= os.getenv("SECRET_KEY"), 
       DB_API_URL = os.getenv("DB_API_URL"),
       DB_API_KEY = os.getenv("DB_API_KEY"), 
       AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY"), 
       AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY") 
    )

    #app.config["UPLOAD_FOLDER"] = 'video_upload' #get rid of this
    #app.config['UPLOAD_EXTENSIONS'] = ['mp4']
    #app.config["MAX_CONTENT_PATH"] = 30 * 1000 * 1000 # 30 megabyte upload limit

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


    # show custom error page for 404 error
    @app.errorhandler(404)
    def not_found_error(er):
        message = "This page doesn't exist silly :/"
        return render_template('error/error.html', msg=message)

    # @app.errorhandler(500)
    # def internal_error(er):
    #     message = "There's an error on our end ¯\_(ツ)_/¯"
    #     return render_template('error/error.html', msg=message)

    # show custom error page for all other HTTP error codes
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