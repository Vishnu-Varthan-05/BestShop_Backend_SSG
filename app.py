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

db_config = {
    'host': '10.30.10.13',
    'user': 'bestshop',
    'password': 'bestshop',
    'database': 'best_shop',
}

# db_config = {
#     'host': '127.0.0.1',
#     'user': 'root',
#     'password': '31125',
#     'database': 'best_shop',
# }

SECRET_KEY = 'haha_here_is_my_big_secret!!!'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    return mysql.connector.connect(**db_config)

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1) 
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
                cursor.execute('DELETE FROM category WHERE category_id = %s', (categoryID,))
                connection.commit()

                if category_info and category_info['category_image']:
                    image_path = category_info['category_image']
                    if os.path.exists(image_path):
                        os.remove(image_path)
                return jsonify({'message': 'Category deleted successfully'})
        
            except Exception as e:
                print(f"Error: {e}")
                return jsonify({'error': 'Failed to delete category.. Category is not empty'}), 500

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

@app.route('/category-fields', methods = ['GET', 'POST'])
@app.route('/category-fields/<int:fieldID>', methods = ['DELETE'])
def manage_fields(fieldID = None):
    if request.method == 'GET' and fieldID is None:
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

    elif request.method == 'POST' and fieldID is None:
        cursor = None
        connection = None
        try:
            data = request.json
            print(data)
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
        
    elif request.method == 'DELETE' and fieldID is not None:
        cursor = None
        connection = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute('DELETE FROM category_fields WHERE field_id = %s', (fieldID,))
            connection.commit()

            return jsonify({'message': 'Feilds deleted successfully'})

        except Exception as e:
                print(f"Error: {e}")
                return jsonify({'error': 'Failed to delete Field.. Field is not empty'}), 500 


@app.route('/field-details', methods=['GET', 'POST'])
@app.route('/field-details/<int:fieldDetailsID>', methods = ['DELETE'])
def manage_field_details(fieldDetailsID = None):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        if request.method == 'GET' and fieldDetailsID is None:
            cursor.execute('SELECT * FROM field_details')
            field_details = cursor.fetchall()
            return jsonify(field_details)
        
        elif request.method == 'POST' and fieldDetailsID is None:
            data = request.form
            field_id = data['field_id']
            details_name = data['details_name']
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
        
        elif request.method == 'DELETE' and fieldDetailsID is not None:
            try:
                cursor.execute('SELECT details_image FROM field_details WHERE detail_id = %s', (fieldDetailsID,))
                details_info = cursor.fetchone()
                cursor.execute('DELETE FROM field_details WHERE detail_id = %s', (fieldDetailsID,))
                connection.commit()

                if details_info and details_info['details_image']:
                    image_path = details_info['details_image']
                    if os.path.exists(image_path):
                        os.remove(image_path)
                return jsonify({'message': 'Field detail deleted successfully'})
            
            except Exception as e:
                print(f"Error: {e}")
                return jsonify({'error': 'Failed to delete field detail.. There are some stockes Mapped to it.. '}), 500

    except mysql.connector.Error as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/end_dist/<int:dist_id>', methods=['GET'])
