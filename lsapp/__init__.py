from flask import (Flask, render_template, Response, Blueprint, flash, g, redirect, request, url_for)
import os
from datetime import datetime
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv
load_dotenv() #used for local secret management with .env file

# configures and generates a running flask application instance 
def create_app(debug=True, main=True):
    app = Flask(__name__)
    
    # grabbing environment secret keys
    app.config.from_mapping(
       SECRET_KEY= os.getenv("SECRET_KEY"), 
       DB_API_URL = os.getenv("DB_API_URL"),
       DB_API_KEY = os.getenv("DB_API_KEY"), 
       AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY"), 
       AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY") 
    )

    # importing database and s3 connection code 
    from . import db
    from . import s3

    # importing auth.py application routes, pages, and logic
    from . import auth
    app.register_blueprint(auth.bp)

    # importing live.py application routes, pages, and logic
    from . import live
    app.register_blueprint(live.bp)
    
    app.add_url_rule('/', endpoint='index') #setting default domain route

    # serve a custom error page for 404 not found error
    @app.errorhandler(404)
    def not_found_error(er):
        message = "This page doesn't exist silly :/"
        return render_template('error/error.html', msg=message)

    # serve a custom error page for all other HTTP error codes
    @app.errorhandler(HTTPException)
    def generic_error(er):
        message = "There's an error on our end ¯\_(ツ)_/¯"
        return render_template('error/error.html', msg=message)

    return app #returns application instance for execution