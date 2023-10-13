import os
from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    load_dotenv() #for local secret management with .env file
    SECRET_KEY='dev' #neccessary to run app #???
    DB_API_URL = os.getenv("DB_API_URL"), #local secret management wtih .env file
    DB_API_KEY = os.getenv("DB_API_KEY") #local secret management wtih .env file
    DEBUG = True


# class ProductionConfig(Config):
#     SECRET_KEY='prod' #???
#     db_api_url = os.environ["DB_API_URL"], #supabase api url gh secret
#     db_api_key = os.environ["DB_API_KEY"] #supabase api key gh secret
#     pass


# class TestingConfig(Config):
#     TESTING = True
#     SQLALCHEMY_DATABASE_URI = 'sqlite://'
#     CELERY_CONFIG = {'CELERY_ALWAYS_EAGER': True}
#     SOCKETIO_MESSAGE_QUEUE = None


config = {
    'development': DevelopmentConfig,
    #'production': ProductionConfig,
    #'testing': TestingConfig
}