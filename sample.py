from flask import Flask, jsonify, send_from_directory, request
import mysql.connector
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

db_config = {
    'host': '10.30.10.13',
    'user': 'bestshop',
    'password': 'bestshop',
    'database': 'best_shop',
}



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')