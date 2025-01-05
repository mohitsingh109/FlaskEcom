import logging
import os

import requests
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, session, \
    Response
from flask_login import LoginManager, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from prometheus_client import generate_latest, Counter
from werkzeug.utils import secure_filename

from .froms import PasswordChangeForm, ShopItemsForm, OrderForm
from .models import LoginForm, SignUpForm

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuring the database URL for PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL',
                                                  'postgresql://auth_user:auth_password@postgres:5432/auth_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'hfdksldkslghskdghsdkgh'  # Required for session management
# Initialize the database
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Redirect to login if not authenticated


class User(db.Model):
    __tablename__ = 'customer'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100))
    password_hash = db.Column(db.String(255), nullable=False)
    date_joined = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, id, email, username, password_hash):
        self.id = id
        self.email = email
        self.username = username
        self.password_hash = password_hash

    def is_authenticated(self):
        return True  # For Flask-Login, this returns whether the user is authenticated or not.

    def is_active(self):
        return True  # Here, you can check if the user is active.

    def is_anonymous(self):
        return False  # For Flask-Login, this returns whether the user is anonymous.

    def get_id(self):
        return str(self.id)  # Flask-Login requires this method for getting the user ID.


@login_manager.user_loader
def load_user(user_id):
    """
    This function is called by Flask-Login to load a user from the database using the user_id.
    It retrieves the user by their ID from the 'customer' table.

    :param user_id: User ID stored in the session (from the JWT or Flask session)
    :return: User object or None if the user doesn't exist
    """
    # Querying the database for the user based on the provided user_id
    user = User.query.get(user_id)

    # If user exists, return the user, else return None
    return user if user else None


PRODUCT_SERVICE_URL = 'http://product-service:5001'
CART_SERVICE_URL = 'http://cart-service:5002'
AUTH_SERVICE_URL = 'http://auth-service:5003'
ORDER_SERVICE_URL = 'http://order-service:5004'

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests')


@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain; version=0.0.4')


@app.route('/', methods=['GET'])
def home():
    REQUEST_COUNT.inc()
    # Log the request to the home route
    logging.info("Accessed the home page.")

    # Check for JWT token in session
    token = session.get('jwt_token')
    user_data = None

    if token:
        try:
            # Decode the token to retrieve user information
            auth_service_url = f"{AUTH_SERVICE_URL}/auth/validate-token"
            response = requests.post(auth_service_url, json={"token": token})
            if response.status_code == 200:
                user_data = response.json().get('user')  # Extract user info from response
                logging.info(f"Token validated. User info: {user_data}")
                session['user_id'] = user_data['id']
                session['user_email'] = user_data['email']
            else:
                logging.warning("Invalid or expired token.")
                flash('Invalid or expired token. Please login again.', 'error')
                return redirect(url_for('login'))
        except requests.exceptions.RequestException as e:
            logging.error(f"Error validating token with auth service: {e}")
            flash('Error during token validation. Please try again later.', 'error')
            return redirect(url_for('login'))

    # Admin redirect if authenticated and is admin
    if user_data and user_data.get('id') == 1:
        logging.info("Admin user detected. Redirecting to admin page.")
        return redirect('/admin-page')

    # Fetch flash-sale products
    try:
        logging.info(f"Fetching flash-sale products from {PRODUCT_SERVICE_URL}/products/flash-sale.")
        response = requests.get(f"{PRODUCT_SERVICE_URL}/products/flash-sale")
        response.raise_for_status()  # Raises an error for non-2xx responses
        items = response.json()  # Assuming the response is in JSON format
        logging.info("Successfully fetched flash-sale products.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching products from product service: {e}")
        items = []

    # Fetch user's cart
    try:
        if user_data:
            cart_service_url = f"{CART_SERVICE_URL}/cart/{user_data['id']}"
            logging.info(f"Fetching cart for user ID {user_data['id']} from {cart_service_url}.")
            cart_response = requests.get(cart_service_url)
            cart_response.raise_for_status()
            cart = cart_response.json()
            logging.info("Successfully fetched user's cart.")
        else:
            logging.info("User not authenticated. Skipping cart retrieval.")
            cart = []
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching cart from cart service: {e}")
        cart = []

    # Render the home page
    logging.info("Rendering the home page.")
    return render_template('home.html', items=items, cart=cart)


