from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Sticker, Order, Category, CustomSticker
from utils import admin_required
from werkzeug.utils import secure_filename
from utils import allowed_file, UPLOAD_FOLDER
from decimal import Decimal
from extensions import db
import os

admin = Blueprint('admin', __name__, static_folder="static", template_folder="templates")

@admin.route('/admin_orders')
@admin_required
def admin_orders():
    orders = Order.query.all()
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
            file.save(os.path.join(UPLOAD_FOLDER, filename))

            new_sticker = Sticker(
                name=name,
                price=Decimal(price),
                category_id = category_obj.id,
                description = description,
                image_path = filename,
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
    custom_sticker.approval_status = 'approved'
    db.session.commit()
    flash(f"Request '{custom_sticker.name}' approved.", "success")
    return redirect(url_for('admin.suggestions'))

@admin.route('/deny_request/<int:request_id>', methods=['POST'])
@admin_required
def deny_request(request_id):
    custom_sticker = CustomSticker.query.get_or_404(request_id)
    custom_sticker.approval_status = 'denied'
    db.session.commit()
    flash(f"Request '{custom_sticker.name}' denied.", "info")
    return redirect(url_for('admin.suggestions'))

@admin.route('/add_request_to_dashboard/<int:request_id>', methods=['POST'])
@admin_required
def add_request_to_dashboard(request_id):
    custom = CustomSticker.query.get_or_404(request_id)
    
    # Create a new standard Sticker from the custom request
    new_sticker = Sticker(  
        name=custom.name,
        price=0.99,
        stock=0,
        image_path=custom.image_path, # Note: You may need to move the file from /custom/ to /stickers/
        description=f"Community suggested sticker by User {custom.user_id}",
        category_id=1, # Assign to a default category ID
        is_active=True
    )
    
    custom.approval_status = 'added_to_shop'
    db.session.add(new_sticker)
    db.session.commit()
    
    flash(f"'{custom.name}' has been added to the public shop!", "success")
    return redirect(url_for('admin.index_admin'))


@admin.route('/index_admin')
@admin_required
def index_admin():
    stickers = Sticker.query.filter(Sticker.is_active == True).all()
    return render_template('index_admin.html', stickers=stickers)

@admin.route('/suggestions')
@admin_required
def suggestions():
    suggestions = CustomSticker.query.filter_by(approval_status='pending').order_by(CustomSticker.created_at.desc()).all()
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