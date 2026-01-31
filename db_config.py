import pymysql

def get_db_connection():
    return pymysql.connect(
        host= 'localhost',
        port=3307,
        user="root",
        password="anshitdassdA2", 
        database="tida", # Ensure this matches your actual DB name (e.g. tida or tida6dec)
        cursorclass=pymysql.cursors.DictCursor
    )