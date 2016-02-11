import re

class LogParser:

    failed_log_lines = []

    def __init__(self, **kwargs):
        self._storage = kwargs.get('storage')

    def __parse_line(self, line):
        # ^\[([0-9-]+\s+[0-9:\.]+)\s+ date
        # ([a-zA-Z0-9-_]+)\s+ hostname
        # ([a-zA-Z0-9]+)\s+ process id
        # ([a-zA-Z0-9]+)\s+ transaction id -end of first line regex-
        # ([.a-zA-Z0-9_-`]+)\s+ class/page that generates the error
        # ([a-zA-Z]+)\s{0,}\]\s+ type of error
        # (.*)$ message
        # we will do it in multiple times, username is optional and can contain spaces, so there is no easy way
        # to do it in one regex. Matching everything except the user, the stuff that isn't matched is either empty or
        # it is the user name
        m =  re.match("^\[([0-9-]+\s+[0-9:\.]+)\s+([a-zA-Z0-9-_]+)\s+([a-zA-Z0-9]+)\s+([a-zA-Z0-9]+)\s+", line)
        m2 = re.search("([.a-zA-Z0-9_-`]+)\s+([a-zA-Z]+)\s{0,}\]\s+(.*)$", line)
        try:
            first_end = m.end()
            second_start = m2.start()
            # user is optional as well, so can be an empty string
            user = line[first_end:second_start].strip()
            return m.groups() + (user,) + m2.groups()
        except:
            self.failed_log_lines.append(line)

            return False

    def has_failed_log_entries(self):
        if len(self.failed_log_lines) > 0:
            return True
        else:
            return False

    def get_failed_lag_entries(self):
        return self.failed_log_lines

    def parse_log_file(self, file_name):
        total = ""
        old_date_time = False
        old_object = False
        with open(file_name, encoding="utf-8") as file:
            did_loop = False
            for idx, line in enumerate(file):
                tup = self.__parse_line(line)
                if tup:
                    did_loop = True
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
            if did_loop:
                # store the last log entry as well
                self._storage.write_log_line(date_time=old_date_time, host_name=old_host_name, process_id=old_process_id,
                                             trans_id=old_trans_id, user=old_user, object=old_object, type=old_type,
                                             msg=total)