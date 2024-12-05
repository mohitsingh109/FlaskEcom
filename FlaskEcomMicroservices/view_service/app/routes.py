import logging
import os

import requests
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

from .models import LoginForm, SignUpForm
from .froms import PasswordChangeForm, ShopItemsForm, OrderForm

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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


@app.route('/', methods=['GET'])
def home():

    if current_user.is_authenticated and current_user.id == 1:
        return redirect('/admin-page')

    try:
        response = requests.get(f"{PRODUCT_SERVICE_URL}/products/flash-sale")
        response.raise_for_status()  # Raises an error for non-2xx responses
        items = response.json()  # Assuming the response is in JSON format
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching products from product service: {e}")
        items = []

    try:
        if current_user.is_authenticated:
            cart_service_url = f"{CART_SERVICE_URL}/cart/{current_user.id}"
            cart_response = requests.get(cart_service_url)
            cart_response.raise_for_status()
            cart = cart_response.json()
        else:
            cart = []

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching cart from cart service: {e}")
        cart = []

    return render_template('home.html', items=items, cart=cart)


@app.route('/media/<filename>')
def media(filename):
    return send_from_directory(os.path.join(app.root_path, 'media'), filename)


@app.route('/cart')
@login_required
def show_cart():
    try:
        # Call Cart Service to fetch cart items for the current user
        response = requests.get(f"{CART_SERVICE_URL}/cart/{current_user.id}")

        if response.status_code == 200:
            cart_items = response.json()
        else:
            flash("Failed to fetch cart data")
            return redirect(url_for('home'))

        # Calculate total amount
        amount = sum(item['product']['current_price'] * item['quantity'] for item in cart_items)
        total = amount + 200  # Assuming a fixed shipping cost of 200

        return render_template('cart.html', cart=cart_items, amount=amount, total=total)

    except Exception as e:
        flash(f"Error fetching cart: {e}")
        return redirect(url_for('home'))


@app.route('/pluscart')
@login_required
def plus_cart():
    try:
        cart_id = request.args.get('cart_id')

        # Make a request to Cart Service to increment the quantity
        response = requests.post(f"{CART_SERVICE_URL}/cart/{cart_id}/increment", json={'user_id': current_user.id})

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
@login_required
def minus_cart():
    try:
        cart_id = request.args.get('cart_id')

        # Make a request to Cart Service to decrement the quantity
        response = requests.post(f"{CART_SERVICE_URL}/cart/{cart_id}/decrement", json={'user_id': current_user.id})

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
@login_required
def remove_cart():
    try:
        cart_id = request.args.get('cart_id')

        # Make a request to Cart Service to remove the cart item
        response = requests.delete(f"{CART_SERVICE_URL}/cart/{cart_id}", json={'user_id': current_user.id})

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
    form = LoginForm(request.form)

    if request.method == 'POST' and form.validate():
        email = form.email.data
        password = form.password.data

        # Call the auth-service for authentication
        response = requests.post(f"{AUTH_SERVICE_URL}/auth/login", json={"email": email, "password": password})

        if response.status_code == 200:
            user_data = response.json()  # Response containing user data
            user = User.query.get(user_data['id'])  # Retrieve user from the database by user_id

            if user:
                # Login the user
                login_user(user)

                # Redirect to home page after login
                return redirect(url_for('home'))
            else:
                flash('User not found!', 'error')
        else:
            flash('Login Failed', 'error')

    return render_template('login.html', form=form)


@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
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
# Feature a Flask-Form (it provide feature like login, logout etc)
@login_required
def log_out():
    logout_user()
    return redirect('/')


@app.route('/profile/<int:customer_id>')
@login_required
def profile(customer_id):
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
@login_required
def change_password(customer_id):
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
@login_required
def admin_page():
    if current_user.id == 1:
        return render_template('admin.html')
    return render_template('404.html')


@app.route('/add-shop-items', methods=['GET', 'POST'])
@login_required
def add_shop_items():
    if current_user.id == 1:  # Ensure only admin can add products
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

            # Create the product data to be sent to product-service
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
                    flash(f'{product_name} added Successfully')
                    return render_template('add_shop_items.html', form=form)
                else:
                    flash('Product Not Added! Error: ' + response.text)
            except Exception as e:
                flash(f'Error while connecting to product-service: {str(e)}')

        return render_template('add_shop_items.html', form=form)

    return render_template('404.html')  # Not authorized for non-admin users


@app.route('/shop-items', methods=['GET', 'POST'])
@login_required
def shop_items():
    if current_user.id == 1:
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

    return render_template('404.html')


