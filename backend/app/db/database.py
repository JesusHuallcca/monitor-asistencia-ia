import mysql.connector
from mysql.connector import Error


DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "monitor_asistencia"
}


def get_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            return connection

        return None

    except Error as error:
        raise RuntimeError(
            f"No se pudo conectar con MariaDB: {error}"
        )