import sqlite3
import tempfile
import importlib

from collections import namedtuple

from clip_tools.utils import read_fmt, write_fmt, write_bytes

class Database:

    chunk_signature: str = b'CHNKSQLi'

    def __init__(self, database=None):

        if database is None:
            database = self.init_db()

        self.database_file = tempfile.NamedTemporaryFile("wb", delete=False)

        #print("Writing temporary SQLi database to {}".format(self.database_file.name))

        self.database_file.write(database)
        self.database_file.close()

        self.db_conn = sqlite3.connect(self.database_file.name)
        self.db_cursor = self.db_conn.cursor()

        self.init_scheme()

    def init_scheme(self):

        self.table_scheme = {}

        for table in self._execute_query("Select * from sqlite_schema where type == 'table';"):
            self.update_scheme(table[1])

        param_scheme = self._execute_query("Select * from paramScheme;")
        self.param_scheme = {}
        # Row[1] is the table name
        # Row[2] is the columnt label
        for row in param_scheme:
            if row[1] not in self.param_scheme.keys():
                self.param_scheme[row[1]] = {}

            self.param_scheme[row[1]][row[2]] = dict(zip(self.table_scheme["ParamScheme"][3:], row[3:]))

    def update_scheme(self, table):
        self.table_scheme[table] = [
            x[0].removeprefix('_')
            for x in self._execute_query(f"SELECT name FROM pragma_table_info('{table}')")
        ]

    def init_db(self):

        return b''

    def _execute_query(self, query):

        self.db_cursor.execute(query)
        return self.db_cursor.fetchall()

    def get_free_main_id(self, table):
        return self._execute_query(f"select max(MainId) from {table}")[0][0] + 1

    def get_free_pw_id(self, table):
        free_id = self._execute_query(f"select max(_PW_ID) from {table}")[0][0]
        if free_id is None:
            return 1
        else:
            return free_id + 1

    def fetch_project_data(self):
        return self._row_to_object(self._execute_query(f"Select * from Project")[0], "Project")

    def get_table(self, table):

        # Do not use this to fetch metadata tables like ParamScheme, ElemScheme, etc
        # Do not use this to fetch project information. It has a single row so no MainId.

        if table not in self.table_scheme:
            return None # Raise an exception

        return self._map_results(self._execute_query(f"Select * from {table}"), table)

    def get_referenced_items(self, table, column, value):

        if table not in self.table_scheme:
            return None # Raise an exception

        return self._map_results(
            self._execute_query(f"Select * from {table} where {column}=={value}"),
            table
        )

    def edit_entry(self, table, value_dict):

        query = f"""UPDATE {table} SET
                {", ".join([f"{x[0]} = ?" for x in self._execute_query(f"SELECT name FROM pragma_table_info('{table}')")])}
                WHERE _PW_ID = ?;
                """

        values = list(value_dict.values())
        values.append(value_dict["PW_ID"])

        self.db_cursor.execute(query, tuple(values))
        self.db_conn.commit()

    def insert_new_entry(self, table, value_dict):

        query = f"""INSERT INTO {table}
                ({", ".join([x[0] for x in self._execute_query(f"SELECT name FROM pragma_table_info('{table}')")])})
                VALUES ({", ".join(["?" for _ in range(len(value_dict))])});
                """

        if value_dict["PW_ID"] == -1:
            value_dict["PW_ID"] = self.get_free_pw_id(table)

        self.db_cursor.execute(query, tuple(value_dict.values()))
        self.db_conn.commit()

        return value_dict["PW_ID"]

    def create_table(self, table):
        query = f"CREATE TABLE {table} (_PW_ID INTEGER PRIMARY KEY)"
        self.db_cursor.execute(query)
        self.update_scheme(table)

    def alter_table(self, table, new_columns):

        query = f"""BEGIN TRANSACTION; 
                    {"; ".join([f"ALTER TABLE {table} ADD {new_column}" for new_column in new_columns])};
                    COMMIT;"""

        self.db_cursor.executescript(query)
        self.update_scheme(table)

    def _map_results(self, rows, table):
        mapped_values = {}

        for row in rows:

            mapped_row = self._row_to_object(row, table)
            mapped_values[mapped_row.MainId] = mapped_row

        return mapped_values

    def _row_to_object(self, row, table):

        scheme = self.table_scheme[table]
        data_type = namedtuple(table, scheme)

        _module = importlib.import_module("clip_tools.clip.ClipData")
        _class = getattr(_module, table)

        mapped_row = data_type(*row)._asdict()
        #del mapped_row["PW_ID"]

        return _class(**mapped_row)

    @classmethod
    def new(cls):
        pass

    @classmethod
    def read(cls, fp):

        assert fp.read(8) == Database.chunk_signature

        database_size = read_fmt(">q", fp)
        database = fp.read(database_size)

        return cls(database)

    def write(self, fp):

        fp.write(Database.chunk_signature)

        offset = fp.tell()
        write_fmt(fp, ">q", 0)

        self.db_cursor.close()
        self.db_conn.close()

        with open(self.database_file.name, "rb") as db_file:
            written = write_bytes(fp, db_file.read())
        
        fp.seek(offset)
        write_fmt(fp, ">q", written)

        fp.seek(0, 2)

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