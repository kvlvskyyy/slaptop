from flask import Blueprint, redirect, url_for, flash, session, render_template, request
from utils import login_required
from models import Order, Payment, User
from datetime import datetime
from extensions import db
import stripe
import os


stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
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
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    payment_method = request.form.get('payment_method')
    order_id = request.args.get('order_id')

    payment = Payment(
        order_id=order_id,
        payment_method=payment_method,
        full_name=full_name,
        email=email,
        created_at=datetime.utcnow()
    )
    db.session.add(payment)

    order = Order.query.get(order_id)
    if order:
        order.status = "pending"
        db.session.commit()
        flash("Order placed successfully!", "success")
    else:
        flash("Order not found", "error")
        return redirect(url_for('shop.cart'))

    return redirect(url_for('shop.index'))
