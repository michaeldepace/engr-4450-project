from flask import (Blueprint, flash, g, redirect, render_template, request, url_for)
from werkzeug.exceptions import abort
from lsapp.auth import login_required
from lsapp.db import get_db

bp = Blueprint('live', __name__)

@bp.route('/')
@login_required
def index():
    db = get_db()
    # url_query = request.args.to_dict()
    return render_template('live/index.html', products="test")

@bp.route('/live/broadcast')
@login_required
def broadcast():
    #print(g.user.data)
    return render_template('live/broadcast.html')