from flask import Flask, jsonify, send_from_directory, request
import mysql.connector
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)


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

if __name__ == '__main__':
    app.run(debug=True, host = '0.0.0.0', port=100)