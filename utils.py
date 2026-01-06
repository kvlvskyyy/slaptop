from functools import wraps
from flask import session, flash, redirect, url_for
from models import User

UPLOAD_FOLDER = "static/images/stickers"   # folder for stickers
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def register_context_processors(app):
    @app.context_processor
    def inject_user():
        user = None
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
        return dict(user=user)


def allowed_file(filename):
    ext = filename.split(".")[-1].lower()
    return ext in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            flash("Login is required", "error")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        username = session.get('username')
        if not username:
            flash("Login is required", "error")
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(username=username).first()
        if not user or not user.is_admin:
            flash("You are not allowed to access this page", "error")
            return redirect(url_for('shop.index'))
        return f(*args, **kwargs)
    return wrapper
    