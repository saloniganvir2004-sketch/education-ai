import psycopg2
import psycopg2.extras

from config import settings


def get_db_connection():

    try:
        connection = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=getattr(
                settings,
                "POSTGRES_PASSWORD",
                None
            )
        )
    except Exception as e:
        print("DATABASE CONNECTION ERROR:", e)
        raise

    connection.autocommit = False

    return connection