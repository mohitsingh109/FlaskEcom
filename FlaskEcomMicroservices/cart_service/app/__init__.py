from flask import Flask
from .config import Config
from .database import db
from .routes import cart_routes


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    app.register_blueprint(cart_routes)

    return app
