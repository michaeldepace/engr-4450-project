from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
import functools
from lsapp.db import get_db
from werkzeug.utils import secure_filename
from lsapp.s3 import connect_to_s3
from datetime import datetime
import os

bp = Blueprint('auth', __name__, url_prefix='/auth') #connect this script to the html template files and http url routes

#create a wrapper for route functions that require you to be logged in before accessing
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None: #if the user isn't logged in
            return redirect(url_for('auth.login')) #redirect them to the login page
        return view(**kwargs) #else ???
    return wrapped_view

#register a function that runs before every page request to make current user info accessible across application
@bp.before_app_request #maybe this just makes sure that the user info is available before each request/page load so it is seamlessly available at all times
def load_logged_in_user():
    user_id = session.get('user_id') #checks if user id is stored in current session

    if user_id is None: #if it isn't then there is no user logged in
        g.user = None
    else: #if there is a user id, then the user 
        
        #old code for getting user metadata
        # g.user = get_db().execute( #what is g.user?
        #     'SELECT * FROM user WHERE usr_id = ?', (user_id,)
        # ).fetchone()

        #this might need packaged into smthng simpler like a dictionary
        g.user = get_db().table("users").select("usr_id, usr_login, usr_created_at").eq("usr_id", user_id).execute().data[0]

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif db.table("users").select("*", count='exact').eq('usr_login', username).execute().count > 0:
            error = "This username is taken."

        if error is None:
            try:
                # db.execute(
                #     "INSERT INTO user (username, password) VALUES (?, ?)",
                #     (username, generate_password_hash(password)),
                # )
                # db.commit()

                db.table("users").insert({"usr_login": username, "usr_password": generate_password_hash(password)}).execute()
            except BaseException as e:
                error = "error " + e.message
            # except db.IntegrityError:
            #     error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))
        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        # user = db.execute(
        #     'SELECT * FROM user WHERE username = ?', (username,)
        # ).fetchone()

        user = None
        usr_data = db.table("users").select("*").eq("usr_login", username).execute().data
        if len(usr_data) > 0:
            user = db.table("users").select("*").eq("usr_login", username).execute().data[0]

        #print(user)

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


@bp.route('/logout') #method that clears the session data and redirects to the home page when the user logs out
def logout():
    session.clear()
    return redirect(url_for('index'))

@bp.route('/password', methods=('GET', 'POST'))
@login_required
def change_password():
    if request.method == 'POST':
        #accept input
        #validate and flash on error
            #check passwords match
            #maybe enforce password rules (do on this and original set password registration method)
            #maybe make sure you can't reenter your old password
        #hash and update table

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

        if error is None:
            try:
                db.table("users").update({"usr_password": generate_password_hash(password)}).eq('usr_id', g.user['usr_id']).execute()
            except BaseException as e:
                error = "error " + e.message
            else:
                return redirect(url_for("live.profile"))
        flash(error)

        return redirect(url_for('auth.change_password'))
    else:
        return render_template('auth/change-pswd.html')
    
@bp.route('/icon', methods=('GET', 'POST'))
@login_required
def change_user_icon():
    if request.method == 'POST':
        db = get_db()
        s3 = connect_to_s3()
        uploaded_image = request.files['file']
        upload_filesize = uploaded_image.seek(0, os.SEEK_END)
        upload_filename = secure_filename(uploaded_image.filename)

        if upload_filesize > 1000000: #1000 kb limit for picture uploads
            flash('The uploaded file is too big. 1 mb upload limit, please try again.')
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

        # print('-----------------------upload file size', uploaded_image.seek(0, os.SEEK_END))

        try:
            s3.meta.client.upload_fileobj(uploaded_image, 'engr-4450-fp', file_name)
            db.table("users").update({"prof_pic_s3_path": file_name}).eq('usr_id', g.user['usr_id']).execute()
        except Exception as e:
            print(e) 
            flash('We had a problem uploading your image. Please try again or contact support.')

        return redirect(url_for('live.profile'))
    else:
        return render_template('auth/change-icon.html', user_profile_data={})