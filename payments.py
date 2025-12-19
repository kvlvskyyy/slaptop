from flask import Blueprint, redirect, url_for, flash, session, render_template, request
from utils import login_required
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
    ).first()

    if not order:
        flash("No active order found.", "error")
        return redirect(url_for('shop.cart'))

    # Remove old payment if exists
    if order.payment:
        db.session.delete(order.payment)
        db.session.commit()

    payment = Payment(
        order_id=order.id,
        payment_method=method,
        status="pending"
    )
    db.session.add(payment)

    if method == "stripe":
        order.status = "pending"
        db.session.commit()
        return redirect(url_for('payments.create_checkout_session'))

    elif method == "cash":
        order.status = "unpaid"
        db.session.commit()
        flash("Cash payment selected. Pay on delivery or pickup.", "info")
        return redirect(url_for('payments.success_cash'))

    elif method == "tikkie":
        order.status = "unpaid"
        db.session.commit()
        flash("Tikkie selected. We will contact you shortly.", "info")
        return redirect(url_for('payments.success_tikkie'))

    flash("Please choose a payment method.", "error")
    return redirect(url_for('payments.payment_options'))


@payments.route('/stripe_checkout_session', methods=['GET','POST'])
@login_required
def create_checkout_session():
    order = Order.query.filter_by(user_id=session['user_id'], status="cart").first()
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
            success_url=url_for('payments.success_stripe', _external=True),
            cancel_url=url_for('payments.cancel', _external=True),
            locale='en'
        )

        return redirect(checkout_session.url, code=303)

    except Exception as e:
        return str(e)
    
@payments.route('/success_stripe')
@login_required
def success_stripe():
    order = Order.query.filter_by(
        user_id=session['user_id'],
        status="cart"
    ).first()

    if order:
        order.status = "paid"

        if order.payment:
            order.payment.status = "paid"

        db.session.commit()
        flash("Payment successful! Your order is confirmed.", "success")

    return render_template('success_stripe.html')

@payments.route('/success_cash')
def success_cash():
    order = Order.query.filter_by(user_id=session['user_id'], status="cart").first()

    if order:
        order.status = "cash unpaid"

        if order.payment:
            order.payment.status = "cash unpaid"

        db.session.commit()

        flash("Payment successful! Your order is confirmed.", "success")

    return render_template('success_cash.html')

@payments.route('/success_tikkie')
def success_tikkie():
    order = Order.query.filter_by(user_id=session['user_id'], status="cart").first()

    if order:
        order.status = "tikkie unpaid"

        if order.payment:
            order.payment.status = "tikkie unpaid"

        db.session.commit()

        flash("Payment successful! Your order is confirmed.", "success")

    return render_template('success_tikkie.html')


@payments.route('/cancel')
@login_required
def cancel():
    flash("Payment canceled or returned to cart.", "info")
    return render_template('cancel.html')