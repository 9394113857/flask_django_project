import logging
import os
import sqlite3
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

import requests
from flask import Flask, render_template, request, jsonify
from requests.exceptions import HTTPError

app = Flask(__name__)

# Set up logger configuration
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(logs_dir, exist_ok=True)

log_file = os.path.join(logs_dir, f'{datetime.now().date()}.log')

log_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5)
log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s [%(module)s:%(lineno)d] %(message)s'))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# Delete older log files
for filename in os.listdir(logs_dir):
    if filename.endswith('.log') and filename != os.path.basename(log_file):
        os.remove(os.path.join(logs_dir, filename))

# SQLite database connection setup
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('calculator.db')
        cursor = conn.cursor()
        
        # Define the table creation query
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS calculator_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT,
                num1 REAL,
                num2 REAL,
                result REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''

        # Create the table
        cursor.execute(create_table_query)
        conn.commit()

        return conn
    except sqlite3.Error as e:
        logger.error(f'SQLite error: {e}')
        return None

# Home page route
@app.route('/')
def home():
    logger.info('Home page accessed')
    return render_template('index.html')

@app.route('/calculate')
def calculate():
    try:
        num1 = request.args.get('num1')
        num2 = request.args.get('num2')
        operation = request.args.get('operation')

        logger.info(f'Calculate route accessed with operation: {operation}, num1: {num1}, num2: {num2}')

        # Validate inputs
        if not (num1 and num2 and operation):
            return jsonify({'error': 'Missing parameters (num1, num2, operation)'}), 400

        # Make request to external API
        url = f'http://localhost:8000/app3/{operation}/{num1}/{num2}/'
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes

        result = response.json()['result']

        logger.info(f'Result: {result}')

        # Store result in database
        conn = create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO calculator_logs (operation, num1, num2, result)
                    VALUES (?, ?, ?, ?)
                ''', (operation, num1, num2, result))
                conn.commit()
            except sqlite3.Error as e:
                logger.error(f'SQLite error: {e}')
                return jsonify({'error': 'Database error occurred'}), 500
            finally:
                conn.close()
        else:
            return jsonify({'error': 'Database connection error'}), 500

        return jsonify({'result': result}), 200

    except requests.exceptions.RequestException as e:
        logger.error(f'Request error: {e}')
        return jsonify({'error': f'Request error: {e}'}), 500

    except KeyError as e:
        logger.error(f'KeyError: {e}')
        return jsonify({'error': 'Invalid response format from external API'}), 500

    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        return jsonify({'error': 'Internal server error'}), 500

    
    except requests.exceptions.RequestException as e:
        logger.error(f'Request error: {e}')
        return f"Request error: {e}", 500  # Return an error response for request exceptions

# View routes for app1 and app2
@app.route('/app1/')
def app1_view():
    return get_response_content('http://localhost:8000/app1/')

@app.route('/app1/second/')
def app1_second_view():
    return get_response_content('http://localhost:8000/app1/second/')

@app.route('/app2/')
def app2_view():
    return get_response_content('http://localhost:8000/app2/')

@app.route('/app2/second/')
def app2_second_view():
    return get_response_content('http://localhost:8000/app2/second/')

# Function to handle HTTP errors from requests
@app.errorhandler(HTTPError)
def handle_http_error(error):
    error_code = error.response.status_code
    error_message = error.response.text

    logger.error(f'HTTP Error {error_code}: {error_message}')

    return f"HTTP Error {error_code}: {error_message}", error_code

# Helper function to fetch response content from external APIs
def get_response_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f'Request error: {e}')
        return f"Request error: {e}", 500

if __name__ == '__main__':
    # Allow specifying a custom port at runtime, default to 5000
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000

    app.run(port=port, debug=True)
    logger.info(f"Server started at port {port}")
