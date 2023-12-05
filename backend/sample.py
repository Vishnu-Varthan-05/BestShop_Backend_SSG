from flask import Flask, jsonify, send_from_directory, request
import mysql.connector
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# db_config = {
#     'host': '10.30.10.13',
#     'user': 'bestshop',
#     'password': 'bestshop',
#     'database': 'best_shop',
# }

db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '31125',
    'database': 'best_shop',
}

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    return mysql.connector.connect(**db_config)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

# @app.route('/get_id/<path:text>', methods=['GET'])
# def get_respective_id(text):
#     try:
#         connection = get_db_connection()
#         cursor = connection.cursor(dictionary=True)
#         if text.startswith('category/'):
#             category_name = text.split('/')[1]
#             cursor.execute('SELECT category_id FROM category WHERE category_name = %s', (category_name,))
#             category_id = cursor.fetchone().get('category_id')
#             return jsonify({'category_id': category_id})
#         elif text.startswith('category_fields/'):
#             field_name = text.split('/')[1]
#             cursor.execute('SELECT field_id FROM category_fields WHERE field_name = %s', (field_name,))
#             field_id = cursor.fetchone().get('field_id')
#             return jsonify({'field_id': field_id})
#         else:
#             return jsonify({'error': 'Invalid text parameter'})

#     except Exception as e:
#         return jsonify({'error': str(e)})
#     finally:
#         cursor.close()
#         connection.close()

if __name__ == '__main__':
    app.run(debug=True, host = '0.0.0.0')
