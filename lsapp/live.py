from flask import (Blueprint, flash, g, redirect, render_template, request, Response, url_for, current_app, session, jsonify, abort)
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import boto3
from lsapp.auth import login_required
from lsapp.db import get_db
from lsapp.s3 import connect_to_s3

bp = Blueprint('live', __name__) # register/connect this script with the html template files and http url routes

# The first decorator (bp.route) constructs the route that this function will be called for
# In this instance, this is the leaderboard found at the site index, so the route is
# simply / (from the url that is not needed to be specified as it can change)

# Then login_required ensures that this route can only be accessed if the user
# is currently logged in.
# It basically just checks if a user is logged in and if not it redirects to 
# a log in page

@bp.route('/')
@login_required
def index():
    # Lots of functions will have this line here
    db = get_db()
    # This just creates a client to communicate with the data base

    # Use said client to make calls to the data base, in this particular the
    # function asks for it in descending order by like count, and only grabs 5
    # then it checks the likes table to see which videos the current user has liked
    # so it can correctly display which ones are liked and which can be liked
    leaderboard_vids = db.table("video_data").select("*").order("num_likes", desc=True).limit(5).execute().data
    like_data = db.table("video_likes").select("*").eq('user_id', g.user["usr_id"]).execute().data
    # List of liked videos, this list will store the videos that the user liked
    # in a way that we can use when we render the template
    liked_video_ids = []
    for item in like_data:
        liked_video_ids.append(item['vid_id'])
    # render_template will be seen a lot, its the main call
    # to render an html page using a template stored in the first argument
    # the next few are variables needed for the template
    # like what videos to display and which are liked
    return render_template('live/index.html', videos=leaderboard_vids, likes=liked_video_ids)

@bp.route('/videos')
@login_required
#@cross_origin()
def all_videos():
    db = get_db()
    # this call sorts by creation date to show each video in order of most recent post
    vids = db.table("video_data").select("*").order('created_at', desc=True).execute().data
    # again, this like_data call will grab the videos this user liked
    # and make it so they cannot like them again
    like_data = db.table("video_likes").select("*").eq('user_id', g.user["usr_id"]).execute().data
    liked_video_ids = []
    for item in like_data:
        liked_video_ids.append(item['vid_id'])
    # These are all the comments stored in the comment database
    # we then store each comment in a dictionary with its video in a list
    # so essentially, each video id is a key in the dict
    # each key has a empty list, which each comment gets appended to
    # so a key will have a list with all the comment strings that then
    # will get attched to the videos in the template
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
    # Now we have connect_to_s3 which uses boto3 to open a connection with the S3 Server
    # this connection allows us to send videos to the server to be stored
    s3 = connect_to_s3()
    if request.method == "POST":
        # If statement ensures the user has sent a file, otherwise ask for a file
        uploaded_video = request.files['file']
        # Checking the file object size in bytes
        # basically just go from start to end and thats how many bytes it is
        upload_filesize = uploaded_video.seek(0, 2)
        # this sets the pointer to the front of the file, so that it can continue to read files
        uploaded_video.seek(0, os.SEEK_SET)
        # Secure_filename checks the filename, ensures its not constructed in a way that can cause problems
        # such as /../../../
        upload_filename = secure_filename(uploaded_video.filename)

        # check if video file size is creater than 30 mb limit
        if upload_filesize > 30000000: 
            flash('The uploaded file is too big. 30 mb upload limit, please try again.')
            return redirect(url_for('live.submit'))
        # check if video file exists at all and isnt an empty file
        if upload_filesize == 0:
            flash('The uploaded file is not valid. Please try again.')
            return redirect(url_for('live.submit'))

        # make sure the filename isn't empty
        if upload_filename == '':
            flash('Invalid file name. Please try again.')
            return redirect(url_for('live.submit'))

        # make sure the file extension is .mp4
        if '.' not in upload_filename or upload_filename.rsplit('.', 1)[1].lower() != 'mp4': #not in current_app.config["UPLOAD_EXTENSIONS"]:
            flash('Incorrect file type. MP4 files only, please try again.')
            return redirect(url_for('live.submit'))
        # Get upload time
        timestamp = datetime.now().strftime("%d%m%Y%H%M%S%f")
        user_id = g.user["usr_id"]
        # craft the file name withh the user id and upload time
        file_name = f'vid-{user_id}-{timestamp}.mp4'
        # Try and send the file to the bucket, specifying that it is mp4 video again and update the table of videos with the new video
        try:
            s3.meta.client.upload_fileobj(uploaded_video, 'engr-4450-fp', file_name, ExtraArgs={"ContentType": "video/mp4"}) # push the file data to the s3 bucket
            db.table("submissions").insert({"uploader_id": user_id, "video_s3_path": file_name}).execute() # log uploaded video in submissions db table
        except Exception as e:
            flash('We had a problem uploading your video. Please try again or contact support.')

        return redirect(url_for('live.submit'))
    else:
        return render_template('live/submit.html')

