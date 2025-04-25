from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import mysql.connector
import requests
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'ecommerce'
}

# Helper function to get database connection
def get_db_connection():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        logger.error(f"Database connection failed: {err}")
        raise

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    logger.info("Health check requested")
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({'status': 'healthy'}), 200
    except mysql.connector.Error:
        logger.error("Health check failed: Database unavailable")
        return jsonify({'status': 'unhealthy', 'error': 'Database unavailable'}), 503

# Provider: Get all products
@app.route('/api/products', methods=['GET'])
def get_all_products():
    logger.info("Providing all products data")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, name, description, price, stock FROM products')
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    logger.info(f"Returning {len(products)} products")
    return jsonify(products)

# Provider: Get product by ID
@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    logger.info(f"Providing product data for product_id: {product_id}")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, name, description, price, stock FROM products WHERE id = %s', (product_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()
    if product:
        logger.info(f"Product found: {product['name']}")
        return jsonify(product)
    logger.warning(f"Product not found: {product_id}")
    return jsonify({'error': 'Product not found'}), 404

# Provider: Create product
@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    stock = data.get('stock')
    if not name or not price or not stock:
        logger.warning("Invalid input for creating product")
        return jsonify({'error': 'Name, price, and stock are required'}), 400
    try:
        price = float(price)
        if price <= 0:
            logger.warning("Invalid price value")
            return jsonify({'error': 'Price must be a positive number'}), 400
    except (ValueError, TypeError):
        logger.warning("Invalid price format")
        return jsonify({'error': 'Price must be a valid number'}), 400
    if not isinstance(stock, int) or stock < 0:
        logger.warning("Invalid stock value")
        return jsonify({'error': 'Stock must be a non-negative integer'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO products (name, description, price, stock) VALUES (%s, %s, %s, %s)', 
                      (name, description, price, stock))
        conn.commit()
        product_id = cursor.lastrowid
        cursor.close()
        conn.close()
        logger.info(f"Product created: {name}")
        return jsonify({'id': product_id, 'name': name, 'description': description, 'price': price, 'stock': stock}), 201
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        logger.error(f"Failed to create product: {err}")
        return jsonify({'error': str(err)}), 500

# Provider: Update product
@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    logger.info(f"Updating product data for product_id: {product_id}")
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    stock = data.get('stock')
    if not name or not price or not stock:
        logger.warning("Invalid input for updating product")
        return jsonify({'error': 'Name, price, and stock are required'}), 400
    try:
        price = float(price)
        if price <= 0:
            logger.warning("Invalid price value")
            return jsonify({'error': 'Price must be a positive number'}), 400
    except (ValueError, TypeError):
        logger.warning("Invalid price format")
        return jsonify({'error': 'Price must be a valid number'}), 400
    if not isinstance(stock, int) or stock < 0:
        logger.warning("Invalid stock value")
        return jsonify({'error': 'Stock must be a non-negative integer'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE products SET name = %s, description = %s, price = %s, stock = %s WHERE id = %s',
                      (name, description, price, stock, product_id))
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            logger.warning(f"Product not found: {product_id}")
            return jsonify({'error': 'Product not found'}), 404
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Product updated: {name}")
        return jsonify({'id': product_id, 'name': name, 'description': description, 'price': price, 'stock': stock}), 200
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        logger.error(f"Failed to update product: {err}")
        return jsonify({'error': str(err)}), 500

# Provider: Delete product
@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    logger.info(f"Deleting product data for product_id: {product_id}")
    try:
        order_response = requests.get(f'http://localhost:5003/api/orders?product_id={product_id}', timeout=5)
        if order_response.status_code == 200 and len(order_response.json()) > 0:
            logger.warning(f"Cannot delete product {product_id}: has existing orders")
            return jsonify({'error': 'Cannot delete product with existing orders'}), 400
        review_response = requests.get(f'http://localhost:5004/api/reviews?product_id={product_id}', timeout=5)
        if review_response.status_code == 200 and len(review_response.json()) > 0:
            logger.warning(f"Cannot delete product {product_id}: has existing reviews")
            return jsonify({'error': 'Cannot delete product with existing reviews'}), 400
    except requests.RequestException as err:
        logger.error(f"Dependency check failed: {err}")
        return jsonify({'error': 'Service unavailable'}), 503
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM products WHERE id = %s', (product_id,))
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            logger.warning(f"Product not found: {product_id}")
            return jsonify({'error': 'Product not found'}), 404
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Product deleted: {product_id}")
        return jsonify({'message': 'Product deleted successfully'}), 200
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        logger.error(f"Failed to delete product: {err}")
        return jsonify({'error': str(err)}), 500

# Consumer: Get product reviews from Review Service
@app.route('/api/products/<int:product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    logger.info(f"Consuming review data for product_id: {product_id}")
    try:
        response = requests.get(f'http://localhost:5004/api/reviews?product_id={product_id}', timeout=5)
        if response.status_code == 200:
            logger.info(f"Successfully fetched reviews for product_id: {product_id}")
            return jsonify(response.json())
        logger.error(f"Failed to fetch reviews: {response.status_code}")
        return jsonify({'error': 'Failed to fetch reviews'}), response.status_code
    except requests.RequestException as err:
        logger.error(f"Review service request failed: {err}")
        return jsonify({'error': 'Review service unavailable'}), 503

# Web interface: List all products
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, name, description, price, stock FROM products')
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    logger.info("Rendering product service index page")
    return render_template('product.html', products=products)

# Web interface: View product reviews
@app.route('/products/<int:product_id>/reviews')
def view_product_reviews(product_id):
    logger.info(f"Rendering reviews for product_id: {product_id}")
    try:
        product_response = requests.get(f'http://localhost:5002/api/products/{product_id}', timeout=5)
        if product_response.status_code != 200:
            logger.error(f"Product not found: {product_id}")
            return render_template('product.html', error='Product not found', products=[])
        
        reviews_response = requests.get(f'http://localhost:5004/api/reviews?product_id={product_id}', timeout=5)
        if reviews_response.status_code != 200:
            logger.error(f"Failed to fetch reviews for product_id: {product_id}")
            return render_template('product.html', error='Failed to fetch reviews', products=[])
        
        reviews = reviews_response.json()
        product = product_response.json()
        
        for review in reviews:
            user_response = requests.get(f'http://localhost:5001/api/users/{review["user_id"]}', timeout=5)
            review['username'] = user_response.json()['username'] if user_response.status_code == 200 else 'Unknown'
        
        logger.info(f"Rendering reviews page for product_id: {product_id}")
        return render_template('product.html', products=[], product=product, reviews=reviews)
    except requests.RequestException as err:
        logger.error(f"Service request failed: {err}")
        return render_template('product.html', error='Service unavailable', products=[])

if __name__ == '__main__':
    app.run(port=5002, debug=True)