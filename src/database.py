import os
import psycopg
from dotenv import load_dotenv
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("host"),
    "port": os.getenv("port"),
    "user": os.getenv("user"),
    "password": os.getenv("password"),
    "dbname": os.getenv("dbname")
}

class Database:
    def __init__(self):
        self.schema_name = os.getenv("schema_name")

    def get_schema_details(self):
        '''Retrieve the schema representation of the database'''
        with psycopg.connect(**DB_CONFIG) as conn:
            try:
                schema = f"Schema representation for schema '{self.schema_name}':\n" # string based representation

                cursor = conn.cursor()
                cursor.execute(f"SELECT table_name \
                                FROM information_schema.tables \
                                WHERE table_schema = '{self.schema_name}'")
                tables = cursor.fetchall()
                for table in tables: # table[0] is the table name
                    table_name = table[0]
                    schema += f"Table: {table_name}\n"

                    # Add columns and their data types
                    schema += "Columns | Data Types\n"
                    cursor.execute(f"SELECT column_name, data_type  \
                                FROM information_schema.columns \
                                WHERE table_name = '{table_name}'")
                    rows = cursor.fetchall()
                    for (column, data_type) in rows:
                        schema += f"{column} | {data_type}\n"

                    # Add sample data (5 rows)
                    schema += "Sample Data:\n"
                    cursor.execute(f"SELECT * \
                                    FROM {self.schema_name}.{table_name}\
                                    LIMIT 5")
                    sample_rows = cursor.fetchall()
                    for row in sample_rows:
                        schema += f"{row}\n"
            except Exception as e:
                raise Exception(f"Error retrieving schema representation: {e}")
            finally:
                cursor.close()
        return schema

    def execute_query(self, query):
        with psycopg.connect(**DB_CONFIG) as conn:
            try:
                conn.readonly = True  # Set the connection to read-only mode
                cursor = conn.cursor()
                cursor.execute(query)
                result = cursor.fetchall()
                conn.commit()
                return str(result)
            except Exception as e:
                raise Exception(f"Error executing query: {e}")
            finally:
                cursor.close()
