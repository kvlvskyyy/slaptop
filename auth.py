from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import User
from extensions import db

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/login', methods=['GET' , 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['username'] = user.username
            session['user_id'] = user.id
            flash("Logged in successfully!", "success")
            return redirect(url_for('shop.index'))
        else:
            flash("Invalid email or password", "error")
            return render_template('login.html')
    elif request.method == 'GET':
        return render_template('login.html')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        passwordconfirm = request.form['passwordconfirm']
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()

        if password != passwordconfirm:
            flash("Passwords do not match", "error")
            return render_template('signup.html')

        elif existing_user:
            flash("Username or email already exists", "error")
            return render_template('signup.html')
        else:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = new_user.username
            session['user_id'] = new_user.id
            flash("Registration successful!", "success")
            return redirect(url_for('shop.index'))
    elif request.method == 'GET':
        return render_template('signup.html')
    
    
@auth.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for('shop.index'))