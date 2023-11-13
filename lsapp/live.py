from flask import (Blueprint, flash, g, redirect, render_template, request, Response, url_for, current_app, session, jsonify)
from werkzeug.utils import secure_filename
import os
from datetime import datetime   
import boto3
from flask_cors import cross_origin
from lsapp.auth import login_required
from lsapp.db import get_db
from lsapp.s3 import connect_to_s3



bp = Blueprint('live', __name__)


#handle missing request id client dictionary key pop error 

@bp.route('/')
@login_required
def index():
    db = get_db()
    leaderboard_vids = db.table("video_data").select("*").order("num_likes", desc=True).limit(5).execute().data
    like_data = db.table("video_likes").select("*").eq('user_id', g.user["usr_id"]).execute().data
    liked_video_ids = []
    for item in like_data:
        liked_video_ids.append(item['vid_id'])
    return render_template('live/index.html', videos=leaderboard_vids, likes=liked_video_ids)

@bp.route('/videos')
@login_required
@cross_origin()
def all_videos():
    db = get_db()
    vids = db.table("video_data").select("*").order('created_at', desc=True).execute().data
    
    like_data = db.table("video_likes").select("*").eq('user_id', g.user["usr_id"]).execute().data
    liked_video_ids = []
    for item in like_data:
        liked_video_ids.append(item['vid_id'])

    comment_data = db.table("comment_data").select("*").execute().data
    comment_dictionary = {}
    for record in vids:
        vid_id = record["vid_id"]
        comment_dictionary[vid_id] = []

    for record in comment_data:
        comment_vid_id = record["video_id"]
        comment_dictionary[comment_vid_id].append(record)

    return render_template('live/videos.html', videos=vids, likes=liked_video_ids, comments=comment_dictionary)

@bp.route('/submission', methods=["GET", "POST"])
@login_required
def submit():
    db = get_db()
    s3 = connect_to_s3()
    if request.method == "POST":
        uploaded_video = request.files['file']
        upload_filesize = uploaded_video.seek(0, os.SEEK_END)
        upload_filename = secure_filename(uploaded_video.filename)

        if upload_filesize > 30000000: #30 mb limit for uploads
            flash('The uploaded file is too big. 30 mb upload limit, please try again.')
            return redirect(url_for('live.submit'))

        if upload_filename == '':
            flash('Invalid file name. Please try again.')
            return redirect(url_for('live.submit'))

        if '.' not in upload_filename or upload_filename.rsplit('.', 1)[1].lower() not in current_app.config["UPLOAD_EXTENSIONS"]:
            flash('Incorrect file type. MP4 files only, please try again.')
            return redirect(url_for('live.submit'))

        timestamp = datetime.now().strftime("%d%m%Y%H%M%S%f")
        user_id = g.user["usr_id"]
        file_name = f'vid-{user_id}-{timestamp}.mp4'

        try:
            s3.meta.client.upload_fileobj(uploaded_video, 'engr-4450-fp', file_name)
            db.table("submissions").insert({"uploader_id": user_id, "video_s3_path": file_name}).execute()
        except Exception as e:
            print(e) 
            flash('We had a problem uploading your video. Please try again or contact support.')

        return redirect(url_for('live.submit'))
    else:
        return render_template('live/submit.html')

@bp.route('/profile')
@login_required
def profile():
    db = get_db()
    vids = db.table("video_data").select("*").eq('uploader_id', g.user["usr_id"]).execute().data
    vid_id_list = []

    for record in vids:
        # Put this list so that I can check what comments need printed two steps down
        vid_id_list.append(record['vid_id'])

    like_data = db.table("video_likes").select("*").eq('user_id', g.user["usr_id"]).execute().data
    liked_video_ids = []
    for item in like_data:
        liked_video_ids.append(item['vid_id'])

    comment_data = db.table("comment_data").select("*").in_("video_id",vid_id_list).execute().data
    comment_dictionary = {}
    for record in vids:
        vid_id = record["vid_id"]
        comment_dictionary[vid_id] = []

    for record in comment_data:
        # Run into a KeyError as it tries to render comments that do not exist, which is why vid_id_list exists
        comment_vid_id = record["video_id"]
        comment_dictionary[comment_vid_id].append(record)

    user_profile_data = db.table("users").select("*").eq('usr_id', g.user['usr_id']).execute().data[0]
    user_profile_data["usr_created_at"] = str(user_profile_data["usr_created_at"])[:10]#.strftime('%m/%d/%Y, %H:%M:%S')

    #this query only grabs videos from the submissions table that have been liked by the current user
    liked_video_data = db.table("video_data").select('*, video_likes(user_id)').eq('video_likes.user_id', g.user["usr_id"]).not_.is_('video_likes', 'null').execute().data 

    return render_template('live/profile.html', videos=vids, likes=liked_video_ids, comments=comment_dictionary, user_profile_data=user_profile_data, liked_vids=liked_video_data)

@bp.route('/video/<vid_id>', methods=["GET"]) #view and individual video on its own page
@login_required
def view_video(vid_id):
    db = get_db()
    vids = db.table("video_data").select("*").eq('vid_id', vid_id).execute().data
    
    like_data = db.table("video_likes").select("*").eq('user_id', g.user["usr_id"]).eq('vid_id', vid_id).execute().data
    liked_video_ids = []
    for item in like_data:
        liked_video_ids.append(item['vid_id'])

    comment_data = db.table("comment_data").select("*").eq('video_id', vid_id).execute().data
    comment_dictionary = {}
    
    for record in vids:
        vid_id = record["vid_id"]
        comment_dictionary[vid_id] = []

    for record in comment_data:
        comment_vid_id = record["video_id"]
        comment_dictionary[comment_vid_id].append(record)

    return render_template('live/video.html', videos=vids, likes=liked_video_ids, comments=comment_dictionary)
    #return render_template('live/video.html', video=vid)

@bp.route('/like/<video_id>', methods=["POST"])
@login_required
def like_video(video_id):
    db = get_db()
    likes = db.table("video_likes").select('*', count='exact').eq('vid_id', video_id).eq('user_id', g.user["usr_id"]).execute().count
    if likes == 0:
        db.table("video_likes").insert({'vid_id': video_id, 'user_id':g.user["usr_id"]}).execute()
    new_vid_likes = db.table("video_likes").select('*', count='exact').eq('vid_id', video_id).execute().count
    #print('__________________________________new likes: ', new_vid_likes)
    #return redirect(url_for('live.index'))
    return str(new_vid_likes)

@bp.route('/unlike/<video_id>', methods=["POST"])
@login_required
def unlike_video(video_id):
    db = get_db()
    likes = db.table("video_likes").select('*', count='exact').eq('vid_id', video_id).eq('user_id', g.user["usr_id"]).execute().count
    if likes != 0:
        db.table("video_likes").delete().eq('vid_id', video_id).eq('user_id', g.user["usr_id"]).execute()
    new_vid_likes = db.table("video_likes").select('*', count='exact').eq('vid_id', video_id).execute().count
    #print('__________________________________new likes: ', new_vid_likes)
    #return redirect(url_for('live.index'))
    return str(new_vid_likes) #Response(status=204)


@bp.route('/video/comment', methods=["POST"])
@login_required
def submit_video_comment():
    db = get_db()
    user_id = request.form['user_id']
    vid_id = request.form['vid_id']
    comment_text = request.form['comment_text']
    db.table("comments").insert({"user_id": user_id, "video_id": vid_id, "comment_text":comment_text }).execute()
    return redirect(request.referrer)