from flask import current_app, g
from werkzeug.utils import secure_filename
import boto3

# establishes and returns connection to s3 bucket that route/view methods can use to upload video and image files
def connect_to_s3():
    s3 = boto3.resource(
        "s3",
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY'],
        aws_secret_access_key=current_app.config['AWS_SECRET_KEY']
    )
    return s3