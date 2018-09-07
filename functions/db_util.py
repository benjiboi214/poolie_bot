import os, sys
here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(here)

from playhouse.pool import PooledPostgresqlExtDatabase

db_connection = PooledPostgresqlExtDatabase(
    os.environ['db_name'],
    user=os.environ['db_username'],
    password=os.environ['db_password'],
    host=os.environ['db_hostname'],
    port=5432,
    max_connections=3,
    stale_timeout=300
)

class DatabaseManager:
    def __init__(self):
        print("DatabaseManager: __init__ function call")
        self.connection = db_connection
    
    def __enter__(self):
        print("DatabaseManager: __enter__ function call")
        self.connection.connect()
        return self.connection
    
    def __exit__(self, type, value, traceback):
        print("DatabaseManager: __exit__ function call")
        self.connection.close()
        

def create_tables(event, context):
    print("create_tables: Receieved event - ", event)

    from models import User, Competition
    tables = [User, Competition]
    print("create_tables: Creating tables {}".format(tables))
    with DatabaseManager() as db_connection:
        db_connection.create_tables(tables)
    print("create_tables: Finished creating tables")
    return event