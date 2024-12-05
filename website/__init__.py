from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

"""
Initialize Flask Application
"""

db = SQLAlchemy()
DB_NAME = 'database.sqlite3'


def create_database():
    db.create_all()
    print('Database Created')


def create_app():
    app = Flask(__name__)
    # use for encrypting our session data
    app.config['SECRET_KEY'] = 'f8c3de3d-1fea-4d7c-a8b0-29f63c4c3454'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'

    # Initialize database with app
    db.init_app(app)

    # To perform Authentication we'll use Login Manager
    # It's a session management that keep track of anyone who has login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # load user based on pk
    @login_manager.user_loader
    def load_user(id):
        return Customer.query.get(int(id))

    # Register the url here from blueprints
    from .views import views
    from .auth import auth
    from .admin import admin
    from .models import Customer, Cart, Product, Order

    app.register_blueprint(views, url_prefix='/')  # localhost:5000/about-us
    app.register_blueprint(auth, url_prefix='/')  # localhost:5000/auth/login
    app.register_blueprint(admin, url_prefix='/')

    # Code is commented as we've already created the DB
    with app.app_context():
        create_database()

    return app
