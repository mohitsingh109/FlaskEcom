from flask import Flask
from .config import Config
from .database import db
from .routes import order_routes


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    app.register_blueprint(order_routes)

    return app
