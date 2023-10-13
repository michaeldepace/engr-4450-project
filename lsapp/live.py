from flask import (Blueprint, flash, g, redirect, render_template, request, url_for, current_app, session)
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from flask_cors import CORS, cross_origin
import os
from lsapp.auth import login_required
from lsapp.db import get_db
from flask_socketio import SocketIO

from flask import session, Response
from flask_socketio import emit, join_room, leave_room
from lsapp import socketio, clients


#from lsapp.ls_code.camera import Camera

bp = Blueprint('live', __name__)


@bp.route('/')
@login_required
#@cross_origin
def index():
    db = get_db()
    
    session["room"] = 1

    # for key in session:
    #     print(key, session[key])

    # url_query = request.args.to_dict()
    return render_template('live/index.html', users=clients)

@bp.route('/live/submission', methods=["GET", "POST"])
#@cross_origin
@login_required

def submit():
    if request.method == "POST":
        uploaded_video = request.files['file']
        filename = secure_filename(uploaded_video.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in current_app.config["UPLOAD_EXTENSIONS"]:
                abort(400)
            uploaded_video.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            
        return redirect(url_for('live.submit'))
    else:
        return render_template('live/submit.html')


@socketio.on('test')
def test(msg):
    return
    #print("test")
    #print(msg)
    #print(lsapp.clients)



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