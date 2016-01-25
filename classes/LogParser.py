import re
#@todo: introduce debug log (i.e. parse_line)
class LogParser:

    def __init__(self, **kwargs):
        self._storage = kwargs.get('storage')

    def __parse_line(self, line):
        m =  re.match("^\[([0-9-]+\s+[0-9:\.]+)\s+([a-zA-Z0-9-_]+)\s+([a-zA-Z0-9]+)\s+([a-zA-Z0-9]+)\s+"
                      "([a-zA-Z0-9\\\_]+)?\s+([.a-zA-Z0-9_-]+)\s+([a-zA-Z]+)\s{0,}\]\s+(.*)$", line)
        try:
            return m.groups()
        except AttributeError:
            print("Line does not match defined logging pattern!")
            print(line)
            exit()

    def parse_log_file(self, file_name):
        total = ""
        old_date_time = False
        old_object = False
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
                # new message detected, so we need to store the "old" log entry
                if (date_time != old_date_time and old_date_time != False) or (object != old_object and old_object != False):
                    self._storage.write_log_line(date_time=old_date_time, host_name=old_host_name,
                                                 process_id=old_process_id, trans_id=old_trans_id, user=old_user,
                                                 object=old_object, type=old_type, msg=total)
                    total = msg
                # continuation of existing message or first message
                else:
                    if total == "":
                        total = msg
                    else:
                        total = total + "\n" + msg
                old_date_time = date_time
                old_host_name = host_name
                old_process_id = process_id
                old_trans_id = trans_id
                old_user = user
                old_object = object
                old_type = type
            # store the last log entry as well
            self._storage.write_log_line(date_time=old_date_time, host_name=old_host_name, process_id=old_process_id,
                                         trans_id=old_trans_id, user=old_user, object=old_object, type=old_type,
                                         msg=total)