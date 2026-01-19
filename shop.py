from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
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
        return redirect(request.referrer or url_for('shop.index'))

    # 1. Get or Create the Order (Cart)
    order = Order.query.filter_by(user_id=user_id, status="cart").first()
    if not order:
        order = Order(user_id=user_id, created_at=datetime.utcnow(), status="cart", total_price=0)
        db.session.add(order)
        db.session.flush() # Flush ensures we get an ID for the order immediately

    # 2. Add Item or Increase Quantity
    item = OrderItem.query.filter_by(order_id=order.id, sticker_id=sticker.id).first()
    if item:
        item.quantity += 1
    else:
        item = OrderItem(
            quantity=1,
            price_at_time=Decimal(str(sticker.price)),
            sticker_id=sticker.id,
            order_id=order.id
        )
        db.session.add(item)

    # 3. Update Total Price and Save
    order.total_price += Decimal(str(sticker.price))
    db.session.commit()

    # 4. Calculate Total Quantity from Database (The Fix)
    # We loop through the items in the order we just updated to get the real count
    total_quantity = sum(item.quantity for item in order.order_items)

    # 5. Return JSON for the JavaScript Notification
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': 'Item added to shopping cart!',
            'total_quantity': total_quantity
        })

    # 6. Fallback for non-JS browsers
    return redirect(request.referrer or url_for('shop.index'))







@shop.route('/cart')
@login_required
def cart():
    order = Order.query.filter_by(user_id=session['user_id'], status="cart").first()
    if not order or not order.order_items:
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
    # Check if request is JSON (from JS) or Form Data (from HTML form)
    if request.is_json:
        data = request.get_json()
        action = data.get('action')
    else:
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

    # --- NEW: Return JSON for AJAX ---
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        # Calculate badge count
        total_qty = sum(i.quantity for i in order.order_items)
        
        return jsonify({
            'success': True,
            'new_quantity': item.quantity,
            'new_item_total': f"{item.price_at_time * item.quantity:.2f}",
            'new_cart_total': f"{order.total_price:.2f}",
            'total_cart_items': total_qty
        })

    return redirect(request.referrer or url_for('shop.cart'))



@shop.route('/')
def index():
    query = request.form.get('search', '')
    if query:
        results = Sticker.query.filter(Sticker.is_active == True, Sticker.name.ilike(f'%{query}%')).all()
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
    orders = Order.query.filter(
        Order.user_id == user_id,
        Order.status != "cart"
    ).order_by(Order.created_at.desc()).all()
    return render_template("user_order_history.html", orders=orders)


@shop.route('/add_custom_to_cart', methods=['POST'])
@login_required
def add_custom_to_cart():
    custom_id = request.form.get('sticker_id')
    user_id = session['user_id']

    if not custom_id:
        flash("No custom sticker selected!", "error")
        return redirect(url_for('shop.index'))

    custom = CustomSticker.query.get(custom_id)
    if not custom:
        flash("Custom sticker not found!", "error")
        return redirect(url_for('shop.index'))

    if custom.approval_status != "approved":
        flash("This custom sticker is not approved yet.", "error")
        return redirect(url_for('shop.index'))

    if not custom.sticker_id:
        sticker = Sticker(
            name=custom.name,
            price=0.99,
            category_id=4,
            description=custom.description,
            image_path=custom.image_path,
            stock=0,
            is_custom=True,
            user_id=custom.user_id,
            is_active=False
        )
        db.session.add(sticker)
        db.session.flush()

        custom.sticker_id = sticker.id
    else:
        sticker = Sticker.query.get(custom.sticker_id)

    order = Order.query.filter_by(user_id=user_id, status="cart").first()
    if not order:
        order = Order(user_id=user_id, status="cart", total_price=Decimal("0.00"))
        db.session.add(order)
        db.session.flush()

    item = OrderItem.query.filter_by(
        order_id=order.id,
        sticker_id=sticker.id
    ).first()

    if item:
        item.quantity += 1
    else:
        item = OrderItem(
            quantity=1,
            price_at_time=Decimal(str(sticker.price)),
            sticker_id=sticker.id,
            order_id=order.id
        )
        db.session.add(item)

    order.total_price += Decimal(str(sticker.price))
    db.session.commit()

    flash("Custom sticker added to cart!", "success")
    return redirect(request.referrer or url_for('shop.cart'))





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
@login_required
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
    return redirect(url_for('admin.index_admin'))

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
        description = request.form.get('description')

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
                description=description,
                approval_status="pending",
                request_approval=request_approval,
                created_at=datetime.utcnow()
            )
            db.session.add(new_request)
            db.session.commit()

            flash("Your sticker has beeen submitted for approval!", "success")
            return redirect(url_for('shop.my_requests'))
        else:
            flash("Invalid file type", "error")

    return render_template("add_sticker_user.html")
    
@shop.route('/contact')
def contact():
    return render_template('contact.html')
