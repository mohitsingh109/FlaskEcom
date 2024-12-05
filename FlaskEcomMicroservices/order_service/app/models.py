from .database import db
from datetime import datetime


class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    previous_price = db.Column(db.Float, nullable=False)
    in_stock = db.Column(db.Integer, nullable=False)
    flash_sale = db.Column(db.Boolean, default=False)
    product_picture = db.Column(db.String(100), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)


class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100))
    password_hash = db.Column(db.String(150), nullable=False)
    date_joined = db.Column(db.DateTime(), default=datetime.utcnow)


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    product_link = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    customer_link = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

    product = db.relationship('Product', backref=db.backref('cart_items', lazy=True))
    customer = db.relationship('Customer', backref=db.backref('cart_items', lazy=True))


class Order(db.Model):
    __tablename__ = 'orders'  # Ensure this is consistent with your database
    id = db.Column(db.Integer, primary_key=True)
    product_link = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)  # Ensure this matches Product
    customer_link = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    payment_id = db.Column(db.String(100), nullable=False)

    # Define relationships
    product = db.relationship('Product', backref=db.backref('orders', lazy=True))
    customer = db.relationship('Customer', backref=db.backref('orders', lazy=True))

    def __repr__(self):
        return f"<Order(product_link={self.product_link}, customer_link={self.customer_link}, quantity={self.quantity}, status={self.status})>"