@bp.route('/video/<vid_id>', methods=["GET"]) #view and individual video on its own page
@login_required
def view_video(vid_id):
    # EXTREMELY similar to all_videos, but instead only gets the one video and makes sure
    # that video block doesnt have a link to itself, as it is on its own page
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

    return render_template('live/video.html', videos=vids, likes=liked_video_ids, comments=comment_dictionary, hidelink=True)

@bp.route('/like/<video_id>', methods=["POST"])
@login_required
def like_video(video_id):
    # this function finds the video that the user is attempting to like
    # if it has no likes, itll create the format for a liked video
    # i.e. video id and the user id who likes it is appended
    # in the like table it stores a list of each user who liked it
    # so that users who liked a video do not like it again
    db = get_db()
    likes = db.table("video_likes").select('*', count='exact').eq('vid_id', video_id).eq('user_id', g.user["usr_id"]).execute().count
    if likes == 0:
        db.table("video_likes").insert({'vid_id': video_id, 'user_id':g.user["usr_id"]}).execute()
    new_vid_likes = db.table("video_likes").select('*', count='exact').eq('vid_id', video_id).execute().count
    return str(new_vid_likes)

@bp.route('/unlike/<video_id>', methods=["POST"])
@login_required
def unlike_video(video_id):
    # same deal here just slightly different because now if the video has no likes we an actully get rid of the entry
    db = get_db()
    likes = db.table("video_likes").select('*', count='exact').eq('vid_id', video_id).eq('user_id', g.user["usr_id"]).execute().count
    if likes != 0:
        db.table("video_likes").delete().eq('vid_id', video_id).eq('user_id', g.user["usr_id"]).execute()
    new_vid_likes = db.table("video_likes").select('*', count='exact').eq('vid_id', video_id).execute().count
    return str(new_vid_likes)

@bp.route('/video/comment', methods=["POST"])
@login_required
def submit_video_comment():
    # similarly to liking a video, this goes to the comment table, and adds an entry into
    # the comment dictionary entry for the video id in the request, then
    # redirect(request.referrer) sends the user back where they came
    db = get_db()
    user_id = request.form['user_id']
    vid_id = request.form['vid_id']
    comment_text = request.form['comment_text']
    db.table("comments").insert({"user_id": user_id, "video_id": vid_id, "comment_text":comment_text }).execute()
    return redirect(request.referrer)

@bp.route('/profiles/<user_id>', methods=["GET"])
@login_required
def view_profile(user_id):
    db = get_db()
    # quick check here, if a user clicks on the My Profile button, they go to
    # /myprofile
    # but if they click on a name on the all_videos or index page
    # they go to /profile/user_id
    # so you could go to your profile page assuming you arent you
    # so this ensures that if you attempt to go to your profile that isnt
    # /myprofile
    # you will be taken there instead
    if int(g.user['usr_id']) == int(user_id):
        return redirect(url_for('auth.profile'))

    uploaded_vids = db.table("video_data").select("*").eq('uploader_id', user_id).execute().data
    vid_id_list = []

    for record in uploaded_vids:
        # Put this list so that I can check what comments need printed two steps down
        vid_id_list.append(record['vid_id'])

    like_data = db.table("video_likes").select("*").eq('user_id', g.user['usr_id']).execute().data
    liked_video_ids = []
    for item in like_data:
        liked_video_ids.append(item['vid_id'])

    comment_data = db.table("comment_data").select("*").in_("video_id",vid_id_list).execute().data
    comment_dictionary = {}
    for record in uploaded_vids:
        vid_id = record["vid_id"]
        comment_dictionary[vid_id] = []

    for record in comment_data:
        # Run into a KeyError as it tries to render comments that do not exist, which is why vid_id_list exists
        comment_vid_id = record["video_id"]
        comment_dictionary[comment_vid_id].append(record)

    user_profile_data = db.table("users").select("*").eq('usr_id', user_id).execute().data[0]
    user_profile_data["usr_created_at"] = str(user_profile_data["usr_created_at"])[:10]

    #this query only grabs videos from the submissions table that have been liked by the current user
    liked_video_data = db.table("video_data").select('*, video_likes(user_id)').eq('video_likes.user_id', user_id).not_.is_('video_likes', 'null').execute().data 

    return render_template('live/profiles.html', videos=uploaded_vids, likes=liked_video_ids, comments=comment_dictionary, user_profile_data=user_profile_data, liked_vids=liked_video_data)