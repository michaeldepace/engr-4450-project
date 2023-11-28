from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
import functools
from lsapp.db import get_db
from werkzeug.utils import secure_filename
from lsapp.s3 import connect_to_s3
from datetime import datetime
import os
import re

bp = Blueprint('auth', __name__) # register/connect this script with the html template files and http url routes

# create a wrapper for route functions that require you to be logged in before accessing the route in question
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None: # checks if the user isn't logged in
            return redirect(url_for('auth.login')) #redirect them to the login page so they can log in
        return view(**kwargs) #allows the user to go ahead and access their secured page
    return wrapped_view

# register a function that runs before every page request to make current user info accessible across application
@bp.before_app_request # this just makes sure that the user info is available before each request/page load so it is seamlessly available at all times
def load_logged_in_user():
    user_id = session.get('user_id') #checks if user id is stored in current session data

    if user_id is None: #if it isn't then there is no user logged in
        g.user = None
    else: #if there is a user id, then set the grab the user's account data for this request cycle
        g.user = get_db().table("users").select("usr_id, usr_login, usr_created_at, prof_pic_s3_path").eq("usr_id", user_id).execute().data[0] # grabs and caches user data from supabase

# function that runs for the <domain>/register route
# responsible for serving a register account form page to the user and accepting submitted input from that form
# handles validating registration account credentials and creating user account in database
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST': #application logic to handle user submitting register form
        username = request.form['username'] # grab username from submitted form data
        password = request.form['password'] # grab password from submitted form data
        db = get_db() #establish a connection to supabase
        error = None

        #series of checks to validate submitted username and password fields  
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif db.table("users").select("*", count='exact').eq('usr_login', username).execute().count > 0: #checks if the username exists already in the database
            error = "This username is taken."
        elif checkPassword(password) != "":
            error = checkPassword(password) #validate password using separate password validation function

        if error is None: # if there are no problems with the username and password, then the user is registered and their account information is stored in the database
            try:
                # store the user account information in the database
                db.table("users").insert({"usr_login": username, "usr_password": generate_password_hash(password)}).execute()
            except BaseException as e:
                error = "error " + e.message
            else:
                return redirect(url_for("auth.login")) #redirect the user to log in 
        flash(error) # display the error message to the user

        g.reg_usr = username #store username attempt for next request cycle
        g.reg_pwd = password #store password attempt for next request cycle
    return render_template('auth/register.html') #redirect to register page so the user can try again to register 

# function that runs for the <domain>/register route
# responsible for serving a register account form page to the user and accepting submitted input from that form
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']# grab username from submitted form data
        password = request.form['password']# grab password from submitted form data
        db = get_db() #establish a connection to supabase
        error = None
        user = None
        usr_data = db.table("users").select("*").eq("usr_login", username).execute().data
        if len(usr_data) > 0:
            user = db.table("users").select("*").eq("usr_login", username).execute().data[0]
        
        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['usr_password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['usr_id']
            session['user_name'] = user['usr_login']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')


@bp.route('/logout') # clears the session data (including login cookie), and redirects to the home page when the user logs out
def logout():
    session.clear() # clears session cookie of any login/auth confirmation 
    return redirect(url_for('index')) # redirects user to home page (leaderboard)

@bp.route('/password', methods=('GET', 'POST'))
@login_required
def change_password():
    if request.method == 'POST':
        confirm_password = request.form['confirm-password']
        password = request.form['password']
        db = get_db()
        error = None

        if not password:
            error = 'Password is required.'
        elif not confirm_password:
            error = 'Password confirmation is required.'
        elif password != confirm_password:
            error = 'Passwords must match'
        elif checkPassword(password) != "":
            error = checkPassword(password)

        if error is None:
            try:
                db.table("users").update({"usr_password": generate_password_hash(password)}).eq('usr_id', g.user['usr_id']).execute()
            except BaseException as e:
                error = "error " + e.message
            else:
                return redirect(url_for("auth.profile"))
        flash(error)

        g.c_pwd = password
        g.c_cnf_pwd = confirm_password

        return redirect(url_for('auth.change_password'))
    else:
        return render_template('auth/change-pswd.html')

# Checks if an inputted password follows a set of password rules (length, numbers, special characters)
def checkPassword(pwd):
    message = ""
    
    if len(pwd) < 12: # Check if password is at least 12 characters
        message = "Password must be at least 12 characters."
    elif re.search(r"\d", pwd) is None: # Check if it contains at least one digit
        message = "Password must contain at least 1 digit."
    elif re.search(r"[a-zA-Z]", pwd) is None: # Check if it contains at least 1 letter
        message = "Password must contain at least 1 letter."
    elif re.compile('[@_!#$%^&*()<>?/\|}{~:]').search(pwd) is None:#re.search(r"[^a-zA-Z0-9_]", pwd) is None: # Check if it contains at least 1 special character
        message = "Password must contain at least one special character (@, !, ?, *, &, $, #, etc.)"

    print("password: ", pwd)

    return message


@bp.route('/icon', methods=('GET', 'POST'))
@login_required
def change_user_icon():
    db = get_db()
    if request.method == 'POST':
        s3 = connect_to_s3()
        uploaded_image = request.files['file']
        upload_filesize = uploaded_image.seek(0, os.SEEK_END)
        uploaded_image  .seek(0, os.SEEK_SET)
        upload_filename = secure_filename(uploaded_image.filename)

        if upload_filesize > 2000000: #2000 kb limit for picture uploads
            flash('The uploaded file is too big. 2 mb upload limit, please try again.')
            return redirect(url_for('auth.change_user_icon'))
        
        if upload_filesize == 0:
            flash('The uploaded file is not valid. Please try again.')
            return redirect(url_for('auth.change_user_icon'))

        if upload_filename == '':
            flash('Invalid file name. Please try again.')
            return redirect(url_for('auth.change_user_icon'))

        if '.' not in upload_filename or upload_filename.rsplit('.', 1)[1].lower() not in ('png','jpg','jpeg'):
            flash('Incorrect file type. JPG, JPEG, and PNG files only, please try again.')
            return redirect(url_for('auth.change_user_icon'))
        
        upload_ext = upload_filename.rsplit('.', 1)[1].lower()

        timestamp = datetime.now().strftime("%d%m%Y%H%M%S%f")
        user_id = g.user["usr_id"]
        file_name = f'icon-{user_id}-{timestamp}.{upload_ext}'

        try:
            s3.meta.client.upload_fileobj(uploaded_image, 'engr-4450-fp', file_name)
            db.table("users").update({"prof_pic_s3_path": file_name}).eq('usr_id', g.user['usr_id']).execute()
        except Exception as e:
            print(e) 
            flash('We had a problem uploading your image. Please try again or contact support.')

        return redirect(url_for('auth.profile'))
    else:
        user_prof_data = db.table("users").select("*").eq('usr_id', g.user['usr_id']).execute().data[0]
        return render_template('auth/change-icon.html', user_profile_data=user_prof_data)
    
@bp.route('/myprofile')
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
    user_profile_data["usr_created_at"] = str(user_profile_data["usr_created_at"])[:10]

    #this query only grabs videos from the submissions table that have been liked by the current user
    liked_video_data = db.table("video_data").select('*, video_likes(user_id)').eq('video_likes.user_id', g.user["usr_id"]).not_.is_('video_likes', 'null').execute().data 

    return render_template('auth/myprofile.html', videos=vids, likes=liked_video_ids, comments=comment_dictionary, user_profile_data=user_profile_data, liked_vids=liked_video_data)