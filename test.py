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

@app.route('/field-details', methods=['GET', 'POST'])
def manage_field_details():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        if request.method == 'GET':
            cursor.execute('SELECT * FROM field_details')
            field_details = cursor.fetchall()
            return jsonify(field_details)
        elif request.method == 'POST':
            data = request.form
            field_name = data['field_name']
            details_name = data['details_name']
            cursor.execute('SELECT field_id FROM category_fields WHERE field_name = %s', (field_name,))
            field_id_tuple = cursor.fetchone()
            if not field_id_tuple:
                return jsonify({'error': 'Invalid field_name'}), 400
            field_id = field_id_tuple['field_id']
            cursor.execute(
                'INSERT INTO field_details (field_id, details_name) VALUES (%s, %s)',
                (field_id, details_name)
            )
            connection.commit()
            field_details_id = cursor.lastrowid
            if 'image' in request.files:
                file = request.files['image']
                if file and allowed_file(file.filename):
                    filename = f"{field_details_id}_{secure_filename(file.filename)}"
                    file_to_be_saved = os.path.join(app.config['UPLOAD_FOLDER'], 'images', 'field_details', filename)
                    file.save(file_to_be_saved)
                    cursor.execute(
                        'UPDATE field_details SET details_image = %s WHERE detail_id = %s',
                        (file_to_be_saved, field_details_id)
                    )
                    connection.commit()
            return jsonify({'message': 'Field details added successfully'})
    except mysql.connector.Error as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        cursor.close()
        connection.close()
@app.route('/dropdown/<path:text>', methods=['GET'])
def get_dropdown_options(text):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        if text.isdigit():
            cursor.execute('SELECT field_name FROM category_fields WHERE category_id = %s', (text,))
            options = [result['field_name'] for result in cursor.fetchall()]
        elif text == 'category':
            cursor.execute('SELECT category_name FROM category')
            options = [result['category_name'] for result in cursor.fetchall()]
        elif text == 'category_fields':
            cursor.execute('SELECT field_name FROM category_fields')
            options = [result['field_name'] for result in cursor.fetchall()]
        elif text.startswith('category_fields/'):
            category_name = text.split('/')[1]
            cursor.execute('SELECT category_id FROM category WHERE category_name = %s', (category_name,))
            category_id = cursor.fetchone().get('category_id')
            cursor.execute('SELECT field_name FROM category_fields WHERE category_id = %s', (category_id,))
            options = [result['field_name'] for result in cursor.fetchall()]
        else:
            return jsonify({'error': 'Invalid text parameter'})
        return jsonify(options)

    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        cursor.close()
        connection.close()

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
