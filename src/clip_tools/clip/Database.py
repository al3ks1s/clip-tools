import sqlite3
import tempfile
import importlib

from collections import namedtuple

from clip_tools.utils import read_fmt

class Database:
    
    chunk_signature: str = b'CHNKSQLi'

    database_size: int

    def __init__(self, database_size, database):
        self.database_size = database_size

        self.database_file = tempfile.NamedTemporaryFile("wb")

        #print("Writing temporary SQLi database to {}".format(self.database_file.name))

        self.database_file.write(database)

        self.db_conn = sqlite3.connect(self.database_file.name)
        self.db_cursor = self.db_conn.cursor()
              
        self.table_scheme = {}

        for table in self._execute_query("Select * from sqlite_schema where type == 'table';"):
            self.table_scheme[table[1]] = [x[0].removeprefix('_') for x in self._execute_query(f"SELECT name FROM pragma_table_info('{table[1]}')")]

        param_scheme = self._execute_query("Select * from paramScheme;")
        self.param_scheme = {}
        # Row[1] is the table name
        # Row[2] is the columnt label
        for row in param_scheme:
            if row[1] not in self.param_scheme.keys():
                self.param_scheme[row[1]] = {}
            
            self.param_scheme[row[1]][row[2]] = { k:v for k,v in zip(self.table_scheme["ParamScheme"][3:], row[3:]) }
            
    def _execute_query(self, query):

        self.db_cursor.execute(query)

        return self.db_cursor.fetchall()

    def fetch_values(self, table):

        # Do not use this to fetch metadata tables like ParamScheme, ElemScheme, etc
        # Do not use this to fetch project information. It has a single row so no MainId.

        if table not in self.table_scheme:
            return None # Raise an exception?

        return self.map_results(self._execute_query(f"Select * from {table}"), table)

    def map_results(self, rows, table):
        
        mapped_values = {}

        for row in rows:
            
            mapped_row = self.row_to_object(row, table)
            mapped_values[mapped_row.MainId] = mapped_row

        return mapped_values

    def row_to_object(self, row, table):
        
        scheme = self.table_scheme[table]
        data_type = namedtuple(table, scheme)

        _module = importlib.import_module("clip_tools.clip.ClipData")
        _class = getattr(_module, table)

        mapped_row = data_type(*row)._asdict()
        del mapped_row["PW_ID"]
        
        return _class(**mapped_row)

    def edit_entry(self, table, value_dict):
        pass

    def insert_new_entry(self, table, value_dict):
        pass

    @classmethod
    def read(cls, fp):
        
        assert fp.read(8) == Database.chunk_signature

        database_size = read_fmt(">q", fp)[0]

        database = fp.read(database_size)

        return cls(database_size, database)

    def write(self, fp):
        pass


    def _scheme_to_classes(self):
        # Cursed data class writing
        # Use only if needing to regenerate a ClipData.py

        param_value_mapping = {
            1: "int",
            2: "float",
            3: "str",
            4: "bytes" 
        }

        DataString = "import attr\n\n\n"

        for table in self.param_scheme:
            
            DataString += "@attr.define\n"
            DataString += f"class {table}():\n"
            
            param_table = self.param_scheme[table]

            DataString += f"    # Class with {len(param_table)} possible columns\n"
            
            DataString += "    MainId: int = None # The param scheme doesn't necessarily have a MainId\n"

            for param in param_table:
                DataString += f"    {param}: {param_value_mapping.get(param_table[param]["DataType"])} = None\n"

            DataString += "\n\n"


        with open("ClipData.py", "w") as f:
            f.write(DataString)

        print(DataString)