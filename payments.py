from flask import Blueprint, redirect, url_for, flash, session, render_template, request
from flask_mail import Message
from utils import login_required
from models import Order, Payment, User
from datetime import datetime
from extensions import db, mail
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
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        payment_method = request.form.get('payment_method')
        order_id = request.args.get('order_id')

        # Create Payment record
        payment = Payment(
            order_id=order_id,
            payment_method=payment_method,
            full_name=full_name,
            email=email,
            created_at=datetime.utcnow()
        )
        db.session.add(payment)
        
        # Update order status to 'pending'
        order = Order.query.get(order_id)
        if order:
            order.status = "pending"
            db.session.commit()
            flash("Order placed successfully!", "success")
        else:
            flash("Order not found", "error")
            return redirect(url_for('shop.cart'))
        
        order = Order.query.get(order_id)

        # Generate a list of items as a string
        items_list = ""
        if order and order.order_items:
            for item in order.order_items:
                items_list += f"- {item.sticker.name} x{item.quantity} (€{item.price_at_time})\n"

        msg = Message(
            subject="Your Stickerdom Order Confirmation 🎉",
            recipients=[email],
            body=f"""Hi {full_name},

Thank you for your order at Stickerdom! 

Your order ID is: {order_id}

Purchased items:
{items_list}

Total price: €{order.total_price}

You can pick up your order from our pickup point at any time during opening hours.

If you have any questions, feel free to reply to this email — we’re happy to help!

Best regards,
The Stickerdom Team"""
        )

        try:
            mail.send(msg)
        except Exception:
            flash("Order placed, but confirmation email could not be sent.", "warning")

        return redirect(url_for('payments.checkout_success', order_id=order_id))

@payments.route('/checkout-success/<int:order_id>')
def checkout_success(order_id):
    order = Order.query.get(order_id)
    if not order:
        flash("Order not found.")
        return redirect(url_for('shop.index'))

    return render_template("checkout_success.html", order=order)
