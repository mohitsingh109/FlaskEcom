from flask import Flask
from flask_jwt_extended import JWTManager

from .models import db


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://auth_user:auth_password@postgres:5432/auth_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'F5DB977622D67F7B78647F828D385'
    app.config['JWT_ALGORITHM'] = 'HS256'
    # Initialize JWTManager
    jwt = JWTManager(app)

    db.init_app(app)

    from .routes import auth_bp
    app.register_blueprint(auth_bp)

    return app
