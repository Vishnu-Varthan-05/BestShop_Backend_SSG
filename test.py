import mysql.connector

db_config = {
    'host': '127.0.0.1',
    'user': 'vishnu',
    'password': 'vishnu',
    'database': 'best_shop',
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

connection = get_db_connection()
cursor = connection.cursor()
cursor.execute("""
    SELECT
        SUM(msq.quantity) AS total_quantity,
        SUM(stock_details.selling_price * msq.quantity) AS total_price
    FROM
        model_size_quantity msq
    INNER JOIN stock_details USING(stock_id)
    GROUP BY
        CASE
            WHEN DATEDIFF(CURDATE(), stock_details.date_added) < 30 THEN 'less_than_30_days'
            WHEN DATEDIFF(CURDATE(), stock_details.date_added) BETWEEN 30 AND 180 THEN 'between_30_and_180_days'
            WHEN DATEDIFF(CURDATE(), stock_details.date_added) > 180 THEN 'more_than_180_days'
        END;
    """)
result = cursor.fetchall()

series = []

if len(result) > 0:
    series.append({
        'name': 'Less than 30 days',
        'data': [result[0][0], result[0][1], result[0][1] / result[0][0]]
    })

if len(result) > 1:
    series.append({
        'name': 'Between 30 to 180 days',
        'data': [result[1][0], result[1][1], result[1][1] / result[1][0]]
    })

if len(result) > 2:
    series.append({
        'name': 'More than 180 days',
        'data': [result[2][0], result[2][1], result[2][1] / result[2][0]]
    })

