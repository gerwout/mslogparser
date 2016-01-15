import re
from classes.SqliteStorage import SqliteStorage

#@todo: should select on time of event
#@todo: ability to parse multiple log files at the same point in time
#@todo: full text search should not be fuzzy
#@todo: add ability to export 1 or more messages
#@todo: show message dialog after clicking
#@todo: add trans and process id

class LogParser:

    __startList = []
    __endList = []
    __dropList = []
    # no other storage yet, just a placeholder in case we meed another one
    __storage = "sqlite"

    def __init__(self):
        self.__dropList.append("END OF LIST")
        self.__startList.append("CALL STACK OF EXCEPTION")
        self.__endList.append("END OF CALL STACK")
        self.__startList.append("CALL STACK OF CURRENT THREAD")
        self.__endList.append("END OF CALL STACK")
        self.__startList.append("ASP.NET CONTEXT")
        self.__endList.append("END OF ASP.NET CONTEXT")
        self.__startList.append("BROWSER CAPABILITIES")
        self.__endList.append("END OF BROWSER CAPABILITIES")
        self.__startList.append("BEGIN HISTORY DUMP")
        self.__endList.append("END OF HISTORY DUMP")

    # @todo: should not exit, put throw something in and log to some debug log
    def __parse_line(self, line):
        m =  re.match("^\[([0-9-]+\s+[0-9:\.]+)\s+([a-zA-Z0-9-_]+)\s+([a-zA-Z0-9]+)\s+([a-zA-Z0-9]+)\s+"
                      "([a-zA-Z0-9\\\]+)\s+([a-zA-Z0-9_-]+)\s+([a-zA-Z]+)\s+\]\s+(.*)$", line)
        try:
            return m.groups()
        except:
            print (line)
            exit()

    def parse_log_file(self, file_name):
        if self.__storage == "sqlite":
            storage = SqliteStorage(file_name, create=True)
        with open(file_name) as file:
            for idx, line in enumerate(file):
                tup = self.__parse_line(line)
                date_time = tup[0]
                host_name = tup[1]
                process_id = tup[2]
                trans_id = tup[3]
                user = tup[4]
                object = tup[5]
                type = tup[6]
                msg = tup[7]
                # if it is in the ignore list, drop the log entry
                if msg.startswith(tuple(self.__dropList)):
                    start_detected = False
                    end_detected = False
                    multi_line = False
                    continue
                # start of multi line message
                elif msg.startswith(tuple(self.__startList)):
                    start_detected = True
                    end_detected = False
                    multi_line = True
                    total = msg
                # end of multiline message
                elif msg.startswith(tuple(self.__endList)):
                    end_detected = True
                    start_detected = False
                    multi_line = False
                    total = total + "\n" + msg
                    storage.write_log_line(date_time=date_time, host_name=host_name, process_id=process_id,
                                               trans_id=trans_id, user=user, object=object, type=type, msg=total)
                    total = ""
                # single line message or continuation of multi line message
                else:
                    start_detected = False
                    end_detected = False
                    # single line message
                    if not 'multi_line' in locals() or ('multi_line' in locals() and not multi_line):
                        storage.write_log_line(date_time=date_time, host_name=host_name, process_id=process_id,
                                               trans_id=trans_id, user=user, object=object, type=type, msg=msg)
                    else:
                        total = total + "\n" + msg
        if self.__storage == "sqlite":
            storage.update_fulltext_index()
            storage.create_indexes()
            storage.close_db()
