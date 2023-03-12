"""
Handles log file.
Once you start app previous log file is deleted.
"""
from datetime import datetime


class LogData:

    def end_program(self):
        self.write_log("************************************************************")
        current_time = datetime.now()
        formatted_date = current_time.strftime("%A, %d. %B %Y.")
        formatted_date = "Finished on " + formatted_date
        self.write_log(formatted_date)
        self.write_log("************************************************************")


    def write_log(self, data):
        log_file = open("log.txt", "a", encoding="utf-8")
        current_time = datetime.now()
        formatted_date = current_time.strftime("%H:%M - ")
        data = formatted_date + data + "\n"
        log_file.write(data)
        log_file.close

    def reset_log(self):
        log_file = open("log.txt", "w", encoding="utf-8")
        current_time = datetime.now()
        formatted_date = current_time.strftime("%A, %d. %B %Y.")
        formatted_date = "Started on " + formatted_date + "\n"
        data = ["************************************************************\n",
                "This is 'Personal Budget' log file\n",
                "Author: Danijel Nisevic (DsoftN)\n",
                "Log is deleted every time you start a new session.\n",
                "************************************************************\n",
                formatted_date,
                "************************************************************\n\n"]
        for i in data:
            log_file.write(i)
        log_file.close

    def get_current_date(self):
        current_time = datetime.now()
        formatted_date = current_time.strftime("%d.%m.%Y.")
        return formatted_date

    def get_current_time(self):
        current_time = datetime.now()
        formatted_time = current_time.strftime("%H:%M:%S")
        return formatted_time


# a = [(5,"Pet", "petica"), (1, "jedan", "jedinica"), (3,"tri","trojka")]
# print (a)
# a.sort(key = lambda x: x[0])
# print (a)
# ubaciti u bazu datum u formatu 02.02.2023. = 20230202
# sortirati po njemu, a to neka bude skriveno polje i kada
# se dobije event click umesto po datumu sortirati po ovome


