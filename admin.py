from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from email_utils import send_email
from models import Sticker, Order, Category, CustomSticker
from utils import admin_required
from werkzeug.utils import secure_filename
from flask_mail import Message
from utils import allowed_file, UPLOAD_FOLDER
from decimal import Decimal
from models import User
from extensions import db, mail
import cloudinary
import cloudinary.uploader
import os

admin = Blueprint('admin', __name__, static_folder="static", template_folder="templates")


@admin.route('/admin_orders')
@admin_required
def admin_orders():
    orders = Order.query.filter(Order.status != "cart").order_by(Order.created_at.desc()).all()
    return render_template('admin_orders.html', orders=orders)



@admin.route("/add_sticker", methods=["GET", "POST"])
@admin_required
def add_sticker():
    categories = Category.query.all()
    if request.method == "POST":
        name = request.form['name']
        price = request.form['price']
        category_name = request.form.get('category')
        category_obj = Category.query.filter_by(name=category_name).first()
        description = request.form.get('description')
        stock = request.form.get('stock', 0)

        existing = Sticker.query.filter_by(name=name).first()
        if existing:
            flash(f"A sticker with the name '{name}' already exists.", "error")
            return redirect(url_for('admin.add_sticker'))


        if not category_obj:
            flash("Category not found", "error")
            return redirect(url_for('admin.add_sticker'))

        file = request.files['image']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            if file:
                upload_result = cloudinary.uploader.upload(file)
                
                image_url = upload_result['secure_url']

                new_sticker = Sticker(
                    name=name,
                    price=Decimal(price),
                    category_id = category_obj.id,
                    description=description,
                    image_url=image_url,
                    stock=int(stock),
                    approval_status="pending"
                )

            db.session.add(new_sticker)
            db.session.commit()

            flash("Sticker added successfully!", "success")
            return redirect(url_for('admin.add_sticker'))
        else:
            flash("Please upload a valid image file.", "error")
    return render_template("add_sticker.html", categories=categories)

@admin.route('/approve_request/<int:request_id>', methods=['POST'])
@admin_required
def approve_request(request_id):
    custom_sticker = CustomSticker.query.get_or_404(request_id)
    user = custom_sticker.user

    custom_sticker.approval_status = 'approved'

    # activate linked sticker
    sticker = Sticker.query.get(custom_sticker.sticker_id)
    if sticker:
        sticker.is_custom = True

    db.session.commit()


    flash(f"Request '{custom_sticker.name}' approved.", "success")
    return redirect(url_for('admin.suggestions'))


@admin.route('/deny_request/<int:request_id>', methods=['POST'])
@admin_required
def deny_request(request_id):
    custom_sticker = CustomSticker.query.get_or_404(request_id)

    request_name = custom_sticker.name

    sticker = None
    if custom_sticker.sticker_id:
        sticker = Sticker.query.get(custom_sticker.sticker_id)

    db.session.delete(custom_sticker)
    db.session.commit()

        
    if sticker:
        if sticker.order_items:
            sticker.is_active = False
        else:
            db.session.delete(sticker)
        db.session.commit()

    flash(f"Request '{request_name}' denied.", "info")
    return redirect(url_for('admin.suggestions'))


@admin.route('/add_request_to_dashboard/<int:request_id>', methods=['POST'])
@admin_required
def add_request_to_dashboard(request_id):
    custom = CustomSticker.query.get_or_404(request_id)

    if custom.approval_status != "approved":
        flash("Request must be approved first", "error")
        return redirect(url_for('admin.suggestions'))

    # Check if sticker already exists
    existing_sticker = Sticker.query.filter_by(name=custom.name).first()
    if existing_sticker:
        custom.sticker_id = existing_sticker.id
        custom.approval_status = "added_to_shop"
        db.session.commit()
        flash(f"'{custom.name}' already exists in the shop, linked to request.", "info")
        return redirect(url_for('admin.index_admin'))

    # Upload image to cloud if not already uploaded
    if custom.image_url:  # If already has a cloud URL
        image_url = custom.image_url
    else:
        flash("Custom sticker image missing. Please upload it first.", "warning")
        image_url = None

    # Create the Sticker in DB
    sticker = Sticker(
        name=custom.name,
        price=Decimal("0.99"),
        stock=0,
        image_url=image_url,  # Use cloud URL
        description=custom.description,
        category_id=3,
        is_custom=True,
        is_active=True
    )

    db.session.add(sticker)
    db.session.flush()  # get sticker.id safely

    # Link custom sticker to newly created shop sticker
    custom.sticker_id = sticker.id
    custom.approval_status = "added_to_shop"
    db.session.commit()

    flash(f"'{custom.name}' added to shop (hidden)", "success")
    return redirect(url_for('admin.index_admin'))




@admin.route('/index_admin')
@admin_required
def index_admin():
    stickers = Sticker.query.filter(Sticker.is_active == True).all()
    return render_template('index_admin.html', stickers=stickers)

@admin.route('/suggestions')
@admin_required
def suggestions():
    suggestions = CustomSticker.query.order_by(CustomSticker.created_at.desc()).all()
    return render_template('suggestions.html', suggestions=suggestions)



@admin.route('/edit_sticker/<int:sticker_id>', methods=['GET', 'POST'])
@admin_required
def edit_sticker(sticker_id):
    sticker = Sticker.query.get_or_404(sticker_id)
    
    if request.method == 'POST':
        # Update text fields
        sticker.name = request.form.get('name')
        sticker.price = float(request.form.get('price'))
        sticker.stock = int(request.form.get('stock'))
        sticker.description = request.form.get('description')

        # Update Category
        category_name = request.form.get('category')
        category_obj = Category.query.filter_by(name=category_name).first()
        if category_obj:
            sticker.category_id = category_obj.id
        
        # Handle optional image update
        file = request.files.get('image')
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            upload_result = cloudinary.uploader.upload(file)
            sticker.image_url = upload_result['secure_url']

        db.session.commit()
        flash("Sticker updated successfully!", "success")
        return redirect(url_for('admin.index_admin'))

    categories = Category.query.all()
    return render_template('edit_sticker.html', sticker=sticker, categories=categories)


@admin.route("/order/<int:order_id>/status/<string:new_status>", methods=["POST"])
@admin_required
def update_order_status(order_id, new_status):
    order = Order.query.get_or_404(order_id)

    allowed_statuses = ["pending", "confirmed", "finished", "cancelled"]
    new_status = new_status.lower().strip()

    if new_status not in allowed_statuses:
        flash("Invalid status", "danger")
        return redirect(url_for("admin.admin_orders"))

    order.status = new_status
    db.session.commit()

    flash(f"Order #{order.id} marked as {new_status}", "success")
    return redirect(url_for("admin.admin_orders"))

@admin.route('/order/<int:order_id>/delete', methods=['POST'])
@admin_required
def delete_order(order_id):
    print("🔥 DELETE ROUTE HIT FOR ORDER:", order_id)

    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for('admin.admin_orders'))
