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
import shutil
import cloudinary
import cloudinary.uploader
import os

admin = Blueprint('admin', __name__, static_folder="static", template_folder="templates")


def send_order_status_email(user_email, order, status):
    status = status.lower().strip()
    subject = ''
    body = ''

    if order.payment:
        pickup_info = f"{order.payment.date} at {order.payment.time}"
    else:
        pickup_info = "the agreed pickup time"


    if status == 'cancelled':
        subject = f"Your Stickerdom order #{order.id} has been cancelled"
        body = f"Hello,\n\nWe’re sorry to inform you that your order #{order.id} has been cancelled.\nIf you have questions, contact us.\n\nThanks, Stickerdom Team"
    elif status == 'finished':
        subject = f"Your Stickerdom order #{order.id} is ready!"
        body = f"""
Hello,

Good news! Your order #{order.id} has been completed.

You can pick up your order at OIL 4.30 {pickup_info}.

Thank you for shopping with Stickerdom!

Best regards,
Stickerdom Team
"""
    elif status == 'confirmed':
        subject = f"Your Stickerdom order #{order.id} is confirmed!"
        body = f"""
Hello,

Your order #{order.id} has been confirmed successfully.

We are preparing your stickers for pickup.

Thank you for shopping with Stickerdom!

Best regards,
Stickerdom Team
"""
    else:
        print("DEBUG: status did not match, email not sent")
        return

    # msg = Message(subject=subject,
    #               recipients=[user_email],
    #               body=body)
    # send_email(msg)



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
                    image_path=image_url,
                    stock=int(stock)
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

#     msg = Message(
#         subject="Your custom sticker has been approved 🎉",
#         recipients=[custom_sticker.user.email],
#         body=f"""Hi {custom_sticker.user.username},

# Great news! 🎉

# Your {custom_sticker.name} sticker request has been approved and is now available.


# You can now add your sticker to your cart and place your order!


# If you gave permission for it to be shared, we will consider adding your sticker to our website for others to order and view.


# Thank you for choosing our sticker webshop — we truly appreciate your support!


# Best regards,
# The Stickerdom Team
# """
#     )

    # try:
    #     send_email(msg)
    # except Exception:
    #     flash("Sticker approved, but email could not be sent.", "warning")

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


#     msg = Message(
#         subject="Your Stickerdom Sticker Request Update",
#         recipients=[user.email],
#         body=f"""Hi {user.username},

# Thank you for your interest in Stickerdom and for submitting your sticker request.

# After careful review, we regret to inform you that your "{custom_sticker.name}" sticker request has been denied and will not be processed further.
# This decision may be due to content restrictions, copyright concerns, technical limitations, or not meeting our current guidelines.

# If you believe this decision was made in error or you would like more information, feel free to reply to this email, and our team will be happy to assist you.

# Thank you for your understanding and for your interest in our products.

# Best regards,
# The Stickerdom Team
# """
#     )

#     send_email(msg)



    flash(f"Request '{request_name}' denied.", "info")
    return redirect(url_for('admin.suggestions'))


@admin.route('/add_request_to_dashboard/<int:request_id>', methods=['POST'])
@admin_required
def add_request_to_dashboard(request_id):
    custom = CustomSticker.query.get_or_404(request_id)

    if custom.approval_status != "approved":
        flash("Request must be approved first", "error")
        return redirect(url_for('admin.suggestions'))

    existing_sticker = Sticker.query.filter_by(name=custom.name).first()
    if existing_sticker:
        custom.sticker_id = existing_sticker.id
        custom.approval_status = "added_to_shop"
        db.session.commit()
        flash(f"'{custom.name}' already exists in the shop, linked to request.", "info")
        return redirect(url_for('admin.index_admin'))
    
    src_path = os.path.join("static/images/custom", custom.image_path)
    dst_path = os.path.join(UPLOAD_FOLDER, custom.image_path)
    if os.path.exists(src_path):
        shutil.copy(src_path, dst_path)
    else:
        flash("Warning: Custom sticker image not found, placeholder will be used.", "warning")
    
    sticker = Sticker(
        name=custom.name,
        price=Decimal("0.99"),
        stock=0,
        image_path=custom.image_path,
        description=custom.description,
        category_id=3,
        is_custom=True,
        is_active=True
    )

    db.session.add(sticker)
    db.session.flush() # get sticker.id safely

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
            # Use the same UPLOAD_FOLDER from your add_sticker route
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            sticker.image_path = filename

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
    user = User.query.get(order.user_id)

    if user and user.email and new_status in ["finished", "cancelled", "confirmed"]:
        try:
            send_order_status_email(user.email, order, new_status)
        except Exception as e:
            flash("Order updated, but email could not be sent.", "warning")

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
