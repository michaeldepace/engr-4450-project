from flask import (Blueprint, flash, g, redirect, render_template, request, Response, url_for, current_app, session)
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
#from flask_cors import CORS, cross_origin
import os
from lsapp.auth import login_required
from lsapp.db import get_db
from lsapp.s3 import connect_to_s3
from flask_socketio import SocketIO
from flask import session#, Response
from flask_socketio import emit, join_room, leave_room
from lsapp import socketio, clients
from datetime import datetime   
from werkzeug.utils import secure_filename
import boto3

bp = Blueprint('live', __name__)


#handle missing request id client dictionary key pop error 

@bp.route('/')
@login_required
def index():
    db = get_db()
    leaderboard_vids = db.table("submissions").select("*").order("num_likes", desc=True).limit(5).execute().data
    #vids = db.table("submissions").select("*").order('num_likes', desc=True).execute().data

    return render_template('live/index.html', users=clients, videos=leaderboard_vids)

@bp.route('/live/submission', methods=["GET", "POST"])
#@cross_origin
@login_required

def submit():
    db = get_db()
    s3 = connect_to_s3()

    if request.method == "POST":
        uploaded_video = request.files['file']
        filename = secure_filename(uploaded_video.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            #if file_ext not in current_app.config["UPLOAD_EXTENSIONS"]:
            #    abort(400)
            

            #uploaded_video.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

            timestamp = datetime.now().strftime("%d%m%Y%H%M%S%f")
            user_id = g.user["usr_id"]
            file_name = f'vid-{user_id}-{timestamp}.mp4'
            try:
                s3.meta.client.upload_fileobj(uploaded_video, 'engr-4450-fp', file_name)
                db.table("submissions").insert({"uploader_id": user_id, "video_s3_path": file_name}).execute()
            except Exception as e:
                print(e) #do something

        return redirect(url_for('live.submit'))
    else:
        return render_template('live/submit.html')

@bp.route('/like/<video_id>', methods=["POST"])
@login_required
def like_video(video_id):
    db = get_db()
    likes = db.table("submissions").select('num_likes').eq('vid_id', video_id).execute().data[0]['num_likes']
    db.table("submissions").update({'num_likes': likes + 1}).eq('vid_id', video_id).execute()
    return ('', 204)


@bp.route('/live/videos')
@login_required
def all_videos():
    db = get_db()
    vids = db.table("submissions").select("*").order('num_likes', desc=True).execute().data

    return render_template('live/videos.html', users=clients, videos=vids)


"""Old code remove later """

# @bp.route('/live/broadcast')
# @login_required
# def broadcast():
#     #print(g.user.data)
#     return render_template('live/broadcast.html')


# def gen(camera):
#     while True:
#         frame = camera.get_frame()

#         #cam = cv2.VideoCapture(0)
#         #_, frame = cam.read()
#         #frame = cv2.imencode('.jpg', frame)[1].tobytes() # encode as a jpeg image and return it


#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# @bp.route('/video_feed')
# @login_required
# def video_feed():
#     return Response(gen(Camera()),
#                     mimetype='multipart/x-mixed-replace; boundary=frame')

# <div style="border: 2px solid black; display:flex; align-items:center;">
#     <img style="width:100%; height:100%;" src="{{ url_for('live.video_feed') }}">
# </div>