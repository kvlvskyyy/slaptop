from functools import wraps
from flask import session, flash, redirect, url_for
from models import User, Category
from extensions import db


UPLOAD_FOLDER = "static/images/stickers"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


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

def create_default_categories():
    default_categories = ["Fontys", "Memes", "Games", "Custom Stickers", "Other"]

    for name in default_categories:
        exists = Category.query.filter_by(name=name).first()
        if not exists:
            db.session.add(Category(name=name))

    db.session.commit()




