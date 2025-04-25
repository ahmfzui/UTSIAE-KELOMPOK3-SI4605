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

# Provider: Get all reviews
@app.route('/api/reviews', methods=['GET'])
def get_all_reviews():
    logger.info("Providing all reviews data")
    user_id = request.args.get('user_id')
    product_id = request.args.get('product_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = 'SELECT id, user_id, product_id, rating, comment, created_at FROM reviews'
    params = []
    if user_id:
        query += ' WHERE user_id = %s'
        params.append(int(user_id))
    elif product_id:
        query += ' WHERE product_id = %s'
        params.append(int(product_id))
    cursor.execute(query, params)
    reviews = cursor.fetchall()
    cursor.close()
    conn.close()
    logger.info(f"Returning {len(reviews)} reviews")
    return jsonify(reviews)

# Provider: Create review
@app.route('/api/reviews', methods=['POST'])
def create_review():
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    rating = data.get('rating')
    comment = data.get('comment')
    if not user_id or not product_id or not rating:
        logger.warning("Invalid input for creating review")
        return jsonify({'error': 'User ID, product ID, and rating are required'}), 400
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        logger.warning("Invalid rating value")
        return jsonify({'error': 'Rating must be an integer between 1 and 5'}), 400
    try:
        user_response = requests.get(f'http://localhost:5001/api/users/{user_id}', timeout=5)
        if user_response.status_code != 200:
            logger.warning(f"Invalid user_id: {user_id}")
            return jsonify({'error': 'Invalid user ID'}), 400
        product_response = requests.get(f'http://localhost:5002/api/products/{product_id}', timeout=5)
        if product_response.status_code != 200:
            logger.warning(f"Invalid product_id: {product_id}")
            return jsonify({'error': 'Invalid product ID'}), 400
    except requests.RequestException:
        logger.error("Service unavailable")
        return jsonify({'error': 'Service unavailable'}), 503
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO reviews (user_id, product_id, rating, comment) VALUES (%s, %s, %s, %s)', 
                      (user_id, product_id, rating, comment))
        conn.commit()
        review_id = cursor.lastrowid
        cursor.close()
        conn.close()
        logger.info(f"Review created: {review_id}")
        return jsonify({'id': review_id, 'user_id': user_id, 'product_id': product_id, 'rating': rating, 'comment': comment}), 201
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        logger.error(f"Failed to create review: {err}")
        return jsonify({'error': str(err)}), 500

# Provider: Update review
@app.route('/api/reviews/<int:review_id>', methods=['PUT'])
def update_review(review_id):
    logger.info(f"Updating review data for review_id: {review_id}")
    data = request.get_json()
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    rating = data.get('rating')
    comment = data.get('comment', '')
    if not user_id or not product_id or not rating:
        logger.warning("Invalid input for updating review")
        return jsonify({'error': 'User ID, product ID, and rating are required'}), 400
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        logger.warning("Invalid rating value")
        return jsonify({'error': 'Rating must be an integer between 1 and 5'}), 400
    try:
        user_response = requests.get(f'http://localhost:5001/api/users/{user_id}', timeout=5)
        if user_response.status_code != 200:
            logger.error(f"Invalid user: {user_id}")
            return jsonify({'error': 'Invalid user'}), 400
        product_response = requests.get(f'http://localhost:5002/api/products/{product_id}', timeout=5)
        if product_response.status_code != 200:
            logger.error(f"Invalid product: {product_id}")
            return jsonify({'error': 'Invalid product'}), 400
    except requests.RequestException as err:
        logger.error(f"Service request failed: {err}")
        return jsonify({'error': 'Service unavailable'}), 503
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE reviews SET user_id = %s, product_id = %s, rating = %s, comment = %s WHERE id = %s',
                      (user_id, product_id, rating, comment, review_id))
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            logger.warning(f"Review not found: {review_id}")
            return jsonify({'error': 'Review not found'}), 404
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Review updated: {review_id}")
        return jsonify({'id': review_id, 'user_id': user_id, 'product_id': product_id, 'rating': rating, 'comment': comment}), 200
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        logger.error(f"Failed to update review: {err}")
        return jsonify({'error': str(err)}), 500

# Provider: Delete review
@app.route('/api/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    logger.info(f"Deleting review data for review_id: {review_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM reviews WHERE id = %s', (review_id,))
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            logger.warning(f"Review not found: {review_id}")
            return jsonify({'error': 'Review not found'}), 404
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Review deleted: {review_id}")
        return jsonify({'message': 'Review deleted successfully'}), 200
    except mysql.connector.Error as err:
        cursor.close()
        conn.close()
        logger.error(f"Failed to delete review: {err}")
        return jsonify({'error': str(err)}), 500

# Web interface: List all reviews
@app.route('/')
def index():
    logger.info("Rendering review service index page")
    try:
        reviews_response = requests.get('http://localhost:5004/api/reviews', timeout=5)
        if reviews_response.status_code != 200:
            logger.error("Failed to fetch reviews")
            return render_template('review.html', error='Failed to fetch reviews', reviews=[])
        
        reviews = reviews_response.json()
        for review in reviews:
            user_response = requests.get(f'http://localhost:5001/api/users/{review["user_id"]}', timeout=5)
            review['username'] = user_response.json()['username'] if user_response.status_code == 200 else 'Unknown'
            product_response = requests.get(f'http://localhost:5002/api/products/{review["product_id"]}', timeout=5)
            review['product_name'] = product_response.json()['name'] if product_response.status_code == 200 else 'Unknown'
        
        logger.info(f"Rendering {len(reviews)} reviews")
        return render_template('review.html', reviews=reviews)
    except requests.RequestException as err:
        logger.error(f"Service request failed: {err}")
        return render_template('review.html', error='Service unavailable', reviews=[])

if __name__ == '__main__':
    app.run(port=5004, debug=True)