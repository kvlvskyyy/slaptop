import os
from flask import Flask, session, request, redirect
from extensions import db, migrate, mail
from models import User, Order, Category
from dotenv import load_dotenv
from payments import payments
from admin import admin
from auth import auth
from shop import shop
from flask_babel import Babel, gettext as _

load_dotenv()

# This function tells Flask-Babel which language to use based on session
def get_locale():
    if 'language' in session:
        return session['language']
    return 'en'

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.getenv("FLASK_SECRET_KEY")

    db.init_app(app)
    migrate.init_app(app, db)
    
    # Babel configuration for translations
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['LANGUAGES'] = {'en': 'English', 'nl': 'Nederlands'}
    Babel(app, locale_selector=get_locale)

    # Flask-Mail Configuration
    app.config.update(
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USE_SSL=False,
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER=os.getenv("MAIL_USERNAME")
    )

    mail.init_app(app)

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
    
    # Route to change language - users click this to switch between English/Dutch
    @app.route('/set-language/<language>')
    def set_language(language):
        session['language'] = language
        return redirect(request.referrer or '/') 

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)