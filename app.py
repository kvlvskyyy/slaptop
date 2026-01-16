import os
from flask import Flask, session, request, redirect
from seed_stickers import generate_stickers, clear_stickers
from utils import create_default_categories
from flask_babel import Babel, gettext as _
from extensions import db, migrate, mail
from models import User, Order, Category
from dotenv import load_dotenv
from payments_blueprint import payments
from admin import admin
from auth import auth
from shop import shop
from flask import send_from_directory, render_template
import socket


load_dotenv()

def is_smtp_reachable(host, port):
    try:
        with socket.create_connection((host, port), timeout=5):
            return True
    except Exception:
        return False
    

# This function tells Flask-Babel which language to use based on session
def get_locale():
    if 'language' in session:
        return session['language']
    return 'en'

def create_app():
    app = Flask(__name__)

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        database_url = "sqlite:///app.db"

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.getenv("FLASK_SECRET_KEY")

    db.init_app(app)
    migrate.init_app(app, db)
    
    # Babel configuration for translations
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['LANGUAGES'] = {'en': 'English', 'nl': 'Nederlands'}
    Babel(app, locale_selector=get_locale)

    # Flask-Mail Configuration
    if is_smtp_reachable('smtp.gmail.com', 587):
    # SMTP reachable – use real Gmail SMTP
        app.config.update(
            MAIL_SERVER='smtp.gmail.com',
            MAIL_PORT=587,
            MAIL_USE_TLS=True,
            MAIL_USE_SSL=False,
            MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
            MAIL_DEFAULT_SENDER=os.getenv("MAIL_USERNAME"),
            MAIL_TIMEOUT=10
        )
        print("✅ SMTP reachable: Using Gmail SMTP")
    else:
        app.config.update(
            MAIL_SERVER='localhost',
            MAIL_PORT=8025,
            MAIL_USE_TLS=False,
            MAIL_USE_SSL=False,
            MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
            MAIL_DEFAULT_SENDER=os.getenv("MAIL_USERNAME"),
        )
        print("⚠️ SMTP unreachable: Using debug email server (console only)")

    mail.init_app(app)

    app.register_blueprint(auth)
    app.register_blueprint(shop)
    app.register_blueprint(payments)
    app.register_blueprint(admin)


    

    # 1. Route for the Service Worker (Must be at root scope)
    @app.route('/service-worker.js')
    def service_worker():
        return send_from_directory('static', 'service-worker.js')

    # 2. Route for the Offline Page
    @app.route('/offline')
    def offline():
        return render_template('offline.html') # Ensure offline.html is in your templates folder
    
    @app.route('/manifest.json')
    def manifest():
        return send_from_directory('static', 'manifest.json')


    # This runs for EVERY template in the app (Shop, Admin, Auth, etc.)
    @app.context_processor
    def inject_global_context():
        # 1. User
        user = None
        if 'user_id' in session:
            user = User.query.get(session['user_id'])

        # 2. Categories (for the Navbar dropdown)
        categories = Category.query.all()

        # 3. Cart Count (for the Navbar badge)
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

    # Route to change language - users click this to switch between English/Dutch
    @app.route('/set-language/<language>')
    def set_language(language):
        session['language'] = language
        return redirect(request.referrer or '/') 


    with app.app_context():

        # user = User.query.filter_by(username="Admin").first()
    
        # if user:
        #     user.is_admin = True
        #     db.session.commit()
        #     print("User 'Admin' is now an admin!")
        # else:
        #     print("User 'Admin' not found.")

        db.create_all()
        try:
            # upgrade()

            if not Category.query.first():
                create_default_categories()

        except Exception as e:
            print("DB init error:", e)
        
        # clear_stickers()
        generate_stickers()


    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
