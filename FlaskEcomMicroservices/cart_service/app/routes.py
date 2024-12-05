import logging

import requests
from flask import Blueprint, flash, jsonify, request

from .models import Cart
from .models import db

cart_routes = Blueprint('cart_routes', __name__)

PRODUCT_SERVICE_URL = 'http://product-service:5001'

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


@cart_routes.route('/cart/add-to-cart/<int:item_id>/<int:user_id>', methods=['POST'])
def add_to_cart(item_id, user_id):
    try:

        logger.info("Fetching the product details")
        # Call Product Service to fetch product details
        product_service_url = f"{PRODUCT_SERVICE_URL}/products/{item_id}"
        response = requests.get(product_service_url)

        if response.status_code == 200:
            product = response.json()  # Assuming the product data is returned in JSON format

            # Check if the item already exists in the cart for the given user
            item_exists = Cart.query.filter_by(product_link=item_id, customer_link=user_id).first()

            if item_exists:
                # Update quantity if item already exists in the cart
                item_exists.quantity += 1
                db.session.commit()
                flash(f'Quantity of {product["product_name"]} has been updated.')
            else:
                # Add new item to the cart
                new_cart_item = Cart(product_link=item_id, customer_link=user_id, quantity=1)
                db.session.add(new_cart_item)
                db.session.commit()
                flash(f'{product["product_name"]} added to cart.')

            return jsonify({"message": "Item added to cart successfully."}), 200
        else:
            flash("Error fetching product data.")
            return jsonify({"message": "Error fetching product data"}), 400
    except Exception as e:
        flash(f"Error adding item to cart: {e}")
        return jsonify({"message": "Error adding item to cart"}), 500


@cart_routes.route('/cart/<int:user_id>', methods=['GET'])
def get_cart_items(user_id):
    cart_items = Cart.query.filter_by(customer_link=user_id).all()
    result = []
    for item in cart_items:
        product = item.product
        data = {
            'id': item.id,
            'product_link': item.product_link,
            'quantity': item.quantity,
            'product': {
                'id': product.id,
                'product_name': product.product_name,
                'current_price': product.current_price,
                'previous_price': product.previous_price,
                'in_stock': product.in_stock,
                'flash_sale': product.flash_sale,
                'product_picture': product.product_picture,
                'date_added': product.date_added
            }
        }
        result.append(data)

    return jsonify(result), 200


@cart_routes.route('/cart/<int:cart_id>/increment', methods=['POST'])
def increment_cart_item(cart_id):
    try:
        # Get the cart item by ID
        cart_item = Cart.query.get(cart_id)
        if not cart_item:
            return jsonify({'error': 'Cart item not found'}), 404

        # Increment the quantity
        cart_item.quantity += 1
        db.session.commit()

        # Recalculate the total amount for all cart items for this user
        user_id = request.json.get('user_id')
        cart_items = Cart.query.filter_by(customer_link=user_id).all()

        total_amount = sum(item.product.current_price * item.quantity for item in cart_items)

        data = {
            'quantity': cart_item.quantity,
            'amount': total_amount,
            'total': total_amount + 200  # Add shipping or other charges
        }

        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cart_routes.route('/cart/<int:cart_id>/decrement', methods=['POST'])
def decrement_cart_item(cart_id):
    try:
        # Get the cart item by ID
        cart_item = Cart.query.get(cart_id)
        if not cart_item:
            return jsonify({'error': 'Cart item not found'}), 404

        # Decrement the quantity if it's greater than 1
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            db.session.commit()
        else:
            # Optionally, remove the item if quantity reaches zero
            db.session.delete(cart_item)
            db.session.commit()
            return jsonify({'quantity': 0, 'amount': 0, 'total': 200}), 200

        # Recalculate the total amount for all cart items for this user
        user_id = request.json.get('user_id')
        cart_items = Cart.query.filter_by(customer_link=user_id).all()

        total_amount = sum(item.product.current_price * item.quantity for item in cart_items)

        data = {
            'quantity': cart_item.quantity,
            'amount': total_amount,
            'total': total_amount + 200  # Add shipping or other charges
        }

        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