@app.route('/media/<filename>')
def media(filename):
    REQUEST_COUNT.inc()
    return send_from_directory(os.path.join(app.root_path, 'media'), filename)


@app.route('/cart')
def show_cart():
    REQUEST_COUNT.inc()
    try:
        # Check for JWT token in session
        token = session.get('jwt_token')
        if not token:
            flash("You need to login to access the cart.", "error")
            return redirect(url_for('login'))

        user_data = None
        # Validate the token with Auth-Service
        try:
            auth_service_url = f"{AUTH_SERVICE_URL}/auth/validate-token"
            response = requests.post(auth_service_url, json={"token": token})
            if response.status_code == 200:
                user_data = response.json().get('user')  # Extract user info from Auth-Service
                session['user_id'] = user_data['id']
                session['user_email'] = user_data['email']
                logging.info(f"Token validated. User info: {user_data}")
            else:
                logging.warning("Invalid or expired token.")
                flash("Invalid or expired token. Please login again.", "error")
                return redirect(url_for('login'))
        except requests.exceptions.RequestException as e:
            logging.error(f"Error validating token with auth service: {e}")
            flash("Error during token validation. Please try again later.", "error")
            return redirect(url_for('login'))

        # Call Cart Service to fetch cart items for the user
        cart_service_url = f"{CART_SERVICE_URL}/cart/{user_data['id']}"
        response = requests.get(cart_service_url)

        if response.status_code == 200:
            cart_items = response.json()
        else:
            flash("Failed to fetch cart data", "error")
            return redirect(url_for('home'))

        # Calculate total amount
        amount = sum(item['product']['current_price'] * item['quantity'] for item in cart_items)
        total = amount + 200  # Assuming a fixed shipping cost of 200

        return render_template('cart.html', cart=cart_items, amount=amount, total=total)

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        flash(f"Error fetching cart: {e}", "error")
        return redirect(url_for('home'))


