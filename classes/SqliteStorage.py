import sqlite3
import re
from collections import OrderedDict

class SqliteStorage:

    def __init__(self, filename, create=False):
        if not filename.endswith(".sqlite"):
            filename = filename + ".sqlite"
        self.__connect_db(filename)
        if create:
            self.__create_sqlite_db()


    def __connect_db(self, file_name):
        # @todo change in some debug logging
        # print os.getcwd()
        self.__conn = sqlite3.connect(file_name)
        self.__conn.row_factory = self.__dict_factory
        self.__cursor = self.__conn.cursor()

    def close_db(self):
        self.__conn.close()

    def __dict_factory(self, cursor, row):
        d = OrderedDict()
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d


    def __create_sqlite_db(self):
        self.__cursor.execute("CREATE TABLE logs(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                                     "date_time TEXT, "
                                     "host_name TEXT, "
                                     "pid INTEGER, "
                                     "transid INTEGER, "
                                     "user TEXT, "
                                     "object TEXT, "
                                     "type TEXT, "
                                     "message, TEXT);")


        self.__cursor.execute("CREATE VIRTUAL TABLE messages USING FTS4 (content='logs', message TEXT);")
        self.commit_changes()

    def get_unique_users(self):
        query = "SELECT DISTINCT user FROM logs ORDER BY user"
        self.__cursor.execute(query)
        rows = self.__cursor.fetchall()
        users = []
        for row in rows:
            users.append(row['user'])

        return users

    def get_unique_objects(self):
        query = "SELECT DISTINCT object FROM logs ORDER BY object"
        self.__cursor.execute(query)
        rows = self.__cursor.fetchall()
        objects = []
        for row in rows:
            objects.append(row['object'])

        return objects

    def get_unique_types(self):
        query = "SELECT DISTINCT type FROM logs ORDER BY type"
        self.__cursor.execute(query)
        rows = self.__cursor.fetchall()
        objects = []
        for row in rows:
            objects.append(row['type'])

        return objects

    def get_unique_hostnames(self):
        query = "SELECT DISTINCT host_name FROM logs ORDER BY host_name"
        self.__cursor.execute(query)
        rows = self.__cursor.fetchall()
        host_names = []
        for row in rows:
            host_names.append(row['host_name'])

        return host_names

    def get_log_data(self, **kwargs):
        query = "SELECT strftime('%d-%m-%Y %H:%M:%f', date_time) AS date_time, host_name, pid, transid, user, object, " \
                "type, message from logs"
        params = []

        if len(kwargs.keys()) > 0:
            query += " WHERE "
            if 'first_time_stamp' in kwargs:
                params += [str(kwargs['first_time_stamp'])]
                query += "STRFTIME('%s', date_time) >= ? "
            if 'second_time_stamp' in kwargs:
                params += [str(kwargs['second_time_stamp'])]
                query += "AND STRFTIME('%s', date_time) <= ? "
            if 'host_name' in kwargs and kwargs['host_name'] != "-":
                params += [kwargs['host_name']]
                query += "AND host_name = ? "
            if 'user' in kwargs and kwargs['user'] != "-":
                params += [kwargs['user']]
                query += "AND user = ? "
            if 'object' in kwargs and kwargs['object'] != "-":
                params += [kwargs['object']]
                query += "AND object = ? "
            if 'type' in kwargs and kwargs['type'] != "-":
                params += [kwargs['type']]
                query += "AND type = ? "
            if 'full_text' in kwargs and kwargs['full_text'] != "":
                params += [kwargs['full_text']]
                query += "AND id IN (SELECT docid FROM messages WHERE message MATCH ?) "
        query += " order by date_time"
        self.__cursor.execute(query, params)

        rows = self.__cursor.fetchall()

        return rows


    def drop_indexes(self):
        drop_indexes = []
        drop_indexes.append('DROP INDEX IF EXISTS idx_date_time;')
        drop_indexes.append('DROP INDEX IF EXISTS idx_host_name;')
        drop_indexes.append('DROP INDEX IF EXISTS idx_pid;')
        drop_indexes.append('DROP INDEX IF EXISTS idx_transid;')
        drop_indexes.append('DROP INDEX IF EXISTS idx_user;')
        drop_indexes.append('DROP INDEX IF EXISTS idx_object;')
        drop_indexes.append('DROP INDEX IF EXISTS idx_type;')
        for drop_index in drop_indexes:
            self.__cursor.execute(drop_index)

        self.commit_changes()


    def create_indexes(self):
        indexes = []
        indexes.append("CREATE INDEX idx_date_time on logs (date_time);")
        indexes.append("CREATE INDEX idx_host_name on logs (host_name);")
        indexes.append("CREATE INDEX idx_pid on logs (pid);")
        indexes.append("CREATE INDEX idx_transid on logs (transid);")
        indexes.append("CREATE INDEX idx_user on logs (user);")
        indexes.append("CREATE INDEX idx_object on logs (object);")
        indexes.append("CREATE INDEX idx_type on logs (type);")

        for index in indexes:
            self.__cursor.execute(index)

        self.commit_changes()

    def update_fulltext_index(self):
        query = "INSERT INTO messages(docid, message) SELECT id, message FROM logs;"
        self.__cursor.execute(query)
        self.commit_changes()

    def drop_fulltext_index(self):
        query = "DELETE FROM messages;"
        self.__cursor.execute(query)
        self.commit_changes()


    def commit_changes(self):
        self.__conn.commit()

    def write_log_line(self, **kwargs):
        date_time = kwargs.get('date_time')
        host_name = kwargs.get('host_name')
        process_id = re.sub("[^0-9]", "", kwargs.get('process_id'))
        trans_id = re.sub("[^0-9]", "", kwargs.get('trans_id'))
        user = kwargs.get('user')
        object = kwargs.get('object')
        type = kwargs.get('type')
        msg = kwargs.get('msg')
        query = "INSERT INTO logs (date_time, host_name, pid, transid, user, object, type, message) " \
                "VALUES(?, ?, ?, ?, ?, ?, ?, ?);"
        self.__cursor.execute(query, (date_time, host_name, process_id, trans_id, user, object, type, msg))

    def getMinDateTime(self):
        query = "SELECT MIN(date_time) AS min FROM logs"
        self.__cursor.execute(query)
        rows = self.__cursor.fetchall()
        min_date_time = rows[0]['min'].split(".", 1)[0]

        return min_date_time

    def getMaxDateTime(self):
        query = "SELECT MAX(date_time) AS max FROM logs"
        self.__cursor.execute(query)
        rows = self.__cursor.fetchall()
        min_date_time = rows[0]['max'].split(".", 1)[0]

        return min_date_time