def end_dist(dist_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(f'''
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
            WHERE 
                s.dist_id = {dist_id} AND DATE(s.date_added) = CURDATE() 
            GROUP BY 
                s.stock_id, s.time_added, s.date_added, s.name, s.quantity, s.price, c.category_name
        ''')
        stocks = cursor.fetchall()
        # print(stocks)
        for stock in stocks:
            stock['time_added'] = str(stock['time_added'])
            stock['date_added'] = str(stock['date_added'])
            stock['field_details_name'] = stock['field_details_name'].split(',')
        return jsonify({'dist_id': dist_id, 'stocks': stocks})
    except mysql.connector.Error as e:
        return jsonify({'error': str(e)}), 500
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
            dist_id = int(data['dist_id'])
            cursor.execute(
                'INSERT INTO stock_details (time_added, date_added, name, quantity, price, dist_id) VALUES (CURRENT_TIME(), CURRENT_DATE(), %s, %s, %s, %s)',
                (name, quantity, price, dist_id)
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

@app.route('/dashboard-data', methods=['GET'])
def get_dashboard_data():
    cursor = None 
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = """
        SELECT
            SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) BETWEEN 181 AND 300 THEN price * quantity ELSE 0 END) AS price_close_to_1_year,
            SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) BETWEEN 31 AND 180 THEN price * quantity ELSE 0 END) AS price_above_6_months,
            SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) <= 30 THEN price * quantity ELSE 0 END) AS price_above_1_month,
            SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) BETWEEN 181 AND 300 THEN quantity ELSE 0 END) AS quantity_close_to_1_year,
            SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) BETWEEN 31 AND 180 THEN quantity ELSE 0 END) AS quantity_above_6_months,
            SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) <= 30 THEN quantity ELSE 0 END) AS quantity_above_1_month,
            COALESCE(SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) BETWEEN 181 AND 300 THEN price * quantity ELSE 0 END) / NULLIF(SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) BETWEEN 181 AND 300 THEN quantity ELSE 0 END), 0), 0) AS rate_close_to_1_year,
            COALESCE(SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) BETWEEN 31 AND 180 THEN price * quantity ELSE 0 END) / NULLIF(SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) BETWEEN 31 AND 180 THEN quantity ELSE 0 END), 0), 0) AS rate_above_6_months,
            COALESCE(SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) <= 30 THEN price * quantity ELSE 0 END) / NULLIF(SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) <= 30 THEN quantity ELSE 0 END), 0), 0) AS rate_above_1_month
        FROM stock_details
        """
        cursor.execute(query)
        result = cursor.fetchone()
        series = [
            {
                'name': 'Price of the Product',
                'data': [result[0], result[1], result[2]]
            },
            {
                'name': 'Product Count',
                'data': [result[3], result[4], result[5]]
            },
            {
                'name': 'Rate of the Product',
                'data': [result[6], result[7], result[8]]
            }
        ]
        return jsonify({'series': series})
    except mysql.connector.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor is not None:
            cursor.close()

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
        elif text.startswith('category_fields/'):
            category_name = text.split('/')[1]
            cursor.execute('SELECT category_id FROM category WHERE category_name = %s', (category_name,))
            category_id = cursor.fetchone().get('category_id')
            cursor.execute('SELECT field_id, field_name FROM category_fields WHERE category_id = %s', (category_id,))
            options = cursor.fetchall()
        else:
            return jsonify({'error': 'Invalid text parameter'})

        return jsonify(options)

    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        cursor.close()
        connection.close()
        
@app.route('/uploads/<path:filename>', methods=['GET'])
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

@app.route('/add_users', methods=['POST'])
def register_user():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        data = request.json
        username = data['username']
        password = data['password']
        is_admin = data.get('is_admin', 0) 

        hashed_password = generate_password_hash(password)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({'error': 'Username is already taken'}), 400

        cursor.execute('INSERT INTO users (username, password, is_admin) VALUES (%s, %s, %s)', (username, hashed_password, is_admin))
        connection.commit()
        return jsonify({'message': 'User registered successfully'})

    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'Internal Server Error'}), 500

    finally:
        cursor.close()
        connection.close()

@app.route('/login', methods=['POST'])
def login_user():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        data = request.json
        username = data['username']
        password = data['password']

        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user[2], password):
            token = generate_token(user[0])
            return jsonify({'token': token})
        else:
            return jsonify({'error': 'Invalid username or password'}), 401

    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'Internal Server Error'}), 500

    finally:
        cursor.close()
        connection.close()

@app.route('/logout', methods=['POST'])
def logout_user():
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        return jsonify({'message': 'Logout successful'})
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host = '0.0.0.0')