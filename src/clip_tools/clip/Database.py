import sqlite3
import tempfile

from clip_tools.utils import read_fmt

class Database:
    
    chunk_signature: str = b'CHNKSQLi'

    database_size: int

    def __init__(self, database_size, database):
        self.database_size = database_size

        self.database_file = tempfile.NamedTemporaryFile("wb")

        print("Writing temporary SQLi database to {}".format(self.database_file.name))

        self.database_file.write(database)

        self.db_conn = sqlite3.connect(self.database_file.name)
        self.db_cursor = self.db_conn.cursor()

    def execute_query(self, query):
        return self.db_cursor.execute(query)

    @classmethod
    def read(cls, fp):
        
        assert fp.read(8) == Database.chunk_signature

        database_size = read_fmt(">q", fp)[0]

        database = fp.read(database_size)

        return cls(database_size, database)

        