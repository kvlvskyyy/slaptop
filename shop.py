from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import Sticker, Order, OrderItem, Category, CustomSticker
from utils import login_required
from werkzeug.utils import secure_filename
from extensions import db
from datetime import datetime
from decimal import Decimal
import os



shop = Blueprint('shop', __name__, static_folder="static", template_folder="templates")



@shop.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    sticker_id = request.form.get('sticker_id')
    user_id = session['user_id']

    sticker = Sticker.query.get(sticker_id)
    if not sticker:
        flash("Sticker not found.", "error")
        return redirect(request.referrer)

    # Get or create cart
    order = Order.query.filter_by(user_id=user_id, status="cart").first()
    if not order:
        order = Order(user_id=user_id, created_at=datetime.utcnow(), status="cart", total_price=0)
        db.session.add(order)
        db.session.flush() # flush gets order.id straight away without committing

    item = OrderItem.query.filter_by(order_id=order.id, sticker_id=sticker.id).first()
    if item:
        item.quantity += 1
    else:
        item = OrderItem(quantity=1, price_at_time=Decimal(str(sticker.price)), sticker_id=sticker.id, order_id=order.id)
        db.session.add(item)

    order.total_price += Decimal(str(sticker.price))

    db.session.commit()
    flash("Sticker added to cart!", "success")
    return redirect(request.referrer)


@shop.route('/add_custom_to_cart', methods=['POST'])
@login_required
def add_custom_to_cart():
    user_id = session['user_id']
    custom_id = request.form.get("sticker_id")

    custom = CustomSticker.query.get_or_404(custom_id)

    if custom.approval_status != "approved":
        flash("Sticker not available", "error")
        return redirect(url_for("shop.my_requests"))

    sticker = Sticker.query.get_or_404(custom.sticker_id)

    order = Order.query.filter_by(user_id=user_id, status="cart").first()
    if not order:
        order = Order(
            user_id=user_id,
            status="cart",
            created_at=datetime.utcnow(),
            total_price=Decimal("0.00")
        )
        db.session.add(order)
        db.session.commit()

    item = OrderItem.query.filter_by(
        order_id=order.id,
        sticker_id=sticker.id
    ).first()

    if item:
        item.quantity += 1
    else:
        item = OrderItem(
            order_id=order.id,
            sticker_id=sticker.id,
            quantity=1,
            price_at_time=sticker.price
        )
        db.session.add(item)

    order.total_price += Decimal(str(sticker.price))
    db.session.commit()

    flash("Sticker added to cart!", "success")
    return redirect(url_for("shop.cart"))



@shop.route('/cart')
@login_required
def cart():
    order = Order.query.filter_by(user_id=session['user_id'], status="cart").first()
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
        results = Sticker.query.filter_by(Sticker.is_active == True, Sticker.name.ilike(f'%{query}%')).all()
    else:
        results = Sticker.query.filter_by(is_active=True).all()

    return render_template('index.html', stickers=results, query=query)


UPLOAD_FOLDER = "static/images/stickers"   # folder for stickers
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):
    ext = filename.split(".")[-1].lower()
    return ext in ALLOWED_EXTENSIONS


@shop.route('/search', methods=["GET", "POST"])
def search():
    if request.method == "POST":
        query = request.form.get('search', '')
    else:
        query = ''

    search_results = Sticker.query.filter(
        Sticker.is_active == True,
        Sticker.name.ilike(f"%{query}%")
        ).all()
    return render_template("search_results.html", search_results=search_results, query=query)

@shop.route('/category/<category_name>', methods=["GET", "POST"])
def category(category_name):
    category = Category.query.filter_by(name=category_name).first_or_404()

    active_stickers = Sticker.query.filter_by(
        category_id=category.id,
        is_active=True
    ).all()

    return render_template(
        "category.html",
        category=category.name,
        category_results=active_stickers
    )

@shop.route("/user_order_history")
@login_required
def user_order_history():
    user_id = session["user_id"]
    orders = Order.query.filter_by(user_id=user_id).all()
    return render_template("user_order_history.html", orders=orders)


@shop.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@shop.route("/orders")
@login_required
def orders():
    user_id = session["user_id"]
    orders = Order.query.filter_by(user_id=user_id).all()
    return render_template("orders.html", orders=orders)

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

@shop.route("/add_sticker_user", methods=["GET", "POST"])
def add_sticker_user():
    return render_template("add_sticker_user.html")

@shop.route("/sticker/<int:sticker_id>")
def sticker_desc(sticker_id):
    sticker = Sticker.query.get_or_404(sticker_id)
    return render_template("sticker_desc.html", sticker=sticker)

@shop.route("/my_requests")
def my_requests():
    user_id = session['user_id']
    custom_stickers = CustomSticker.query.filter_by(user_id=session['user_id']).all()

    return render_template("my_requests.html", custom_stickers=custom_stickers)

@shop.route('/delete_sticker/<int:sticker_id>', methods=['POST'])
def delete_sticker(sticker_id):
    sticker = Sticker.query.get_or_404(sticker_id)
    sticker.is_active = False
    db.session.commit()
    return redirect(url_for('shop.index_admin'))

@shop.route('/payment_options')
@login_required
def payment_options():
    return render_template('payment_options.html')


@shop.route('/request_sticker', methods=["GET", "POST"])
@login_required
def request_sticker():
    if request.method == "POST":
        name = request.form.get('name')
        request_approval = True if request.form.get('request_approval') == 'yes' else False
        file = request.files.get('image')

        if not name or not file:
            flash("Please provide a name and an image", "error")
            return redirect(url_for('shop.add_sticker_user'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            upload_path = os.path.join(shop.static_folder, 'images', 'custom')
            file.save(os.path.join(upload_path, filename))

            new_request = CustomSticker(
                user_id=session['user_id'],
                name=name,
                image_path=filename,
                approval_status="pending",
                request_approval=request_approval,
                created_at=datetime.utcnow()
            )
            db.session.add(new_request)
            db.session.commit()

            new_sticker = Sticker(
                name=name,
                image_path=filename,
                price=Decimal("0.99"),
                is_active=False,
                category_id=3
            )
            db.session.add(new_sticker)
            db.session.flush()

            new_request.sticker_id = new_sticker.id

            db.session.commit()

            flash("Your sticker has beeen submitted for approval!", "success")
            return redirect(url_for('shop.index'))
        else:
            flash("Invalid file type", "error")

    return render_template("add_sticker_user.html")
