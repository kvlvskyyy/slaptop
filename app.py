from functools import wraps
from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'

#sqlalchemy setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#database model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
# class Sticker(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), unique=True, nullable=False)
#     price = db.Column(db.Float, nullable=False)
#     image = db.Column(db.String(255), nullable=False)
    
@app.route('/')
def index():
    # stickers = Sticker.query.all() <-- query the stickers from the database
    stickers = [
        {"name": "FeedPulse Warrior", "price": 0.99, "image": "images/feedpulse_warrior.jpg"},
        {"name": "Sinter Klaas", "price": 0.99, "image": "images/sinterklaas.jpg"},
        {"name": "Get more Feedback", "price": 0.99, "image": "images/get_more_feedback.png"},
        {"name": "Working on documentation", "price": 0.99, "image": "images/working_on_documentation.jpg"},
    ]
    return render_template('index.html', stickers=stickers)

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            flash("Login required")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

@app.route('/login', methods=['GET' , 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['username'] = user.username
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password")
            return render_template('login.html')
    elif request.method == 'GET':
        return render_template('login.html')

@app.route('/signup', methods=['GET' , 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        passwordconfirm = request.form['passwordconfirm']
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()

        if password != passwordconfirm:
            flash("Passwords do not match")
            return render_template('signup.html')

        elif existing_user:
            flash("Username or email already exists")
            return render_template('signup.html')
        else:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = new_user.username
            return redirect(url_for('index'))
    elif request.method == 'GET':
        return render_template('signup.html')
    
    
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))
    
@app.route('/admin')
@login_required
def admin():
    id = User.query.filter_by(username=session['username']).first().id
    if id == 1:
        return render_template('admin.html')
    else:
        return redirect(url_for('index'))


@app.route("/cart")
def cart():
    return render_template("cart.html")

@app.route("/orders")
def orders():
    return render_template("orders.html")

@app.route("/wishlist")
def wishlist():
    return render_template("wishlist.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)