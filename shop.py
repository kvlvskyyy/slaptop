from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import Sticker, Order, OrderItem, Category
from utils import login_required, admin_required
from werkzeug.utils import secure_filename
from extensions import db
from models import User
from constants import *
from datetime import datetime
import os



shop = Blueprint('shop', __name__, static_folder="static", template_folder="templates")


@shop.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return dict(user=user)

@shop.context_processor
def inject_categories():
    categories = Category.query.order_by(Category.name).all()
    return dict(categories=categories)



@shop.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    sticker_id = request.form.get('sticker_id')
    user_id = session['user_id']
    order = Order.query.filter_by(user_id=user_id, status=ORDER_CART).first()
    if not order:
        order = Order(
            user_id=user_id,
            created_at=datetime.utcnow(),
            status=ORDER_CART,
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

@shop.route('/cart')
@login_required
def cart():
    order = Order.query.filter_by(user_id=session['user_id'], status=ORDER_CART).first()
    if not order or not order.order_items:
        flash("Your cart is empty", "info")
        return render_template('cart.html', items=[], total=0)
    return render_template('cart.html', items=order.order_items, total=order.total_price)

@shop.route('/remove_from_cart/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    item = OrderItem.query.get_or_404(item_id)
    order = item.order
    order.total_price -= item.price_at_time * item.quantity
    db.session.delete(item)
    db.session.commit()
    return redirect(request.referrer or url_for('shop.cart'))

@shop.route('/update_quantity/<int:item_id>', methods=['POST'])
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
    return redirect(request.referrer or url_for('shop.cart'))



@shop.route('/')
def index():
    query = request.form.get('search', '')
    if query:
        results = Sticker.query.filter(Sticker.name.ilike(f"%{query}%")).all()
    else:
        results = Sticker.query.all()  # show all by default
    return render_template('index.html', stickers=results, query=query)


UPLOAD_FOLDER = "static/images/stickers"   # folder for stickers
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):
    ext = filename.split(".")[-1].lower()
    return ext in ALLOWED_EXTENSIONS

@shop.route("/add_sticker", methods=["GET", "POST"])
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
            return redirect(url_for('shop.add_sticker'))

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
            return redirect(url_for('shop.add_sticker'))
        else:
            flash("Please upload a valid image file.", "error")
    return render_template("add_sticker.html", categories=categories)

@shop.route('/search', methods=["GET", "POST"])
def search():
    if request.method == "POST":
        query = request.form.get('search', '')
    else:
        query = ''

    search_results = Sticker.query.filter(Sticker.name.ilike(f"%{query}%")).all()
    return render_template("search_results.html", search_results=search_results, query=query)

@shop.route('/category/<category_name>', methods=["GET", "POST"])
def category(category_name):
    category = Category.query.filter_by(name=category_name).first_or_404()

    return render_template(
        "category.html",
        category=category.name,
        category_results=category.stickers
    )

    
@shop.route('/admin')
@admin_required
def admin():
    orders = Order.query.all()
    return render_template('admin.html', orders=orders)

@shop.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@shop.route("/checkout")
@login_required
def checkout():
    order = Order.query.filter_by(user_id=session['user_id'], status=ORDER_CART).first()
    if order.order_items:
        items = order.order_items
        total_quantity = 0
        for item in items:
            total_quantity+=item.quantity
    else:
        flash("Your cart is empty", "info")
        return redirect(url_for('shop.index'))

    return render_template("checkout.html", items=items, total_quantity=total_quantity)

@shop.route("/orders")
def orders():
    return render_template("orders.html")

@shop.route("/wishlist")
def wishlist():
    return render_template("wishlist.html")

@shop.route("/termsconditions")
def termsconditions():
    return render_template("termsconditions.html")

@shop.route("/privacy")
def privacy():
    return render_template("privacy.html")

@shop.route("/returnrefund")
def returnrefund():
    return render_template("returnrefund.html")

@shop.route("/shippinginfo")
def shippinginfo():
    return render_template("shippinginfo.html")

@shop.route("/add_sticker_user")
def add_sticker_user():
    return render_template("add_sticker_user.html")

@shop.route("/sticker_desc")
def sticker_desc():
    return render_template("sticker_desc.html")

# Example logic for your shop.py
@shop.route('/index_admin')
def index_admin():
    # Fetches the 4 rows seen in your database screenshot
    stickers = Sticker.query.all() 
    return render_template('index_admin.html', stickers=stickers)

@shop.route('/edit_sticker/<int:sticker_id>')
def edit_sticker(sticker_id):
    # This endpoint MUST exist to fix the BuildError
    sticker = Sticker.query.get_or_404(sticker_id)
    return render_template('edit_sticker.html', sticker=sticker)

@shop.route('/delete_sticker/<int:sticker_id>', methods=['POST'])
def delete_sticker(sticker_id):
    sticker = Sticker.query.get_or_404(sticker_id)
    db.session.delete(sticker)
    db.session.commit()
    return redirect(url_for('shop.index_admin'))

@shop.route('/payment_options')
@login_required
def payment_options():
    return render_template('payment_options.html')

@shop.route('/handle-payment-choice', methods=['POST'])
@login_required
def handle_payment_choice():
    method = request.form.get('payment_method')

    order = Order.query.filter_by(
        user_id=session['user_id'],
        status=ORDER_CART
    ).first()

    if not order:
        flash("No active order found.", "error")
        return redirect(url_for('shop.cart'))

    if order.payment:
        db.session.delete(order.payment)
        db.session.commit()

    payment = Payment(
        order_id=order.id,
        payment_method=method,
        status=PAYMENT_PENDING
    )
    db.session.add(payment)
    db.session.commit()

    if method == 'stripe':
        return redirect(url_for('shop.create_checkout_session'))

    elif method == 'cash':
        flash("Cash payment selected. Pay on pickup.", "info")
        return redirect(url_for('shop.success'))

    elif method == 'tikkie':
        flash("Tikkie selected. We will contact you.", "info")
        return redirect(url_for('shop.success'))

    flash("Please choose a payment method.", "error")
    return redirect(url_for('shop.payment_options'))


@shop.route('/create-checkout-session', methods=['GET','POST'])
@login_required
def create_checkout_session():
    order = Order.query.filter_by(user_id=session['user_id'], status=ORDER_CART).first()
    if not order or not order.order_items:
        flash("Your cart is empty", "info")
        return redirect(url_for('shop.cart'))

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
            success_url=url_for('shop.success', _external=True),
            cancel_url=url_for('shop.cancel', _external=True),
            locale='en'
        )

        return redirect(checkout_session.url, code=303)

    except Exception as e:
        return str(e)
    
@shop.route('/success')
@login_required
def success():
    order = Order.query.filter_by(
        user_id=session['user_id'],
        status=ORDER_CART
    ).first()

    if order:
        order.status = ORDER_PAID

        if order.payment:
            order.payment.status = ORDER_PAID

        db.session.commit()
        flash("Payment successful! Your order is confirmed.", "success")

    return render_template('success.html')


@shop.route('/cancel')
@login_required
def cancel():
    flash("Payment canceled or returned to cart.", "info")
    return render_template('cancel.html')
