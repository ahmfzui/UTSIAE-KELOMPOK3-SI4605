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

# Provider: Get all orders
@app.route('/api/orders', methods=['GET'])
def get_all_orders():
    logger.info("Providing all orders data")
    user_id = request.args.get('user_id')
    product_id = request.args.get('product_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = 'SELECT id, user_id, product_id, quantity, total_price, status, created_at FROM orders'
    params = []
    if user_id:
        query += ' WHERE user_id = %s'
        params.append(int(user_id))
    elif product_id:
        query += ' WHERE product_id = %s'
        params.append(int(product_id))
    cursor.execute(query, params)
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    logger.info(f"Returning {len(orders)} orders")
    return jsonify(orders)

# Provider: Create order
@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    status = data.get('status')
    if not user_id or not product_id or not quantity or not status:
        logger.warning("Invalid input for creating order")
        return jsonify({'error': 'User ID, product ID, quantity, and status are required'}), 400
    try:
        quantity = int(quantity)
        if quantity <= 0:
            logger.warning("Invalid quantity value")
            return jsonify({'error': 'Quantity must be a positive integer'}), 400
    except (ValueError, TypeError):
        logger.warning("Invalid quantity format")
        return jsonify({'error': 'Quantity must be a valid integer'}), 400
    if status not in ['pending', 'completed', 'cancelled']:
        logger.warning(f"Invalid status value: {status}")
        return jsonify({'error': "Status must be 'pending', 'completed', or 'cancelled'"}), 400
    try:
        user_response = requests.get(f'http://localhost:5001/api/users/{user_id}', timeout=5)
        if user_response.status_code != 200:
            logger.warning(f"Invalid user_id: {user_id}")
            return jsonify({'error': 'Invalid user ID'}), 400
        product_response = requests.get(f'http://localhost:5002/api/products/{product_id}', timeout=5)
        if product_response.status_code != 200:
            logger.warning(f"Invalid product_id: {product_id}")
            return jsonify({'error': 'Invalid product ID'}), 400
        product = product_response.json()
        price = float(product['price'])
        if product['stock'] < quantity:
            logger.warning(f"Insufficient stock for product_id: {product_id}")
            return jsonify({'error': 'Insufficient stock'}), 400
    except requests.RequestException:
        logger.error("Service unavailable")
        return jsonify({'error': 'Service unavailable'}), 503
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE products SET stock = stock - %s WHERE id = %s', (quantity, product_id))
        total_price = price * quantity
        cursor.execute('INSERT INTO orders (user_id, product_id, quantity, total_price, status) VALUES (%s, %s, %s, %s, %s)', 
                      (user_id, product_id, quantity, total_price, status))
        conn.commit()
        order_id = cursor.lastrowid
        cursor.close()
        conn.close()
        logger.info(f"Order created: {order_id}")
        return jsonify({'id': order_id, 'user_id': user_id, 'product_id': product_id, 'quantity': quantity, 'total_price': total_price, 'status': status}), 201
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        logger.error(f"Failed to create order: {err}")
        return jsonify({'error': str(err)}), 500

# Provider: Update order
@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    logger.info(f"Updating order data for order_id: {order_id}")
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    status = data.get('status')
    if not user_id or not product_id or not quantity or not status:
        logger.warning("Invalid input for updating order")
        return jsonify({'error': 'User ID, product ID, quantity, and status are required'}), 400
    try:
        quantity = int(quantity)
        if quantity <= 0:
            logger.warning("Invalid quantity value")
            return jsonify({'error': 'Quantity must be a positive integer'}), 400
    except (ValueError, TypeError):
        logger.warning("Invalid quantity format")
        return jsonify({'error': 'Quantity must be a valid integer'}), 400
    if status not in ['pending', 'completed', 'cancelled']:
        logger.warning(f"Invalid status value: {status}")
        return jsonify({'error': "Status must be 'pending', 'completed', or 'cancelled'"}), 400
    try:
        user_response = requests.get(f'http://localhost:5001/api/users/{user_id}', timeout=5)
        if user_response.status_code != 200:
            logger.warning(f"Invalid user_id: {user_id}")
            return jsonify({'error': 'Invalid user ID'}), 400
        product_response = requests.get(f'http://localhost:5002/api/products/{product_id}', timeout=5)
        if product_response.status_code != 200:
            logger.warning(f"Invalid product_id: {product_id}")
            return jsonify({'error': 'Invalid product ID'}), 400
        product = product_response.json()
        price = float(product['price'])
    except requests.RequestException:
        logger.error("Service unavailable")
        return jsonify({'error': 'Service unavailable'}), 503
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('SELECT quantity, product_id FROM orders WHERE id = %s', (order_id,))
        old_order = cursor.fetchone()
        if not old_order:
            cursor.close()
            conn.close()
            logger.warning(f"Order not found: {order_id}")
            return jsonify({'error': 'Order not found'}), 404
        old_quantity = old_order['quantity']
        stock_adjustment = old_quantity - quantity
        cursor.execute('UPDATE products SET stock = stock + %s WHERE id = %s', (stock_adjustment, old_order['product_id']))
        if product['stock'] < quantity:
            cursor.close()
            conn.close()
            logger.warning(f"Insufficient stock for product_id: {product_id}")
            return jsonify({'error': 'Insufficient stock'}), 400
        total_price = price * quantity
        cursor.execute('UPDATE orders SET user_id = %s, product_id = %s, quantity = %s, total_price = %s, status = %s WHERE id = %s',
                      (user_id, product_id, quantity, total_price, status, order_id))
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Order updated: {order_id}")
        return jsonify({'id': order_id, 'user_id': user_id, 'product_id': product_id, 'quantity': quantity, 'total_price': total_price, 'status': status}), 200
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        logger.error(f"Failed to update order: {err}")
        return jsonify({'error': str(err)}), 500

# Provider: Delete order
@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    logger.info(f"Deleting order data for order_id: {order_id}")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('SELECT quantity, product_id FROM orders WHERE id = %s', (order_id,))
        order = cursor.fetchone()
        if not order:
            cursor.close()
            conn.close()
            logger.warning(f"Order not found: {order_id}")
            return jsonify({'error': 'Order not found'}), 404
        cursor.execute('UPDATE products SET stock = stock + %s WHERE id = %s', (order['quantity'], order['product_id']))
        cursor.execute('DELETE FROM orders WHERE id = %s', (order_id,))
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Order deleted: {order_id}")
        return jsonify({'message': 'Order deleted successfully'}), 200
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        logger.error(f"Failed to delete order: {err}")
        return jsonify({'error': str(err)}), 500

# Web interface: List all orders
@app.route('/')
def index():
    logger.info("Rendering order service index page")
    try:
        orders_response = requests.get('http://localhost:5003/api/orders', timeout=5)
        if orders_response.status_code != 200:
            logger.error("Failed to fetch orders")
            return render_template('order.html', error='Failed to fetch orders', orders=[])
        
        orders = orders_response.json()
        for order in orders:
            user_response = requests.get(f'http://localhost:5001/api/users/{order["user_id"]}', timeout=5)
            order['username'] = user_response.json()['username'] if user_response.status_code == 200 else 'Unknown'
            product_response = requests.get(f'http://localhost:5002/api/products/{order["product_id"]}', timeout=5)
            order['product_name'] = product_response.json()['name'] if product_response.status_code == 200 else 'Unknown'
        
        logger.info(f"Rendering {len(orders)} orders")
        return render_template('order.html', orders=orders)
    except requests.RequestException as err:
        logger.error(f"Service request failed: {err}")
        return render_template('order.html', error='Service unavailable', orders=[])

if __name__ == '__main__':
    app.run(port=5003, debug=True)