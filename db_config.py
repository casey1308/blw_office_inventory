# db_config.py
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # <-- replace
        password="Uzumymw1308",  # <-- replace
        database="office_inventory"
    )
