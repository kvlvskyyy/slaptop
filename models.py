from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import Decimal

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Sticker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    description = db.Column(db.String(255), nullable=True, unique=False)
    image_path = db.Column(db.String(255), nullable=False)
    stock = db.Column(db.Integer, nullable=True, default=0)
    is_active = db.Column(db.Boolean, default=True)

    order_items = db.relationship('OrderItem', backref='sticker', lazy=True)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    stickers = db.relationship("Sticker", backref="category", lazy=True)

class CustomSticker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), unique=False, nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    approval_status = db.Column(db.String(255), nullable=False)
    request_approval = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)

    user = db.relationship("User", backref="custom_stickers")


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=True)
    total_price = db.Column(db.Numeric(10, 2), default=Decimal("0.00"), nullable=True)
    status = db.Column(db.String(255), nullable=True)

    order_items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, unique=False, nullable=True)
    price_at_time = db.Column(db.Numeric(10, 2), nullable=True)
    sticker_id = db.Column(db.Integer, db.ForeignKey('sticker.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)

class CheckoutInfo(db.Model):
    __tablename__ = "checkout_info"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=True)

    order = db.relationship("Order", backref="checkout_info", uselist=False)

class Payment(db.Model):
    __tablename__ = "payment"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    payment_method = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(100), nullable=False)
    
    order = db.relationship("Order", backref="payment", uselist=False)

