from flask import (Blueprint, flash, g, redirect, render_template, request, Response, url_for, current_app, session, jsonify)
from werkzeug.utils import secure_filename
import os
from datetime import datetime   
import boto3
from lsapp.auth import login_required
from lsapp.db import get_db
from lsapp.s3 import connect_to_s3
# from lsapp import socketio, clients

bp = Blueprint('live', __name__)


#handle missing request id client dictionary key pop error 

@bp.route('/')
@login_required
def index():
    db = get_db()
    leaderboard_vids = db.table("video_like_data").select("*").order("num_likes", desc=True).limit(5).execute().data
    like_data = db.table("video_likes").select("*").eq('user_id', g.user["usr_id"]).execute().data
    liked_video_ids = []
    for item in like_data:
        liked_video_ids.append(item['vid_id'])
    return render_template('live/index.html', videos=leaderboard_vids, likes=liked_video_ids)

@bp.route('/videos')
@login_required
def all_videos():
    db = get_db()
    vids = db.table("video_like_data").select("*").order('created_at', desc=True).execute().data
    like_data = db.table("video_likes").select("*").eq('user_id', g.user["usr_id"]).execute().data
    liked_video_ids = []
    for item in like_data:
        liked_video_ids.append(item['vid_id'])
    return render_template('live/videos.html', videos=vids, likes=liked_video_ids)

@bp.route('/submission', methods=["GET", "POST"])
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

        return redirect(url_for('live.index'))
    else:
        return render_template('live/submit.html')

@bp.route('/like/<video_id>', methods=["POST"])
@login_required
def like_video(video_id):
    db = get_db()
    likes = db.table("video_likes").select('*', count='exact').eq('vid_id', video_id).eq('user_id', g.user["usr_id"]).execute().count
    if likes == 0:
        db.table("video_likes").insert({'vid_id': video_id, 'user_id':g.user["usr_id"]}).execute()
    return redirect(url_for('live.index'))

@bp.route('/unlike/<video_id>', methods=["POST"])
@login_required
def unlike_video(video_id):
    db = get_db()
    likes = db.table("video_likes").select('*', count='exact').eq('vid_id', video_id).eq('user_id', g.user["usr_id"]).execute().count
    if likes != 0:
        db.table("video_likes").delete().eq('vid_id', video_id).eq('user_id', g.user["usr_id"]).execute()
    return redirect(url_for('live.index'))