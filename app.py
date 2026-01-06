import os
from flask import Flask
from extensions import db, migrate
from dotenv import load_dotenv
from auth import auth
from shop import shop
from payments import payments
from admin import admin
from utils import register_context_processors

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.getenv("FLASK_SECRET_KEY")


    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(auth)
    app.register_blueprint(shop)
    app.register_blueprint(payments)
    app.register_blueprint(admin)

    register_context_processors(app)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)