from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import mysql.connector
import requests
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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

# Provider: Get all users
@app.route('/api/users', methods=['GET'])
def get_all_users():
    logger.info("Providing all users data")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, username, email, phone_number, address FROM users')
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    logger.info(f"Returning {len(users)} users")
    return jsonify(users)

# Provider: Get user by ID
@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    logger.info(f"Providing user data for user_id: {user_id}")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, username, email, phone_number, address FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        logger.info(f"User found: {user['username']}")
        return jsonify(user)
    logger.warning(f"User not found: {user_id}")
    return jsonify({'error': 'User not found'}), 404

# Provider: Create user
@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    phone_number = data.get('phone_number')
    address = data.get('address')
    if not username or not email or not phone_number or not address:
        logger.warning("Invalid input for creating user")
        return jsonify({'error': 'Username, email, phone number, and address are required'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, email, phone_number, address) VALUES (%s, %s, %s, %s)', 
                      (username, email, phone_number, address))
        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()
        conn.close()
        logger.info(f"User created: {username}")
        return jsonify({'id': user_id, 'username': username, 'email': email, 'phone_number': phone_number, 'address': address}), 201
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        logger.error(f"Failed to create user: {err}")
        return jsonify({'error': str(err)}), 500

# Provider: Update user
@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    logger.info(f"Updating user data for user_id: {user_id}")
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    phone_number = data.get('phone_number')
    address = data.get('address')
    if not username or not email or not phone_number or not address:
        logger.warning("Invalid input for updating user")
        return jsonify({'error': 'Username, email, phone number, and address are required'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE users SET username = %s, email = %s, phone_number = %s, address = %s WHERE id = %s',
                      (username, email, phone_number, address, user_id))
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            logger.warning(f"User not found: {user_id}")
            return jsonify({'error': 'User not found'}), 404
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"User updated: {username}")
        return jsonify({'id': user_id, 'username': username, 'email': email, 'phone_number': phone_number, 'address': address}), 200
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        logger.error(f"Failed to update user: {err}")
        return jsonify({'error': str(err)}), 500

# Provider: Delete user
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    logger.info(f"Deleting user data for user_id: {user_id}")
    # Check for dependencies (orders and reviews)
    try:
        order_response = requests.get(f'http://localhost:5003/api/orders?user_id={user_id}', timeout=5)
        if order_response.status_code == 200 and len(order_response.json()) > 0:
            logger.warning(f"Cannot delete user {user_id}: has existing orders")
            return jsonify({'error': 'Cannot delete user with existing orders'}), 400
        review_response = requests.get(f'http://localhost:5004/api/reviews?user_id={user_id}', timeout=5)
        if review_response.status_code == 200 and len(review_response.json()) > 0:
            logger.warning(f"Cannot delete user {user_id}: has existing reviews")
            return jsonify({'error': 'Cannot delete user with existing reviews'}), 400
    except requests.RequestException as err:
        logger.error(f"Dependency check failed: {err}")
        return jsonify({'error': 'Service unavailable'}), 503
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            logger.warning(f"User not found: {user_id}")
            return jsonify({'error': 'User not found'}), 404
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"User deleted: {user_id}")
        return jsonify({'message': 'User deleted successfully'}), 200
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        logger.error(f"Failed to delete user: {err}")
        return jsonify({'error': str(err)}), 500

# Consumer: Get user's order history from Order Service
@app.route('/api/users/<int:user_id>/orders', methods=['GET'])
def get_user_orders(user_id):
    logger.info(f"Consuming order data for user_id: {user_id}")
    try:
        response = requests.get(f'http://localhost:5003/api/orders?user_id={user_id}', timeout=5)
        if response.status_code == 200:
            logger.info(f"Successfully fetched orders for user_id: {user_id}")
            return jsonify(response.json())
        logger.error(f"Failed to fetch orders: {response.status_code}")
        return jsonify({'error': 'Failed to fetch orders'}), response.status_code
    except requests.RequestException as err:
        logger.error(f"Order service request failed: {err}")
        return jsonify({'error': 'Order service unavailable'}), 503

# Web interface: List all users
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, username, email, phone_number, address FROM users')
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    logger.info("Rendering user service index page")
    return render_template('user.html', users=users)

# Web interface: View user orders
@app.route('/users/<int:user_id>/orders')
def view_user_orders(user_id):
    logger.info(f"Rendering orders for user_id: {user_id}")
    try:
        user_response = requests.get(f'http://localhost:5001/api/users/{user_id}', timeout=5)
        if user_response.status_code != 200:
            logger.error(f"User not found: {user_id}")
            return render_template('user.html', error='User not found', users=[])
        
        orders_response = requests.get(f'http://localhost:5003/api/orders?user_id={user_id}', timeout=5)
        if orders_response.status_code != 200:
            logger.error(f"Failed to fetch orders for user_id: {user_id}")
            return render_template('user.html', error='Failed to fetch orders', users=[])
        
        orders = orders_response.json()
        user = user_response.json()
        
        for order in orders:
            product_response = requests.get(f'http://localhost:5002/api/products/{order["product_id"]}', timeout=5)
            order['product_name'] = product_response.json()['name'] if product_response.status_code == 200 else 'Unknown'
        
        logger.info(f"Rendering orders page for user_id: {user_id}")
        return render_template('user.html', users=[], user=user, orders=orders)
    except requests.RequestException as err:
        logger.error(f"Service request failed: {err}")
        return render_template('user.html', error='Service unavailable', users=[])

if __name__ == '__main__':
    app.run(port=5001, debug=True)