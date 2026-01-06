import os
from flask import Flask, session
from extensions import db, migrate
from dotenv import load_dotenv
from auth import auth
from shop import shop
from payments import payments
# Add these imports so we can access the database in the main app
from models import User, Order, Category
from admin import admin 

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.getenv("FLASK_SECRET_KEY")

    db.init_app(app)
    migrate.init_app(app, db)

    # --- GLOBAL CONTEXT PROCESSOR ---
    # This runs for EVERY template in the app (Shop, Admin, Auth, etc.)
    @app.context_processor
    def inject_global_context():
        # 1. Inject User
        user = None
        if 'user_id' in session:
            user = User.query.get(session['user_id'])

        # 2. Inject Categories (for the Navbar dropdown)
        categories = Category.query.order_by(Category.name).all()

        # 3. Inject Cart Count (for the Navbar badge)
        cart_item_count = 0
        if 'user_id' in session:
            order = Order.query.filter_by(user_id=session['user_id'], status="cart").first()
            if order and order.order_items:
                cart_item_count = sum(item.quantity for item in order.order_items)

        return dict(
            user=user, 
            categories=categories, 
            cart_item_count=cart_item_count
        )

    app.register_blueprint(auth)
    app.register_blueprint(shop)
    app.register_blueprint(payments)
    app.register_blueprint(admin)
    # If you have an admin blueprint, register it here too
    # app.register_blueprint(admin) 

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)