import os
from flask import Flask
from flask_socketio import SocketIO

from dotenv import load_dotenv
load_dotenv() #for local secret management with .env file

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True) #what is instance relative config?
    
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

    socketio = SocketIO(app)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    #ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    #db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import live
    app.register_blueprint(live.bp)
    
    app.add_url_rule('/', endpoint='index')
    
    return app

#how to configure this for socketio