import logging

from flask import Blueprint, request, jsonify
from .models import Order, Cart, Product
from .models import db
import uuid

order_routes = Blueprint('order_routes', __name__)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


@order_routes.route('/place-order/<int:user_id>', methods=['POST'])
def place_order(user_id):
    try:
        data = request.json
        cart_items = data.get('cart_items', [])
        total_amount = data.get('total_amount', 0)
        payment_id = str(uuid.uuid4())

        # Create orders from cart items
        try:
            for item in cart_items:
                new_order = Order(
                    product_link=item['product_link'],
                    customer_link=user_id,
                    quantity=item['quantity'],
                    price=item['product']['current_price'],
                    status='Pending',
                    payment_id=payment_id
                )
                logger.info("Attempting to place new order: %s", new_order)
                db.session.add(new_order)

                product = Product.query.get(item['product_link'])
                if product:
                    product.in_stock -= item['quantity']
                    logger.info("Reducing product quantity: %s, New stock: %d", product.product_name, product.in_stock)

                db.session.commit()
                logger.info("Order placed successfully: %s", new_order)

                # Delete the cart items after placing the orders
                for item in cart_items:
                    cart_item = Cart.query.filter_by(customer_link=user_id, product_link=item['product_link']).first()
                    if cart_item:
                        db.session.delete(cart_item)

                # Commit the deletion of cart items
                db.session.commit()
                logger.info("Cart items deleted successfully after placing the order")
        except Exception as e:
            logger.error("Failed to place order: %s", e)

        return jsonify({'message': 'Order placed successfully', 'payment_id': payment_id, 'total': total_amount}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@order_routes.route('/orders/<int:user_id>', methods=['GET'])
def get_orders(user_id):
    try:
        orders = Order.query.filter_by(customer_link=user_id).all()
        result = []
        for order in orders:
            product = order.product  # Access the related product
            order_data = {
                'id': order.id,
                'quantity': order.quantity,
                'price': order.price,
                'status': order.status,
                'payment_id': order.payment_id,
                'product_link': order.product_link,
                'product': {
                    'id': product.id,
                    'product_name': product.product_name,
                    'current_price': product.current_price,
                    'previous_price': product.previous_price,
                    'in_stock': product.in_stock,
                    'flash_sale': product.flash_sale,
                    'product_picture': product.product_picture,
                    'date_added': product.date_added
                },
                'customer': {
                    'id': order.customer.id,
                    'email': order.customer.email,
                    'username': order.customer.username,
                    'date_joined': order.customer.date_joined,
                }
            }
            result.append(order_data)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        return jsonify({'error': str(e)}), 500


@order_routes.route('/orders', methods=['GET'])
def get_all_orders():
    try:
        orders = Order.query.all()
        result = []
        for order in orders:
            product = order.product  # Access the related product
            order_data = {
                'id': order.id,
                'quantity': order.quantity,
                'price': order.price,
                'status': order.status,
                'payment_id': order.payment_id,
                'product_link': order.product_link,
                'product': {
                    'id': product.id,
                    'product_name': product.product_name,
                    'current_price': product.current_price,
                    'previous_price': product.previous_price,
                    'in_stock': product.in_stock,
                    'flash_sale': product.flash_sale,
                    'product_picture': product.product_picture,
                    'date_added': product.date_added
                },
                'customer': {
                    'id': order.customer.id,
                    'email': order.customer.email,
                    'username': order.customer.username,
                    'date_joined': order.customer.date_joined,
                }
            }
            result.append(order_data)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        return jsonify({'error': str(e)}), 500


@order_routes.route('/orders/order/<int:order_id>', methods=['GET', 'PUT'])
def order_api(order_id):
    if request.method == 'GET':
        # Fetch the order details
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        return jsonify({
            'id': order.id,
            'quantity': order.quantity,
            'price': order.price,
            'status': order.status,
            'payment_id': order.payment_id,
            'product_link': order.product_link,
            'customer_link': order.customer_link
        })

    if request.method == 'PUT':
        # Update the order status
        data = request.get_json()
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        order.status = data.get('status', order.status)

        try:
            db.session.commit()
            return jsonify({'message': 'Order updated successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
