from functools import wraps
from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from dotenv import load_dotenv
import stripe

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")


#sqlalchemy setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)




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

class Sticker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    image_path = db.Column(db.String(255), nullable=False)
    is_custom = db.Column(db.Boolean, nullable=True)#not neeeded
    order_items = db.relationship('OrderItem', backref='sticker', lazy=True)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    stickers = db.relationship("Sticker", backref="category", lazy=True)

class CustomSticker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), unique=False, nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    approval_status = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime)

    user = db.relationship("User", backref="custom_stickers")


#order model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=True)
    total_price = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(255), nullable=True)

    billing_address = db.relationship('BillingAddress', backref='order', uselist=False)
    payment = db.relationship('Payment', backref='order', uselist=False)
    order_items = db.relationship('OrderItem', backref='order', lazy=True)

#orderitem model
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, unique=False, nullable=True)
    price_at_time = db.Column(db.Float, nullable=True)
    sticker_id = db.Column(db.Integer, db.ForeignKey('sticker.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)

class BillingAddress(db.Model):
    __tablename__ = "billing_address"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    address_line_1 = db.Column(db.String(255), nullable=False)
    address_line_2 = db.Column(db.String(255), nullable=True)

class Payment(db.Model):
    __tablename__ = "payment"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    payment_method = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(100), nullable=False)


@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return dict(user=user)

@app.context_processor
def inject_categories():
    categories = Category.query.order_by(Category.name).all()
    return dict(categories=categories)


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

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    sticker_id = request.form.get('sticker_id')
    user_id = session['user_id']
    order = Order.query.filter_by(user_id=user_id, status='cart').first()
    if not order:
        order = Order(
            user_id=user_id,
            created_at=datetime.utcnow(),
            status='cart',
            total_price=0
        )
        db.session.add(order)
        db.session.commit()
    item = OrderItem.query.filter_by(order_id=order.id, sticker_id=sticker_id).first()
    if item:
        item.quantity += 1
    else:
        sticker = Sticker.query.get(sticker_id)
        item = OrderItem(
            quantity=1,
            price_at_time=sticker.price,
            sticker_id=sticker.id,
            order_id=order.id
        )
        db.session.add(item)
    order.total_price += item.price_at_time
    db.session.commit()
    flash("Sticker successfully added to cart!", "success")
    return redirect(request.referrer)

@app.route('/cart')
@login_required
def cart():
    order = Order.query.filter_by(user_id=session['user_id'], status="cart").first()
    if not order or not order.order_items:
        flash("Your cart is empty", "info")
        return render_template('cart.html', items=[], total=0)
    return render_template('cart.html', items=order.order_items, total=order.total_price)

@app.route('/remove_from_cart/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    item = OrderItem.query.get_or_404(item_id)
    order = item.order
    order.total_price -= item.price_at_time * item.quantity
    db.session.delete(item)
    db.session.commit()
    return redirect(request.referrer or url_for('cart'))

@app.route('/update_quantity/<int:item_id>', methods=['POST'])
@login_required
def update_quantity(item_id):
    action = request.form.get("action")

    item = OrderItem.query.get_or_404(item_id)
    order = item.order

    if action == "increase":
        item.quantity += 1
        order.total_price += item.price_at_time

    elif action == "decrease" and item.quantity > 1:
        item.quantity -= 1
        order.total_price -= item.price_at_time

    db.session.commit()
    return redirect(request.referrer or url_for('cart'))



@app.route('/')
def index():
    query = request.form.get('search', '')
    if query:
        results = Sticker.query.filter(Sticker.name.ilike(f"%{query}%")).all()
    else:
        results = Sticker.query.all()  # show all by default
    return render_template('index.html', stickers=results, query=query)


UPLOAD_FOLDER = "static/images/stickers"   # folder for your stickers
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):
    ext = filename.split(".")[-1].lower()
    return ext in ALLOWED_EXTENSIONS

@app.route("/add_sticker", methods=["GET", "POST"])
@admin_required
def add_sticker():
    categories = Category.query.all()
    if request.method == "POST":
        name = request.form['name']
        price = request.form['price']
        category_name = request.form.get('category')
        category_obj = Category.query.filter_by(name=category_name).first()
        description = request.form.get('description')

        if not category_obj:
            flash("Category not found", "error")
            return redirect(url_for('add_sticker'))

        file = request.files['image']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))

            new_sticker = Sticker(
                name=name,
                price=float(price),
                category_id = category_obj.id,
                description = description,
                image_path = filename,
                is_custom = False
            )

            db.session.add(new_sticker)
            db.session.commit()

            flash("Sticker added successfully!", "success")
            return redirect(url_for('add_sticker'))
        else:
            flash("Please upload a valid image file.", "error")
    return render_template("add_sticker.html", categories=categories)


