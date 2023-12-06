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

# @app.route('/dashboard-data', methods=['GET'])
# def get_dashboard_data():
#     cursor = None 
#     try:
#         connection = get_db_connection()
#         cursor = connection.cursor()
#         query = """
#         SELECT
#             SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) BETWEEN 181 AND 300 THEN price ELSE 0 END) AS price_close_to_1_year,
#             SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) BETWEEN 31 AND 180 THEN price ELSE 0 END) AS price_above_6_months,
#             SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) <= 30 THEN price ELSE 0 END) AS price_above_1_month,
#             SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) BETWEEN 181 AND 300 THEN quantity ELSE 0 END) AS quantity_close_to_1_year,
#             SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) BETWEEN 31 AND 180 THEN quantity ELSE 0 END) AS quantity_above_6_months,
#             SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) <= 30 THEN quantity ELSE 0 END) AS quantity_above_1_month
#         FROM stock_details
#         """
#         cursor.execute(query)
#         result = cursor.fetchone()
#         series = [
#             {
#                 'name': 'Price of the Product',
#                 'data': [
#                     result[0],  # Price close to 1 year
#                     result[1],  # Price above 6 months
#                     result[2]   # Price above 1 month
#                 ]
#             },
#             {
#                 'name': 'Product Count',
#                 'data': [
#                     result[3],  # Quantity close to 1 year
#                     result[4],  # Quantity above 6 months
#                     result[5]   # Quantity above 1 month
#                 ]
#             }
#         ]
#         return jsonify({'series': series})
#     except mysql.connector.Error as e:
#         return jsonify({'error': str(e)}), 500
#     finally:
#         if cursor is not None:
#             cursor.close()
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
            SUM(CASE WHEN DATEDIFF(CURDATE(), date_added) <= 30 THEN quantity ELSE 0 END) AS quantity_above_1_month
        FROM stock_details
        """
        cursor.execute(query)
        result = cursor.fetchone()
        series = [
            {
                'name': 'Price of the Product',
                'data': [
                    result[0],  # Price close to 1 year
                    result[1],  # Price above 6 months
                    result[2]   # Price above 1 month
                ]
            },
            {
                'name': 'Product Count',
                'data': [
                    result[3],  # Quantity close to 1 year
                    result[4],  # Quantity above 6 months
                    result[5]   # Quantity above 1 month
                ]
            }
        ]
        return jsonify({'series': series})
    except mysql.connector.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor is not None:
            cursor.close()

if __name__ == '__main__':
    app.run(debug=True, host = '0.0.0.0', port=100)