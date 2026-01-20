from flask import Blueprint, abort, current_app, redirect, url_for, flash, session, render_template, request
from flask_mail import Message
import pytz
from utils import login_required
from models import Order, Payment, User
from datetime import datetime
from extensions import db
from email_utils import send_email


# stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
payments = Blueprint("payments", __name__)


@payments.route('/checkout')
@login_required
def checkout():
    user_id = session["user_id"]
    order = Order.query.filter_by(user_id=session['user_id'], status="cart").first()

    if not order:
        flash("Your cart is empty")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    return render_template(
        "checkout.html",
        email=user.email,
        order=order
    )



@payments.route('/process_checkout', methods=['POST'])
@login_required
def process_checkout():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        date = request.form.get('date')
        time = request.form.get('time')
        payment_method = request.form.get('payment_method')
        order_id = request.form.get('order_id')

        if not order_id:
            abort(400)
        
        order_id = int(order_id)
        order = Order.query.get_or_404(order_id)

        for item in order.order_items:
            sticker = item.sticker
            if sticker.stock < item.quantity:
                flash(
                    f"Not enough stock for {sticker.name}. Available: {sticker.stock}",
                    "error"
                )
                return redirect(url_for('shop.cart'))
        try:
            # Create Payment record
            payment = Payment(
                order_id=order_id,
                payment_method=payment_method,
                full_name=full_name,
                email=email,
                date=date,
                time=time,
                created_at=datetime.now(pytz.timezone('Europe/Amsterdam'))
            )
            db.session.add(payment)

            order.status = "pending"

            # Reduce stock
            for item in order.order_items:
                item.sticker.stock -= item.quantity

            db.session.commit()

            flash("Order placed successfully!", "success")
            return redirect(url_for('payments.checkout_success', order_id=order_id))
        
        except Exception as e:
            db.session.rollback()
            flash("Something went wrong during checkout.", "error")
            return redirect(url_for('shop.cart'))

@payments.route('/checkout-success/<int:order_id>')
def checkout_success(order_id):
    order = Order.query.get_or_404(order_id)
    if not order:
        flash("Order not found.")
        return redirect(url_for('shop.index'))

    return render_template("checkout_success.html", order=order)
