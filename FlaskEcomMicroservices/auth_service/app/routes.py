import logging

from flask import Blueprint, request, jsonify, Response
from prometheus_client import generate_latest, Counter
from werkzeug.security import check_password_hash, generate_password_hash

from .jwtutils import create_token, decode_token
from .models import Customer, db

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests')


@auth_bp.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain; version=0.0.4')


@auth_bp.route('/auth/login', methods=['POST'])
def login():
    REQUEST_COUNT.inc()
    data = request.json
    email = data.get('email')
    password = data.get('password')
    logging.info(f"Login attempt for email: {email}")

    customer = Customer.query.filter_by(email=email).first()
    if customer and customer.verify_password(password):
        # Create a JWT token
        access_token = create_token({'id': customer.id, 'email': customer.email})
        logging.info(f"Start the decoding of token$ {access_token}")
        try:
            decoded_token = decode_token(access_token)
            logging.info(f"Decoded Token: {decoded_token}")
        except Exception as e:
            logging.error(e)
        logging.info(f"Login successful for email: {email}, token: {access_token}")
        return jsonify({
            "message": "Login successful",
            "status": 200,
            "token": access_token
        }), 200
    else:
        logging.warning(f"Invalid login attempt for email: {email}")
        return jsonify({"message": "Invalid credentials", "status": 401}), 401


@auth_bp.route('/auth/sign-up', methods=['POST'])
def sign_up():
    REQUEST_COUNT.inc()
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    logger.info(f"Sign-up attempt for email: {email}")

    if not email or not password:
        logger.warning("Sign-up failed: Missing email or password")
        return jsonify({"message": "Email and password are required!"}), 400

    # Check if user already exists
    if Customer.query.filter_by(email=email).first():
        logger.warning(f"Sign-up failed: Email {email} already exists")
        return jsonify({"message": "Email already exists!"}), 400

    # Create new customer
    new_customer = Customer(email=email, username=username)
    new_customer.password = password  # Password is hashed using the setter

    try:
        db.session.add(new_customer)
        db.session.commit()
        logger.info(f"User registered successfully with email: {email}")
        return jsonify({"message": "User registered successfully!"}), 201
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        return jsonify({"message": f"Error: {str(e)}"}), 500


@auth_bp.route('/auth/customer/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    REQUEST_COUNT.inc()
    logger.info(f"Fetching customer with ID: {customer_id}")

    # Query the database for the customer
    customer = Customer.query.get(customer_id)

    if customer:
        logger.info(f"Customer found with ID: {customer_id}")
        return jsonify({
            'id': customer.id,
            'email': customer.email,
            'username': customer.username,
            'date_joined': customer.date_joined
        }), 200
    else:
        logger.warning(f"Customer not found with ID: {customer_id}")
        return jsonify({'message': 'Customer not found'}), 404


@auth_bp.route('/auth/verify-password', methods=['POST'])
def verify_password():
    REQUEST_COUNT.inc()
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    logger.info(f"Password verification attempt for email: {email}")

    customer = Customer.query.filter_by(email=email).first()

    if customer and check_password_hash(customer.password_hash, password):
        logger.info(f"Password verified for email: {email}")
        return jsonify({'message': 'Password verified'}), 200
    else:
        logger.warning(f"Invalid password for email: {email}")
        return jsonify({'message': 'Invalid password'}), 400


@auth_bp.route('/auth/update-password', methods=['PUT'])
def update_password():
    REQUEST_COUNT.inc()
    data = request.get_json()
    customer_id = data.get('customer_id')
    new_password = data.get('new_password')

    logger.info(f"Password update attempt for customer ID: {customer_id}")

    customer = Customer.query.get(customer_id)

    if customer:
        customer.password_hash = generate_password_hash(new_password)
        db.session.commit()
        logger.info(f"Password updated successfully for customer ID: {customer_id}")
        return jsonify({'message': 'Password updated successfully'}), 200
    else:
        logger.warning(f"Customer not found with ID: {customer_id}")
        return jsonify({'message': 'Customer not found'}), 404


@auth_bp.route('/customers', methods=['GET'])
def get_customers():
    REQUEST_COUNT.inc()
    logger.info("Fetching all customers")

    try:
        customers = Customer.query.all()

        customer_list = [{
            'id': customer.id,
            'email': customer.email,
            'username': customer.username,
            'date_joined': customer.date_joined
        } for customer in customers]

        logger.info("Fetched all customers successfully")
        return jsonify(customer_list)
    except Exception as e:
        logger.error(f"Error fetching customers: {str(e)}")
        return jsonify({'message': f'Error fetching customers: {str(e)}'}), 500


@auth_bp.route('/auth/validate-token', methods=['POST'])
def validate_token():
    REQUEST_COUNT.inc()
    """
    Endpoint to validate a JWT token and return user information if valid.
    """
    token = request.json.get('token')
    if not token:
        return jsonify({'error': 'Token is required'}), 400

    try:
        logging.info(token)
        # Decode the token using Flask-JWT-Extended
        decoded_token = decode_token(token)
        logging.info(f"Decoded Token: {decoded_token}")

        # Extract the 'identity' field from the token (contains user data)
        # 'sub' should contain {'id': user_id, 'email': user_email}
        user_info = decoded_token.get('sub')

        if not user_info:
            return jsonify({'error': 'Invalid token'}), 401

        return jsonify({'user': user_info}), 200
    except Exception as e:
        logging.error(f"Token validation failed: {e}")
        return jsonify({'error': 'Invalid or expired token'}), 401