@app.route('/login', methods=['GET' , 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['username'] = user.username
            session['user_id'] = user.id
            flash("Logged in successfully!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password", "error")
            return render_template('login.html')
    elif request.method == 'GET':
        return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
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
            return redirect(url_for('index'))
    elif request.method == 'GET':
        return render_template('signup.html')
    
    
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for('index'))

@app.route('/search', methods=["GET", "POST"])
def search():
    if request.method == "POST":
        query = request.form.get('search', '')
    else:
        query = ''

    search_results = Sticker.query.filter(Sticker.name.ilike(f"%{query}%")).all()
    return render_template("search_results.html", search_results=search_results, query=query)

@app.route('/category/<category_name>', methods=["GET", "POST"])
def category(category_name):
    category = Category.query.filter_by(name=category_name).first_or_404()

    return render_template(
        "category.html",
        category=category.name,
        category_results=category.stickers
    )

    
@app.route('/admin')
@admin_required
def admin():
    return render_template('admin.html')

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route("/checkout")
@login_required
def checkout():
    order = Order.query.filter_by(user_id=session['user_id'], status='cart').first()
    if order.order_items:
        items = order.order_items
        total_quantity = 0
        for item in items:
            total_quantity+=item.quantity
    else:
        flash("Your cart is empty", "info")
        return redirect(url_for('index'))

    return render_template("checkout.html", items=items, total_quantity=total_quantity)

@app.route("/orders")
def orders():
    return render_template("orders.html")

@app.route("/wishlist")
def wishlist():
    return render_template("wishlist.html")

@app.route("/termsconditions")
def termsconditions():
    return render_template("termsconditions.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/returnrefund")
def returnrefund():
    return render_template("returnrefund.html")

@app.route("/shippinginfo")
def shippinginfo():
    return render_template("shippinginfo.html")

@app.route("/add_sticker_user")
def add_sticker_user():
    return render_template("add_sticker_user.html")

@app.route("/sticker_desc")
def sticker_desc():
    return render_template("sticker_desc.html")

@app.route('/create-checkout-session', methods=['GET','POST'])
@login_required
def create_checkout_session():
    order = Order.query.filter_by(user_id=session['user_id'], status='cart').first()
    if not order or not order.order_items:
        flash("Your cart is empty", "info")
        return redirect(url_for('cart'))

    try:
        line_items = []
        for item in order.order_items:
            line_items.append({
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': item.sticker.name,
                        'description': item.sticker.description,
                    },
                    'unit_amount': int(item.price_at_time * 100),
                },
                'quantity': item.quantity,
            })

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=url_for('success', _external=True),
            cancel_url=url_for('cancel', _external=True),
            locale='en'
        )

        return redirect(checkout_session.url, code=303)

    except Exception as e:
        return str(e)
    
@app.route('/success')
def success():
    order = Order.query.filter_by(user_id=session['user_id'], status='cart').first()
    if order:
        order.status = 'paid'
        db.session.commit()
        flash("Payment successful! Your order is confirmed.", "success")
    return render_template('success.html')

@app.route('/cancel')
@login_required
def cancel():
    # Optionally, you can flash a message
    flash("Payment canceled or returned to cart.", "info")
    return render_template('cancel.html')




if __name__ == "__main__":
    app.run(debug=True)