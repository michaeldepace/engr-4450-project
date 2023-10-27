from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
import functools
from lsapp.db import get_db

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