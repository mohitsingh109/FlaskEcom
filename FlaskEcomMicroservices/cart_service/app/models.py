from datetime import datetime

from .database import db


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    product_link = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    customer_link = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

    product = db.relationship('Product', backref=db.backref('cart_items', lazy=True))
    customer = db.relationship('Customer', backref=db.backref('cart_items', lazy=True))


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    previous_price = db.Column(db.Float, nullable=False)
    in_stock = db.Column(db.Integer, nullable=False)
    flash_sale = db.Column(db.Boolean, default=False)
    product_picture = db.Column(db.String(100), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Product {self.product_name}>"


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100))
    password_hash = db.Column(db.String(150), nullable=False)
    date_joined = db.Column(db.DateTime(), default=datetime.utcnow)