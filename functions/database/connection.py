import os
import sys
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

class DatabaseManagerBase:
    def __init__(self):
        print("DatabaseManagerBase: __init__ function call")
        self.connection = db_connection
    
    def __enter__(self):
        print("DatabaseManagerBase: __enter__ function call")
        self.connection.connect(reuse_if_open=True)
        return self
    
    def __exit__(self, type, value, traceback):
        print("DatabaseManagerBase: __exit__ function call")
        self.connection.close()
