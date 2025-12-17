import os
from flask import Flask
from extensions import db, migrate
from dotenv import load_dotenv
from auth import auth
from shop import shop
import stripe

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.getenv("FLASK_SECRET_KEY")
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(auth)
    app.register_blueprint(shop)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)