from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

from .models import Customer, db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    customer = Customer.query.filter_by(email=email).first()
    if customer and customer.verify_password(password):
        return jsonify({"message": "Login successful", "status": 200, "id": customer.id}), 200
    else:
        return jsonify({"message": "Invalid credentials", "status": 401}), 401


@auth_bp.route('/auth/sign-up', methods=['POST'])
def sign_up():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email and password are required!"}), 400

    # Check if user already exists
    if Customer.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists!"}), 400

    # Create new customer
    new_customer = Customer(email=email, username=username)
    new_customer.password = password  # Password is hashed using the setter

    try:
        db.session.add(new_customer)
        db.session.commit()
        return jsonify({"message": "User registered successfully!"}), 201
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


@auth_bp.route('/auth/customer/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    # Query the database for the customer
    customer = Customer.query.get(customer_id)

    # If customer exists, return their data
    if customer:
        return jsonify({
            'id': customer.id,
            'email': customer.email,
            'username': customer.username,
            'date_joined': customer.date_joined
        }), 200
    else:
        return jsonify({'message': 'Customer not found'}), 404


@auth_bp.route('/auth/verify-password', methods=['POST'])
def verify_password():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Query the database to find the customer by email
    customer = Customer.query.filter_by(email=email).first()

    if customer and check_password_hash(customer.password_hash, password):
        return jsonify({'message': 'Password verified'}), 200
    else:
        return jsonify({'message': 'Invalid password'}), 400


@auth_bp.route('/auth/update-password', methods=['PUT'])
def update_password():
    data = request.get_json()
    customer_id = data.get('customer_id')
    new_password = data.get('new_password')

    # Query the database to find the customer by ID
    customer = Customer.query.get(customer_id)

    if customer:
        # Hash the new password and update
        customer.password_hash = generate_password_hash(new_password)
        db.session.commit()
        return jsonify({'message': 'Password updated successfully'}), 200
    else:
        return jsonify({'message': 'Customer not found'}), 404


@auth_bp.route('/customers', methods=['GET'])
def get_customers():
    try:
        # Fetch all customers from the database
        customers = Customer.query.all()

        # Prepare a list of customer data to return as a JSON response
        customer_list = [{
            'id': customer.id,
            'email': customer.email,
            'username': customer.username,
            'date_joined': customer.date_joined
        } for customer in customers]

        return jsonify(customer_list)

    except Exception as e:
        return jsonify({'message': f'Error fetching customers: {str(e)}'}), 500