@app.route('/pluscart')
def plus_cart():
    REQUEST_COUNT.inc()
    try:
        # Validate the token and get user data
        token = session.get('jwt_token')
        if not token:
            return jsonify({'error': 'You need to login to update the cart.'}), 401

        user_data = validate_token_with_auth_service(token)
        if not user_data:
            return jsonify({'error': 'Invalid or expired token. Please login again.'}), 401

        cart_id = request.args.get('cart_id')

        # Make a request to Cart Service to increment the quantity
        response = requests.post(f"{CART_SERVICE_URL}/cart/{cart_id}/increment", json={'user_id': user_data['id']})

        if response.status_code == 200:
            response_data = response.json()

            # Structure the data to be sent to the frontend
            data = {
                'quantity': response_data.get('quantity'),
                'amount': response_data.get('amount'),
                'total': response_data.get('total')
            }
            return jsonify(data)
        else:
            return jsonify({'error': 'Failed to update cart item quantity'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/minuscart')
def minus_cart():
    REQUEST_COUNT.inc()
    try:
        # Validate the token and get user data
        token = session.get('jwt_token')
        if not token:
            return jsonify({'error': 'You need to login to update the cart.'}), 401

        user_data = validate_token_with_auth_service(token)
        if not user_data:
            return jsonify({'error': 'Invalid or expired token. Please login again.'}), 401

        cart_id = request.args.get('cart_id')

        # Make a request to Cart Service to decrement the quantity
        response = requests.post(f"{CART_SERVICE_URL}/cart/{cart_id}/decrement", json={'user_id': user_data['id']})

        if response.status_code == 200:
            response_data = response.json()

            # Structure the data to be sent to the frontend
            data = {
                'quantity': response_data.get('quantity'),
                'amount': response_data.get('amount'),
                'total': response_data.get('total')
            }
            return jsonify(data)
        else:
            return jsonify({'error': 'Failed to update cart item quantity'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/removecart')
def remove_cart():
    REQUEST_COUNT.inc()
    try:
        # Validate the token and get user data
        token = session.get('jwt_token')
        if not token:
            return jsonify({'error': 'You need to login to remove cart items.'}), 401

        user_data = validate_token_with_auth_service(token)
        if not user_data:
            return jsonify({'error': 'Invalid or expired token. Please login again.'}), 401

        cart_id = request.args.get('cart_id')

        # Make a request to Cart Service to remove the cart item
        response = requests.delete(f"{CART_SERVICE_URL}/cart/{cart_id}", json={'user_id': user_data['id']})

        if response.status_code == 200:
            response_data = response.json()

            # Structure the data to be sent to the frontend
            data = {
                'amount': response_data.get('amount'),
                'total': response_data.get('total')
            }
            return jsonify(data)
        else:
            return jsonify({'error': 'Failed to remove cart item'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/login', methods=['GET', 'POST'])
def login():
    REQUEST_COUNT.inc()
    logging.info("Accessed login page.")
    form = LoginForm(request.form)

    if request.method == 'POST':
        if form.validate():
            email = form.email.data
            password = form.password.data

            logging.info(f"Attempting login for email: {email}")

            try:
                # Call the auth-service for authentication
                response = requests.post(f"{AUTH_SERVICE_URL}/auth/login", json={"email": email, "password": password})
                logging.info(f"Auth-service response status: {response.status_code}")

                if response.status_code == 200:
                    user_data = response.json()  # Response containing user data
                    token = user_data.get('token')  # Get the JWT token from the response

                    if token:
                        # Store the token in the client's session
                        session['jwt_token'] = token
                        logging.info(f"Login successful for email: {email}. JWT token stored in session.")

                        # Redirect to home page after login
                        return redirect(url_for('home'))
                    else:
                        logging.error(f"Auth-service did not return a token for email: {email}")
                        flash('Authentication token not provided by auth-service!', 'error')
                else:
                    logging.warning(
                        f"Login failed for email: {email}. Auth-service returned status: {response.status_code}")
                    flash('Login Failed', 'error')

            except requests.exceptions.RequestException as e:
                logging.error(f"Error communicating with auth-service: {e}")
                flash('Unable to connect to authentication service. Please try again later.', 'error')
        else:
            logging.warning("Login form validation failed.")
            flash('Invalid input. Please check your credentials.', 'error')

    return render_template('login.html', form=form)


@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    REQUEST_COUNT.inc()
    form = SignUpForm()

    if request.method == 'POST' and form.validate():
        email = form.email.data
        username = form.username.data
        password1 = form.password1.data

        # Send the sign-up data to the auth-service
        response = requests.post(
            f"{AUTH_SERVICE_URL}/auth/sign-up",
            json={
                "email": email,
                "username": username,
                "password": password1
            }
        )

        # Handle the response from auth-service
        if response.status_code == 201:
            flash('Account Created Successfully! You can now login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Account Not Created! ' + response.json().get('message', 'Unknown error'), 'error')

    elif request.method == 'POST':
        flash('Please correct the errors in the form.', 'error')

    return render_template('signup.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
def log_out():
    REQUEST_COUNT.inc()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect('/')


@app.route('/profile/<int:customer_id>')
def profile(customer_id):
    REQUEST_COUNT.inc()
    token = session.get('jwt_token')
    if not token:
        flash("You need to login to view your profile.", "error")
        return redirect(url_for('login'))

    user_data = validate_token_with_auth_service(token)
    if not user_data:
        flash("Invalid or expired token. Please login again.", "error")
        return redirect(url_for('login'))

    # Make a request to the auth-service to get the customer data
    response = requests.get(f"{AUTH_SERVICE_URL}/auth/customer/{customer_id}")

    # Check if the response is successful
    if response.status_code == 200:
        customer = response.json()  # The customer data returned by the auth-service
        return render_template('profile.html', customer=customer)
    else:
        flash("Customer not found or error in fetching data", 'error')
        return redirect(url_for('home'))  # Redirect to home if error occurs


@app.route('/change-password/<int:customer_id>', methods=['GET', 'POST'])
def change_password(customer_id):
    REQUEST_COUNT.inc()
    token = session.get('jwt_token')
    if not token:
        flash("You need to login to change your password.", "error")
        return redirect(url_for('login'))

    user_data = validate_token_with_auth_service(token)
    if not user_data or user_data['id'] != customer_id:
        flash("You do not have permission to change this password.", "danger")
        return redirect(url_for('login'))

    form = PasswordChangeForm()

    # Make a request to the auth-service to fetch the customer data
    response = requests.get(f"{AUTH_SERVICE_URL}/auth/customer/{customer_id}")

    if response.status_code != 200:
        flash("Customer not found or error in fetching data", 'error')
        return redirect(url_for('home'))

    customer = response.json()

    if form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data
        confirm_new_password = form.confirm_new_password.data

        # Send the current password to the auth-service for validation
        auth_response = requests.post(
            f"{AUTH_SERVICE_URL}/auth/verify-password",
            json={"email": customer['email'], "password": current_password}
        )

        if auth_response.status_code == 200:
            if new_password == confirm_new_password:
                # Send the new password to the auth-service for updating
                update_response = requests.put(
                    f"{AUTH_SERVICE_URL}/auth/update-password",
                    json={
                        "customer_id": customer_id,
                        "new_password": new_password
                    }
                )

                if update_response.status_code == 200:
                    flash('Password Updated Successfully')
                    return redirect(f'/profile/{customer_id}')
                else:
                    flash('Error in updating password', 'error')
            else:
                flash('New passwords do not match', 'error')
        else:
            flash('Current password is incorrect', 'error')

    return render_template('change_password.html', form=form)


@app.route('/admin-page')
def admin_page():
    REQUEST_COUNT.inc()
    try:
        # Validate the token and get user data
        token = session.get('jwt_token')
        if not token:
            flash("You need to login to access this page.", "error")
            return redirect(url_for('login'))

        user_data = validate_token_with_auth_service(token)
        if not user_data:
            flash("Invalid or expired token. Please login again.", "error")
            return redirect(url_for('login'))

        # Check if the user is an admin (id == 1)
        if user_data.get('id') == 1:
            return render_template('admin.html')

        return render_template('404.html')  # Not authorized for non-admin users

    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "error")
        return redirect(url_for('home'))


@app.route('/add-shop-items', methods=['GET', 'POST'])
def add_shop_items():
    REQUEST_COUNT.inc()
    try:
        # Validate the token and get user data
        token = session.get('jwt_token')
        if not token:
            flash("You need to login to access this page.", "error")
            return redirect(url_for('login'))

        user_data = validate_token_with_auth_service(token)
        if not user_data:
            flash("Invalid or expired token. Please login again.", "error")
            return redirect(url_for('login'))

        # Check if the user is an admin (id == 1)
        if user_data.get('id') != 1:
            return render_template('404.html')  # Not authorized for non-admin users

        # Handle form submission
        form = ShopItemsForm()
        if form.validate_on_submit():
            product_name = form.product_name.data
            current_price = form.current_price.data
            previous_price = form.previous_price.data
            in_stock = form.in_stock.data
            flash_sale = form.flash_sale.data

            file = form.product_picture.data
            file_name = secure_filename(file.filename)
            file_path = f'./media/{file_name}'
            file.save(file_path)

            # Create the product data to be sent to the product-service
            product_data = {
                'product_name': product_name,
                'current_price': current_price,
                'previous_price': previous_price,
                'in_stock': in_stock,
                'flash_sale': flash_sale,
                'product_picture': file_path
            }

            # Send data to the product-service API
            try:
                response = requests.post(PRODUCT_SERVICE_URL + '/products/add', json=product_data)

                if response.status_code in (200, 201):  # Successful product creation
                    flash(f'{product_name} added successfully.', "success")
                    return render_template('add_shop_items.html', form=form)
                else:
                    flash(f"Product not added! Error: {response.text}", "error")
            except Exception as e:
                flash(f"Error while connecting to product-service: {str(e)}", "error")

        return render_template('add_shop_items.html', form=form)

    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "error")
        return redirect(url_for('home'))


@app.route('/shop-items', methods=['GET', 'POST'])
def shop_items():
    REQUEST_COUNT.inc()
    token = session.get('jwt_token')
    if not token:
        flash("You need to login to view the items.", "error")
        return redirect(url_for('login'))

    user_data = validate_token_with_auth_service(token)
    if not user_data or user_data['id'] != 1:
        flash("You do not have permission to view these items.", "danger")
        return redirect(url_for('login'))

    try:
        # Fetch the list of products from the product-service
        product_service_url = f"{PRODUCT_SERVICE_URL}/products"
        response = requests.get(product_service_url)

        if response.status_code == 200:
            items = response.json()  # Assuming the response is a list of product data
        else:
            flash("Error fetching products from product service!")
            items = []

    except Exception as e:
        flash(f"Error: {str(e)}")
        items = []

    return render_template('shop_items.html', items=items)


@app.route('/update-item/<int:item_id>', methods=['GET', 'POST'])
def update_item(item_id):
    REQUEST_COUNT.inc()
    token = session.get('jwt_token')
    if not token:
        flash("You need to login to update the item.", "error")
        return redirect(url_for('login'))

    user_data = validate_token_with_auth_service(token)
    if not user_data or user_data['id'] != 1:
        flash("You do not have permission to update this item.", "danger")
        return redirect(url_for('login'))

    form = ShopItemsForm()

    # Fetch the current item details from the product-service
    product_service_url = f"{PRODUCT_SERVICE_URL}/products/{item_id}"
    response = requests.get(product_service_url)

    if response.status_code == 200:
        item_to_update = response.json()
    else:
        flash("Item not found in product service!")
        return redirect('/shop-items')

    # Pre-fill form with current item data
    form.product_name.render_kw = {'placeholder': item_to_update['product_name']}
    form.previous_price.render_kw = {'placeholder': item_to_update['previous_price']}
    form.current_price.render_kw = {'placeholder': item_to_update['current_price']}
    form.in_stock.render_kw = {'placeholder': item_to_update['in_stock']}
    form.flash_sale.render_kw = {'placeholder': item_to_update['flash_sale']}

    if form.validate_on_submit():
        product_name = form.product_name.data
        current_price = form.current_price.data
        previous_price = form.previous_price.data
        in_stock = form.in_stock.data
        flash_sale = form.flash_sale.data

        file = form.product_picture.data
        file_name = secure_filename(file.filename)
        file_path = f'./media/{file_name}'

        file.save(file_path)

        try:
            # Prepare the data to send in the PUT request
            update_data = {
                'product_name': product_name,
                'current_price': current_price,
                'previous_price': previous_price,
                'in_stock': in_stock,
                'flash_sale': flash_sale,
                'product_picture': file_path
            }

            # Send a PUT request to the product-service to update the product details
            update_response = requests.put(f"{product_service_url}/update", json=update_data)

            if update_response.status_code == 200:
                flash(f'{product_name} updated Successfully')
                return redirect('/shop-items')
            else:
                flash('Error: Unable to update item in product service')
        except Exception as e:
            flash(f'Error: {str(e)}')
            print('Product not Updated', e)

    return render_template('update_item.html', form=form)


@app.route('/delete-item/<int:item_id>', methods=['GET', 'POST'])
def delete_item(item_id):
    REQUEST_COUNT.inc()
    token = session.get('jwt_token')
    if not token:
        flash("You need to login to delete an item.", "error")
        return redirect(url_for('login'))

    user_data = validate_token_with_auth_service(token)
    if not user_data or user_data['id'] != 1:
        flash("You do not have permission to delete this item.", "danger")
        return redirect(url_for('login'))

    try:
        product_service_url = f"{PRODUCT_SERVICE_URL}/products/{item_id}"
        response = requests.delete(product_service_url)

        if response.status_code == 200:
            flash('One item deleted successfully')
        else:
            flash('Error deleting item from product service!')

    except Exception as e:
        flash(f'Error: {str(e)}')

    return redirect('/shop-items')


@app.route('/customers')
def display_customers():
    REQUEST_COUNT.inc()
    token = session.get('jwt_token')
    if not token:
        flash("You need to login to view customers.", "error")
        return redirect(url_for('login'))

    user_data = validate_token_with_auth_service(token)
    if not user_data or user_data['id'] != 1:
        flash("You do not have permission to view customers.", "danger")
        return redirect(url_for('login'))

    try:
        # Send a GET request to the auth-service to fetch customers
        auth_service_url = f"{AUTH_SERVICE_URL}/customers"
        response = requests.get(auth_service_url)

        if response.status_code == 200:
            customers = response.json()
        else:
            flash('Error fetching customers from auth service!')
            customers = []

    except Exception as e:
        flash(f'Error: {str(e)}')
        customers = []

    return render_template('customers.html', customers=customers)


@app.route('/add-to-cart/<int:item_id>')
def add_to_cart(item_id):
    REQUEST_COUNT.inc()
    try:
        # Validate the token and get user data
        token = session.get('jwt_token')
        if not token:
            flash("You need to login to add items to the cart.", "error")
            return redirect(url_for('login'))

        user_data = validate_token_with_auth_service(token)
        if not user_data:
            flash("Invalid or expired token. Please login again.", "error")
            return redirect(url_for('login'))

        # Make a request to the cart service to add the item to the cart
        cart_service_url = f"{CART_SERVICE_URL}/cart/add-to-cart/{item_id}/{user_data['id']}"
        response = requests.post(cart_service_url)

        if response.status_code == 200:
            flash("Item successfully added to cart or quantity updated.")
        else:
            flash("Error adding item to cart.", "error")
    except Exception as e:
        flash(f"Error: {e}", "error")

    return redirect(request.referrer or url_for('home'))


@app.route('/place-order')
def place_order():
    REQUEST_COUNT.inc()
    try:
        # Validate the token and get user data
        token = session.get('jwt_token')
        if not token:
            flash("You need to login to place an order.", "error")
            return redirect(url_for('login'))

        user_data = validate_token_with_auth_service(token)
        if not user_data:
            flash("Invalid or expired token. Please login again.", "error")
            return redirect(url_for('login'))

        logging.info("Fetching data from cart service for user: %s", user_data['id'])
        # Fetch the customer's cart from Cart Service
        cart_response = requests.get(f"{CART_SERVICE_URL}/cart/{user_data['id']}")

        if cart_response.status_code != 200:
            flash("Failed to fetch cart items.")
            return redirect('/')

        cart_items = cart_response.json()
        logging.info("Cart data len: %s", cart_items)
        if not cart_items:
            flash("Your cart is empty.")
            return redirect('/')

        # Calculate the total amount
        total_amount = sum(item['product']['current_price'] * item['quantity'] for item in cart_items)

        # Create the order payload
        order_payload = {
            "cart_items": cart_items,
            "total_amount": total_amount,
            "customer_id": user_data['id']
        }

        logging.info("Order payload : %s", order_payload)
        # Send the order request to Order Service
        order_response = requests.post(f"{ORDER_SERVICE_URL}/place-order/{user_data['id']}", json=order_payload)
        logging.info("Order placed successfully")
        if order_response.status_code in (201, 200):
            flash("Order placed successfully!")
            return redirect('/orders')
        else:
            logging.warning("Order failed successfully")
            flash("Failed to place order.")
            return redirect('/')

    except Exception as e:
        print(f"Error placing order: {e}")
        flash("An error occurred while placing the order.")
        return redirect('/')


@app.route('/orders')
def order():
    REQUEST_COUNT.inc()
    try:
        # Validate the token and get user data
        token = session.get('jwt_token')
        if not token:
            flash("You need to login to view your orders.", "error")
            return redirect(url_for('login'))

        user_data = validate_token_with_auth_service(token)
        if not user_data:
            flash("Invalid or expired token. Please login again.", "error")
            return redirect(url_for('login'))

        # Call the Order Service to get the orders for the user
        response = requests.get(f"{ORDER_SERVICE_URL}/orders/{user_data['id']}")

        if response.status_code == 200:
            orders = response.json()
        else:
            orders = []
        logging.info("Order Data: %s", orders)
        return render_template('orders.html', orders=orders)

    except Exception as e:
        return f"Error fetching orders: {e}", 500


@app.route('/view-orders')
def order_view():
    REQUEST_COUNT.inc()
    token = session.get('jwt_token')
    if not token:
        flash("You need to login to view orders.", "error")
        return redirect(url_for('login'))

    user_data = validate_token_with_auth_service(token)
    if not user_data or user_data['id'] != 1:
        flash("You do not have permission to view these orders.", "danger")
        return redirect(url_for('login'))

    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/orders")

        if response.status_code == 200:
            orders = response.json()
            return render_template('view_orders.html', orders=orders)
        else:
            flash('Failed to retrieve orders from the order service.', 'danger')
            return render_template('404.html')
    except requests.RequestException as e:
        flash(f'Error connecting to order service: {str(e)}', 'danger')
        return render_template('404.html')


@app.route('/update-order/<int:order_id>', methods=['GET', 'POST'])
def update_order(order_id):
    REQUEST_COUNT.inc()
    token = session.get('jwt_token')
    if not token:
        flash("You need to login to update the order.", "error")
        return redirect(url_for('login'))

    user_data = validate_token_with_auth_service(token)
    if not user_data or user_data['id'] != 1:
        flash("You do not have permission to update this order.", "danger")
        return redirect(url_for('login'))

    form = OrderForm()
    order_service_url = f'{ORDER_SERVICE_URL}/orders/order/{order_id}'

    try:
        response = requests.get(order_service_url)
        order = response.json() if response.status_code == 200 else None

        if not order:
            flash(f'Order {order_id} not found')
            return redirect('/view-orders')
    except Exception as e:
        flash('Error fetching order details')
        return redirect('/view-orders')

    if form.validate_on_submit():
        status = form.order_status.data
        try:
            update_data = {'status': status}
            update_response = requests.put(f'{ORDER_SERVICE_URL}/orders/order/{order_id}', json=update_data)

            if update_response.status_code == 200:
                flash(f'Order {order_id} updated successfully')
            else:
                flash(f'Failed to update Order {order_id}: {update_response.text}')

            return redirect('/view-orders')
        except Exception as e:
            flash(f'Order {order_id} not updated')
            return redirect('/view-orders')

    return render_template('order_update.html', form=form, order=order)


def validate_token_with_auth_service(token):
    try:
        auth_service_url = f"{AUTH_SERVICE_URL}/auth/validate-token"
        response = requests.post(auth_service_url, json={"token": token})
        if response.status_code == 200:
            return response.json().get('user')  # Extract user info from Auth-Service
        else:
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error validating token with Auth-Service: {e}")
        return None
