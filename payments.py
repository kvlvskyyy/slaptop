from flask import Blueprint, redirect, url_for, flash, session, render_template, request
from utils import login_required
from constants import *
from models import Order, Payment
from extensions import db
import stripe
import os


payments = Blueprint("payments", __name__)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@payments.route('/payment_options')
@login_required
def payment_options():
    return render_template('payment_options.html')

@payments.route('/handle_payment_choice', methods=['POST'])
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
        return redirect(url_for('payments.create_checkout_session'))

    elif method == 'cash':
        flash("Cash payment selected. Pay on pickup.", "info")
        return redirect(url_for('payments.success'))

    elif method == 'tikkie':
        flash("Tikkie selected. We will contact you.", "info")
        return redirect(url_for('payments.success'))

    flash("Please choose a payment method.", "error")
    return redirect(url_for('payments.payment_options'))


@payments.route('/stripe_checkout_session', methods=['GET','POST'])
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
            success_url=url_for('payments.success', _external=True),
            cancel_url=url_for('payments.cancel', _external=True),
            locale='en'
        )

        return redirect(checkout_session.url, code=303)

    except Exception as e:
        return str(e)
    
@payments.route('/success')
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


@payments.route('/cancel')
@login_required
def cancel():
    flash("Payment canceled or returned to cart.", "info")
    return render_template('cancel.html')
