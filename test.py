from flask import Flask, jsonify, send_from_directory, request
import mysql.connector
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime


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
SECRET_KEY = 'haha_here_is_my_big_secret!!!'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    return mysql.connector.connect(**db_config)

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)  # Token expiration time
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/categories/<int:categoryID>/<int:fieldID>', methods=['GET'])
@app.route('/categories/<int:categoryID>', methods=['GET', 'DELETE'])
@app.route('/categories', methods=['GET', 'POST'])
def categories(categoryID=None, fieldID=None):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        if request.method == 'GET':
            if categoryID is not None and fieldID is not None:
                if fieldID == 0:
                    cursor.execute('SELECT * FROM field_details fd INNER JOIN category_fields f ON f.field_id = fd.field_id INNER JOIN category c ON c.category_id = f.category_id ORDER BY f.field_id DESC')
                else:
                    cursor.execute('SELECT * FROM field_details WHERE field_id = %s', (fieldID,))
            elif categoryID is not None:
                if categoryID == 0:
                    cursor.execute('SELECT * FROM category_fields f INNER JOIN category c ON c.category_id = f.category_id ORDER BY c.category_id DESC')
                else:
                    cursor.execute('SELECT * FROM category_fields WHERE category_id = %s', (categoryID,))
            else:
                cursor.execute('SELECT * FROM category')
            result = cursor.fetchall()
            return jsonify(result)
        
        elif request.method == 'POST':
            data = request.form
            category_name = data['category_name']
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute('INSERT INTO category (category_name) VALUES (%s)', (category_name,))
            connection.commit()
            category_id = cursor.lastrowid
            if 'image' in request.files:
                file = request.files['image']
                if file and allowed_file(file.filename):
                    filename = f"{category_id}_{secure_filename(file.filename)}"
                    fileToBeSaved = os.path.join(app.config['UPLOAD_FOLDER'], 'images', 'category', filename)
                    file.save(fileToBeSaved)
                    cursor.execute('UPDATE category SET category_image = %s WHERE category_id = %s', (fileToBeSaved, category_id))
                    connection.commit()
            return jsonify({'message': 'Category added successfully'})
        
        elif request.method == 'DELETE' and categoryID is not None:
            try:
                cursor.execute('SELECT category_image FROM category WHERE category_id = %s', (categoryID,))
                category_info = cursor.fetchone()
                cursor.execute('SELECT field_details_id FROM mapping_table WHERE category_id = %s', (categoryID,))
                field_details_ids = tuple([row['field_details_id'] for row in cursor.fetchall()])

                cursor.execute('DELETE FROM mapping_table WHERE category_id = %s', (categoryID,))
                cursor.execute('SELECT details_image FROM field_details WHERE detail_id IN (%s)' % ','.join(map(str, field_details_ids)))
                details_image_paths = [row['details_image'] for row in cursor.fetchall()]
                cursor.execute('DELETE FROM field_details WHERE detail_id IN (%s)' % ','.join(map(str, field_details_ids)))
                cursor.execute('DELETE FROM category_fields WHERE category_id = %s', (categoryID,))
                cursor.execute('DELETE FROM category WHERE category_id = %s', (categoryID,))
                connection.commit()

                if category_info and category_info['category_image']:
                    image_path = category_info['category_image']
                    if os.path.exists(image_path):
                        os.remove(image_path)

                for image_path in details_image_paths:
                    if image_path and os.path.exists(image_path):
                        os.remove(image_path)

                return jsonify({'message': 'Category deleted successfully'})

            except Exception as e:
                print(f"Error: {e}")
                return jsonify({'error': 'Failed to delete category'}), 500



        elif request.method == 'GET' and categoryID is not None and fieldID is None:
            cursor.execute('SELECT * FROM category_fields WHERE category_id = %s', (categoryID,))
            category_fields = cursor.fetchall()
            return jsonify(category_fields)
        elif request.method == 'GET' and categoryID is not None and fieldID is not None:
            cursor.execute('SELECT * FROM field_details WHERE field_id = %s', (fieldID,))
            field_details = cursor.fetchall()
            return jsonify(field_details)
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    app.run(debug=True, host = '0.0.0.0')