@app.route('/update-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def update_item(item_id):
    if current_user.id == 1:
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

    return render_template('404.html')


@app.route('/delete-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def delete_item(item_id):
    if current_user.id == 1:
        try:
            # Send a DELETE request to the product-service to delete the product
            product_service_url = f"{PRODUCT_SERVICE_URL}/products/{item_id}"
            response = requests.delete(product_service_url)

            if response.status_code == 200:
                flash('One Item deleted successfully')
            else:
                flash('Error deleting item from product service!')

        except Exception as e:
            flash(f'Error: {str(e)}')

        return redirect('/shop-items')

    return render_template('404.html')


@app.route('/customers')
@login_required
def display_customers():
    if current_user.id == 1:
        try:
            # Send a GET request to the auth-service to fetch customers
            auth_service_url = f"{AUTH_SERVICE_URL}/customers"
            response = requests.get(auth_service_url)

            if response.status_code == 200:
                customers = response.json()  # Assuming the response is a list of customers
            else:
                flash('Error fetching customers from auth service!')
                customers = []

        except Exception as e:
            flash(f'Error: {str(e)}')
            customers = []

        return render_template('customers.html', customers=customers)

    return render_template('404.html')


@app.route('/add-to-cart/<int:item_id>')
@login_required
def add_to_cart(item_id):
    try:
        # Make a request to the cart service to add the item to the cart
        cart_service_url = f"{CART_SERVICE_URL}/cart/add-to-cart/{item_id}/{current_user.id}"
        response = requests.post(cart_service_url)

        if response.status_code == 200:
            flash("Item successfully added to cart or quantity updated.")
        else:
            flash("Error adding item to cart.")
    except Exception as e:
        flash(f"Error: {e}")

    return redirect(request.referrer)


@app.route('/place-order')
@login_required
def place_order():
    try:
        logger.info("Fetching data from cart service for user: %s", current_user.id)
        # Fetch the customer's cart from Cart Service
        cart_response = requests.get(f"{CART_SERVICE_URL}/cart/{current_user.id}")

        if cart_response.status_code != 200:
            flash("Failed to fetch cart items.")
            return redirect('/')

        cart_items = cart_response.json()
        logger.info("Cart data len: %s", cart_items)
        if not cart_items:
            flash("Your cart is empty.")
            return redirect('/')

        # Calculate the total amount
        total_amount = sum(item['product']['current_price'] * item['quantity'] for item in cart_items)

        # Create the order payload
        order_payload = {
            "cart_items": cart_items,
            "total_amount": total_amount,
            "customer_id": current_user.id
        }

        logger.info("Order payload : %s", order_payload)
        # Send the order request to Order Service
        order_response = requests.post(f"{ORDER_SERVICE_URL}/place-order/{current_user.id}", json=order_payload)
        logger.info("Order placed successfully")
        if order_response.status_code in (201, 200):
            flash("Order placed successfully!")
            return redirect('/orders')
        else:
            logger.warning("Order failed successfully")
            flash("Failed to place order.")
            return redirect('/')

    except Exception as e:
        print(f"Error placing order: {e}")
        flash("An error occurred while placing the order.")
        return redirect('/')


@app.route('/orders')
@login_required
def order():
    try:
        # Call the Order Service to get the orders for the current user
        response = requests.get(f"{ORDER_SERVICE_URL}/orders/{current_user.id}")

        if response.status_code == 200:
            orders = response.json()
        else:
            orders = []
        logger.info("Order Data: %s", orders)
        return render_template('orders.html', orders=orders)

    except Exception as e:
        return f"Error fetching orders: {e}", 500


@app.route('/view-orders')
@login_required
def order_view():
    if current_user.id == 1:
        try:

            response = requests.get(f"{ORDER_SERVICE_URL}/orders")

            # If the request was successful (status code 200)
            if response.status_code == 200:
                orders = response.json()  # Assuming the order service returns orders in JSON format
                return render_template('view_orders.html', orders=orders)
            else:
                flash('Failed to retrieve orders from the order service.', 'danger')
                return render_template('404.html')
        except requests.RequestException as e:
            flash(f'Error connecting to order service: {str(e)}', 'danger')
            render_template('404.html')

    return render_template('404.html')


@app.route('/update-order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def update_order(order_id):
    if current_user.id == 1:
        form = OrderForm()

        # Fetch the order details from the Order Service using an API call
        order_service_url = f'{ORDER_SERVICE_URL}/orders/order/{order_id}'
        try:
            response = requests.get(order_service_url)
            order = response.json() if response.status_code == 200 else None

            if not order:
                flash(f'Order {order_id} not found')
                return redirect('/view-orders')
        except Exception as e:
            print(f"Error fetching order: {e}")
            flash('Error fetching order details')
            return redirect('/view-orders')

        if form.validate_on_submit():
            status = form.order_status.data

            # Send the updated status to the Order Service
            try:
                update_data = {
                    'status': status
                }
                update_response = requests.put(f'{ORDER_SERVICE_URL}/orders/order/{order_id}', json=update_data)

                if update_response.status_code == 200:
                    flash(f'Order {order_id} updated successfully')
                else:
                    flash(f'Failed to update Order {order_id}: {update_response.text}')

                return redirect('/view-orders')
            except Exception as e:
                logging.error(f"Error updating order: {e}")
                flash(f'Order {order_id} not updated')
                return redirect('/view-orders')

        return render_template('order_update.html', form=form, order=order)

    return render_template('404.html')
