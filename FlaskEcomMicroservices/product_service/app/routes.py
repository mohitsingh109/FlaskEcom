import logging

from flask import Blueprint, request, jsonify

from .models import Product, db

product_routes = Blueprint('product_routes', __name__)

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# POST route to add a new product
@product_routes.route('/products/add', methods=['POST'])
def add_product():
    data = request.get_json()

    product_name = data.get('product_name')
    current_price = data.get('current_price')
    previous_price = data.get('previous_price')
    in_stock = data.get('in_stock')
    flash_sale = data.get('flash_sale')
    product_picture = data.get('product_picture')  # Assuming it's a file path or URL

    if not all([product_name, current_price, previous_price, in_stock, flash_sale, product_picture]):
        return jsonify({'message': 'Missing required fields'}), 400

    # Create a new product
    new_product = Product(
        product_name=product_name,
        current_price=current_price,
        previous_price=previous_price,
        in_stock=in_stock,
        flash_sale=flash_sale,
        product_picture=product_picture
    )

    try:
        db.session.add(new_product)
        db.session.commit()
        return jsonify({'message': f'Product {product_name} added successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error adding product: {str(e)}'}), 500


@product_routes.route('/products/flash-sale', methods=['GET'])
def flash_sale_products():
    try:
        # Query products that are on flash sale
        flash_sale_items = Product.query.filter_by(flash_sale=True).all()

        if not flash_sale_items:
            logger.warning("No flash sale products found.")

        # Prepare a list of product data to return, including all the columns
        items = []
        logger.info("========>>>>>>>>")
        for item in flash_sale_items:
            try:
                # Check each field and handle missing or invalid values
                product_data = {
                    'id': item.id if item.id is not None else 'N/A',
                    'product_name': item.product_name if item.product_name else 'Unknown',
                    'current_price': item.current_price if item.current_price else 0.0,
                    'previous_price': item.previous_price if item.previous_price else 0.0,
                    'in_stock': item.in_stock if item.in_stock is not None else 0,
                    'flash_sale': item.flash_sale if item.flash_sale is not None else False,
                    'product_picture': item.product_picture if item.product_picture else 'default.jpg'
                }
                items.append(product_data)
            except Exception as e:
                logger.error(f"Error processing product with ID {item.id}: {e}")

        logger.info(f"Found {len(items)} flash sale products.")
        logger.debug(f"Items data: {items}")  # Use debug level to log data

        return jsonify(items)

    except Exception as e:
        # Return error message if something goes wrong
        return jsonify({'message': f'Error fetching flash sale products: {e}'}), 500


@product_routes.route('/products/<int:item_id>/update', methods=['PUT'])
def update_product(item_id):
    try:
        # Fetch the item by ID
        product = Product.query.get(item_id)

        if not product:
            return jsonify({'message': 'Product not found'}), 404

        # Update product details
        data = request.get_json()
        product.product_name = data['product_name']
        product.current_price = data['current_price']
        product.previous_price = data['previous_price']
        product.in_stock = data['in_stock']
        product.flash_sale = data['flash_sale']
        product.product_picture = data['product_picture']

        # Commit changes to the database
        db.session.commit()

        return jsonify({'message': 'Product updated successfully'}), 200
    except Exception as e:
        return jsonify({'message': f'Error updating product: {str(e)}'}), 500


@product_routes.route('/products', methods=['GET'])
def get_all_products():
    try:
        # Fetch all products from the database
        products = Product.query.all()

        # Prepare the product data to return
        product_list = [{
            'id': product.id,
            'product_name': product.product_name,
            'current_price': product.current_price,
            'previous_price': product.previous_price,
            'in_stock': product.in_stock,
            'flash_sale': product.flash_sale,
            'product_picture': product.product_picture,
            'date_added': product.date_added
        } for product in products]

        return jsonify(product_list), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching products: {str(e)}'}), 500


@product_routes.route('/products/<int:item_id>', methods=['DELETE'])
def delete_product(item_id):
    try:
        # Find the product by ID
        item_to_delete = Product.query.get(item_id)
        if item_to_delete:
            db.session.delete(item_to_delete)
            db.session.commit()
            return jsonify({'message': 'Product deleted successfully'}), 200
        else:
            return jsonify({'message': 'Product not found'}), 404

    except Exception as e:
        return jsonify({'message': f'Error deleting product: {str(e)}'}), 500


@product_routes.route('/products/<int:item_id>', methods=['GET'])
def get_product_by_id(item_id):
    try:
        product = Product.query.get(item_id)  # Fetch product from the database using the product ID
        if not product:
            return jsonify({"message": "Product not found"}), 404

        product_data = {
            'id': product.id,
            'product_name': product.product_name,
            'current_price': product.current_price,
            'previous_price': product.previous_price,
            'in_stock': product.in_stock,
            'flash_sale': product.flash_sale,
            'product_picture': product.product_picture,
            'date_added': product.date_added
        }

        logger.info(f"Product data for ID {item_id} fetched successfully")
        return jsonify(product_data)

    except Exception as e:
        logger.error(f"Error fetching product with ID {item_id}: {str(e)}")
        return jsonify({"message": "Error fetching product data"}), 500
