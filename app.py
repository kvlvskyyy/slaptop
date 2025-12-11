from functools import wraps
from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

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

#sticker model
class Sticker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    image_path = db.Column(db.String(255), nullable=False)
    is_custom = db.Column(db.Boolean, nullable=True)



def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            flash("Login is required", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        username = session.get('username')
        if not username:
            flash("Login is required", "error")
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()
        if not user or not user.is_admin:
            flash("You are not allowed to access this page", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrapper
    
@app.route('/')
def index():
    stickers = Sticker.query.all()
    return render_template('index.html', stickers=stickers)


UPLOAD_FOLDER = "static/images/stickers"   # folder for your stickers
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):
    ext = filename.split(".")[-1].lower()
    return ext in ALLOWED_EXTENSIONS

@app.route("/add_sticker", methods=["GET", "POST"])
@admin_required
def add_sticker():
    if request.method == "POST":
        name = request.form['name']
        price = request.form['price']
        category = request.form.get('category')
        description = request.form.get('description')

        file = request.files['image']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))

            new_sticker = Sticker(
                name=name,
                price=float(price),
                category = category,
                description = description,
                image_path = filename,
                is_custom = False
            )

            db.session.add(new_sticker)
            db.session.commit()

            return redirect(url_for('add_sticker'))
    







@app.route('/login', methods=['GET' , 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['username'] = user.username
            flash("Logged in successfully!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password", "error")
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
            flash("Registration successful!", "success")
            return redirect(url_for('index'))
    elif request.method == 'GET':
        return render_template('signup.html')
    
    
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('index'))
    
@app.route('/admin')
@admin_required
def admin():
    return render_template('admin.html')



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