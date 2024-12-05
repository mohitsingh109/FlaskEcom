from flask import Flask
from .models import db


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://auth_user:auth_password@postgres:5432/auth_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from .routes import auth_bp
    app.register_blueprint(auth_bp)

    return app
