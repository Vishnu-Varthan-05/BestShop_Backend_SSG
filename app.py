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

@app.route('/categories', methods=['GET', 'POST'])
def get_all_categories():
    if request.method == 'GET':
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute('SELECT * FROM category')
            categories = cursor.fetchall()
            return jsonify(categories)
        except Exception as e:
            return jsonify({'error': str(e)})
        finally:
            cursor.close()
            connection.close()
    
    elif request.method == 'POST':
        try:
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
        except Exception as e:
            app.logger.error(f"Error adding category: {str(e)}")
            return jsonify({'error': 'Internal Server Error'}), 500
        finally:
            cursor.close()
            connection.close()

@app.route('/category-fields', methods = ['GET', 'POST'])
def get_all_category_fields():
    if request.method == 'GET':
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary = True)
            cursor.execute('SELECT * FROM category_fields')
            category_fields = cursor.fetchall()
            return jsonify(category_fields)
        except Exception as e:
            return jsonify({'error': str(e)})
        finally:
            cursor.close()
            connection.close()   
    
    elif request.method == 'POST':
        cursor = None
        connection = None
        try:
            data = request.json
            category_id = int(data['category_id'])
            field_name = data['field_name']
            field_type = data['type']
            has_separate_page = int(data['has_separate_page'])
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                'INSERT INTO category_fields (category_id, field_name, type, has_separate_page) VALUES (%s, %s, %s, %s)',
                (category_id, field_name, field_type, has_separate_page)
            )
            connection.commit()
            return jsonify({'message': 'Category field added successfully'})
        except Exception as e:
            app.logger.error(f"Error adding category field: {str(e)}")
            return jsonify({'error': 'Internal Server Error'}), 500 

# @app.route('/fields-details', methods=['GET'])
# def get_all_field_details():
#     try:
#         connection = get_db_connection()
#         cursor = connection.cursor(dictionary = True)
#         cursor.execute('SELECT * FROM field_details')
#         field_details = cursor.fetchall()
#         return jsonify(field_details)
#     except Exception as e:
#         return jsonify({'error': str(e)})
#     finally:
#         cursor.close()
#         connection.close()

@app.route('/categories/<int:categoryID>', methods=['GET'])
def get_category_fields(categoryID):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM category_fields WHERE category_id = %s', (categoryID,))
        category_fields = cursor.fetchall()
        return jsonify(category_fields)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        cursor.close()
        connection.close()

@app.route('/categories/<int:categoryID>/<int:fieldID>', methods=['GET'])
def get_field_details(categoryID, fieldID):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM field_details WHERE field_id = %s', (fieldID,))
        field_details = cursor.fetchall()
        return jsonify(field_details)
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        cursor.close()
        connection.close()

@app.route('/stocks', methods=['GET', 'POST'])
def manage_stocks():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    if request.method == 'GET':
        try:
            cursor.execute('''
                SELECT 
                    s.stock_id,
                    DATE_FORMAT(s.time_added, '%H:%i:%s') AS time_added,
                    DATE_FORMAT(s.date_added, '%Y-%m-%d') AS date_added,
                    s.name AS stock_name,
                    s.quantity,
                    s.price,
                    c.category_name,
                    GROUP_CONCAT(fd.details_name) AS field_details_name
                FROM 
                    stock_details s
                INNER JOIN 
                    mapping_table m ON s.stock_id = m.stock_id
                INNER JOIN
                    category c ON m.category_id = c.category_id
                INNER JOIN
                    field_details fd ON m.field_details_id = fd.detail_id
                GROUP BY 
                    s.stock_id, s.time_added, s.date_added, s.name, s.quantity, s.price, c.category_name
            ''')
            stocks = cursor.fetchall()
            for stock in stocks:
                stock['time_added'] = str(stock['time_added'])
                stock['date_added'] = str(stock['date_added'])
                stock['field_details_name'] = stock['field_details_name'].split(',')
            return jsonify(stocks)

        except mysql.connector.Error as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            connection.close()

    elif request.method == 'POST':
        try:
            data = request.json
            category_id = int(data['category_id'])
            field_details_ids = data['field_details_id']
            name = data['name']
            quantity = int(data['quantity'])
            price = int(data['price'])
            cursor.execute(
                'INSERT INTO stock_details (time_added, date_added, name, quantity, price) VALUES (CURRENT_TIME(), CURRENT_DATE(), %s, %s, %s)',
                (name, quantity, price)
            )
            connection.commit()
            stock_id = cursor.lastrowid
            for field_details_id in field_details_ids:
                cursor.execute(
                    'INSERT INTO mapping_table (stock_id, category_id, field_details_id) VALUES (%s, %s, %s)',
                    (stock_id, category_id, field_details_id)
                )
                connection.commit()
            return jsonify({'message': 'Stock added successfully'})
        
        except mysql.connector.Error as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            connection.close()

@app.route('/uploads/<path:filename>', methods=['GET'])
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    app.run(debug=True, host = '0.0.0.0')
