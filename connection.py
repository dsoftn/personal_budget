"""
Danijel Nisevic @DsoftN, 22.01.2023.
"""
import uuid  # Provides computer lan MAC adress
import platform  # Provides computer info
import sqlite3
import os
from PyQt5.QtCore import QDateTime
import random
import log_cls
import datetime


class UserDatabaseConection():
    """Makes connection to User database, 3 type of connection:
    1. SQLite database
    2. MySQL local database
    3. MySQL remote database"""
    def __init__(self, user_id):
        self.active_user_id = user_id
        self.conn = ConnStart()
        self.user_database = self.conn.get_databases(self.active_user_id)
        
    def get_connection(self):
        if self.user_database[0][3] == "SQLite":
            db_path = self.user_database[0][2] + self.user_database[0][1]
            result = sqlite3.connect(db_path)
        return result


class ConnStart:
    """"Makes connection to 'start_up.db' database.
    This database contains info about users, settings and languages.
    """

    def __init__(self):
        """ Connection to database 'start_up.db'"""
        self.log = log_cls.LogData()
        start_up_file = self._add_path("start_up.db")
        self.active_lang = 0
        if os.path.exists(start_up_file):
            self.conn = sqlite3.connect(start_up_file)
            self.cur = self.conn.cursor()
            self.isConnected = True
        else:
            raise FileNotFoundError("File not found: 'start_up.db'.")
    
    def __del__(self):
        self.conn.close()
    
    def is_decimal(self, string_to_check):
        a = string_to_check
        try:
            b = float(a)
        except:
            return False
        else:
            return True

    def lang(self, information_id, jezik_id=0):
        """Accepts a string argument with a variable name
         and returns its value (string) for the active language.
         Optional 'jezik_id' : If omitted, last use or last_user will be selected.
         """
        if jezik_id == 0:
            if self.active_lang == 0:
                jezik_id = self.user_language(self.get_setting_data("last_user", getParametar=True))
            else:
                jezik_id = self.active_lang
        
        self.cur.execute(f"SELECT vrednost FROM interfejs WHERE interfejs.podatak = '{information_id}' AND interfejs.jezik_id = {jezik_id} ;")
        result = self.cur.fetchall()
        if len(result) == 0:
            self.log.write_log("Error. MODULE: connection.lang  TABLE: start_up.interfejs.podatak not found.")
            return ""
        else:
            return result[0][0]

    def user_language(self, user_id, searchByUsername=""):
        """Returns interface language (integer) for selected user_id(integer).
        If 'searchByUsername'(string) is set then 'user_id' is neglected.
        """
        if len(searchByUsername) > 0:
            self.cur.execute(f"SELECT jezik_id FROM user WHERE username = '{searchByUsername}';")
        else:
            self.cur.execute(f"SELECT jezik_id FROM user WHERE user_id = '{user_id}';")
        
        result = self.cur.fetchall()
        if len(result) > 0:
            self.active_lang = result[0][0]
            return result[0][0]
        else:
            self.log.write_log("Error. MODULE: connection.user_language  TABLE: start_up.jezik_id not found.")
            return 1
    
    def get_setting_data(self, functionData, getParametar=False, user_id=0):
        """Returns setting value (string) for selected 'functionData'.
        Optional getParametar if true returns integer value for 'funcData'
        """
        query = f"SELECT vrednost, parametar FROM podesavanje WHERE funkcija = '{functionData}'"
        if user_id == 0:
            query = query + ";"
        else:
            query = query + " AND user_id = " + str(user_id) + ";"
        self.cur.execute(query)
        result = self.cur.fetchall()
        if len(result) == 0:
            self.log.write_log("Fatal Error. MODULE: connection.get_setting_data  TABLE: start_up.podesavanje.funkcija not found.")
        if getParametar:
            return result[0][1]
        else:
            return result[0][0]

    def set_setting_data(self, functionData, value, parametar=0, user_id=0):
        # Writes setting to table 'podesavanje'
        self.cur.execute(f"SELECT podesavanje_id FROM podesavanje WHERE funkcija = '{functionData}' AND user_id = {str(user_id)};")
        result = self.cur.fetchall()
        datum = self.get_current_date()
        if user_id == 0:
            user_name = "System."
        else:
            user_name = self._get_user_name(user_id)
        
        if len(result) == 0:
            self.log.write_log(f"Error. MODULE: set_setting_data. Record '{functionData}' not found. Creating new record. User: {user_name}")
            self.cur.execute(f"INSERT INTO podesavanje(funkcija, vrednost, parametar, datum, opis, user_id) VALUES ('{functionData}', '{value}', 0, '{datum}', '', 0);")
        else:
            self.log.write_log(f"Setting. Function {functionData} update value to {value}, param: {parametar}  User: {user_name}")
            query = f"UPDATE podesavanje SET vrednost = '{value}', parametar = {parametar}, datum = '{datum}' WHERE funkcija = '{functionData}'"
            if user_id == 0:
                query = query + ";"
            else:
                query = query + " AND user_id = " + str(user_id) + ";"
            self.cur.execute(query)
        self.conn.commit()

    def get_current_date(self, get_date_and_time=False, get_time_only=False):
        datum = QDateTime.currentDateTime()
        datum = datum.toString("dd.MM.yyyy. hh:mm:ss")
        c_time = datum[datum.find(" ")+1:]
        c_datum = datum[:datum.find(" ")]
        c_date_time = c_datum + " " + c_time
        if get_date_and_time:
            result = c_date_time
        elif get_time_only:
            result = c_time
        else:
            result = c_datum
        return result
    
    def set_last_user(self, user_id):
        datum = self.get_current_date()
        user_name = self._get_user_name(user_id)
        self.cur.execute(f"UPDATE podesavanje SET vrednost = '{user_name}', parametar = {user_id}, datum = '{datum}' WHERE funkcija = 'last_user';")
        if self.cur.rowcount == 1:
            self.conn.commit()
            return ""
        else:
            self.conn.rollback()
            self.log.write_log("Error. MODULE: connection.set_last_user  TABLE: start_up.podesavanje. Unexpected error. Unable to update table 'podesavanje'")
            return "Unexpected error. Unable to update table 'podesavanje'"

    def is_valid_username(self, username):
        """ Checks username for special char, returns (boolean, string).
        Return (True, "") or (False, Error)
        """
        result = []
        allowed = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890_-."
        if username == "":
            result.append([False, self.lang("login_lbl_new_warning6")])
            return result
        if username[0] not in "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM":
            result.append([False, self.lang("login_lbl_new_warning1")])
            return result
        for i in username:
            if i not in allowed:
                result.append([False, self.lang("login_lbl_new_warning2")])
                return result
        result.append([True, ""])
        return result

    def add_new_user(self, username, password):
        password_enc = self._encrypt_user_password(password)
        file_name = ""
        for i in username:
            if i in "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890":
                file_name = file_name + i
        if file_name == "":
            file_name = "user"
        file_name_sys = file_name + ".db"
        n = 0
        while True:
            if os.path.exists(file_name_sys):
                n += 1
                file_name = file_name + str(n)
                file_name_sys = file_name + ".db"
            else:
                break
        base_conn = sqlite3.connect(file_name_sys)
        base_cur = base_conn.cursor()
        sql_file = open ("cdb.budget", "r", encoding="utf-8")
        for i in sql_file:
            sql_command = i.strip()
            if  sql_command[:2] != "--":
                base_cur.execute(sql_command)
        sql_file.close
        base_conn.commit()
        base_conn.close()
        self.log.write_log(f"Created new database: {file_name_sys}")
        datum = self.get_current_date()
        self.cur.execute(f"INSERT INTO baza(name, path, type, username, password) VALUES ('{file_name_sys}', '', 'SQLite', '', '');")
        baza_id = self.cur.lastrowid
        self.conn.commit()
        if self.active_lang == 0:
            jezik_id = 1
        else:
            jezik_id = self.active_lang
        
        self.cur.execute(f"INSERT INTO user(username, password, baza_id, ime, prezime, adresa, email, telefon, opis, jezik_id, datum) VALUES ('{username}', '{password_enc}', '{baza_id}', '', '', '', '', '', '', '{jezik_id}', '{datum}');")
        self.conn.commit()
        # Add data in 'podesavanje' for new user
        self.log.write_log("Creating new user environment...")
        user_id = self._get_user_id(username)
        s = [
            ("main_x", "Main Window X pos", 264, datum, "Geometrija glavnog prozora", user_id),
            ("main_y", "Main Window Y pos", 72, datum, "Geometrija glavnog prozora", user_id),
            ("main_w", "Main Window WIDTH", 1041, datum, "Geometrija glavnog prozora", user_id),
            ("main_h", "Main Window HEIGHT", 619, datum, "Geometrija glavnog prozora", user_id),
            ("main_full_screen", "Full Screen", 0, datum, "Geometrija glavnog prozora", user_id),
            ("user_creation_date", datum, 0, datum, "Datum kada je user kreiran", user_id),
            ("main_tbl_header_width0", "Sirina kolona u tabeli", 125, datum, "Datum", user_id),
            ("main_tbl_header_width1", "Sirina kolona u tabeli", 125, datum, "Prihod RSD", user_id),
            ("main_tbl_header_width2", "Sirina kolona u tabeli", 125, datum, "Rashod RSD", user_id),
            ("main_tbl_header_width3", "Sirina kolona u tabeli", 125, datum, "Prihod EUR", user_id),
            ("main_tbl_header_width4", "Sirina kolona u tabeli", 125, datum, "Rashod EUR", user_id),
            ("main_tbl_header_width5", "Sirina kolona u tabeli", 125, datum, "Vrsta dogadjaja", user_id),
            ("main_tbl_header_width6", "Sirina kolona u tabeli", 125, datum, "Opis", user_id),
            ("main_tbl_header_width7", "Sirina kolona u tabeli", 125, datum, "Partner", user_id),
            ("main_tbl_header_width8", "Sirina kolona u tabeli", 125, datum, "Mesto", user_id),
            ("main_filter_cmb_column", "Current index", 0, datum, "ComboBox na glavnom prozoru u frejmu filter - kolone", user_id),
            ("main_filter_cmb_operand", "Current index", 0, datum, "ComboBox na glavnom prozoru u frejmu filter - operandi", user_id),
            ("add_event_cmb_event_type", "Current index", 0, datum, "Add event, cmb_event_type, current item", user_id),
            ("add_event_cmb_places", "Current index", 0, datum, "Add event, cmb_places, current item", user_id),
            ("kurs", "EUR->RSD", 0, datum, "Kurs zamene EUR u RSD", user_id),
            ("add.event_cmb_partner", "Current index", 0, datum, "Add event, cmb_partner, current item", user_id),
            ("report_tbl_header_width0", "Sirina kolona u tabeli", 125, datum, "Default", user_id),
            ("report_tbl_header_width1", "Sirina kolona u tabeli", 125, datum, "Default", user_id),
            ("report_tbl_header_width2", "Sirina kolona u tabeli", 125, datum, "Default", user_id),
            ("report_tbl_header_width3", "Sirina kolona u tabeli", 125, datum, "Default", user_id),
            ("report_tbl_header_width4", "Sirina kolona u tabeli", 125, datum, "Default", user_id),
            ("report_tbl_header_width5", "Sirina kolona u tabeli", 125, datum, "Default", user_id),
            ("report_tbl_header_width6", "Sirina kolona u tabeli", 125, datum, "Default", user_id),
            ("report_tbl_header_width7", "Sirina kolona u tabeli", 125, datum, "Default", user_id),
            ("report_tbl_header_width8", "Sirina kolona u tabeli", 125, datum, "Default", user_id),
            ("report_tbl_header_width9", "Sirina kolona u tabeli", 125, datum, "Default", user_id),
            ("report_x", "Report Window X pos", 125, datum, "Geometrija report prozora", user_id),
            ("report_y", "Report Window Y pos", 125, datum, "Geometrija report prozora", user_id),
            ("report_w", "Report Window WIDTH", 824, datum, "Geometrija report prozora", user_id),
            ("report_h", "Report Window HEIGHT", 513, datum, "Geometrija report prozora", user_id),
            ("report_tree_indent_val", "Value for tree view indent", 30, datum, "Value for tree view indent", user_id),
            ("report_tree_indent_max", "Max value for tree view indent", 100, datum, "Max value for tree view indent", user_id),
            ("report_tree_cmb_tree_show", "ComboBox", 0, datum, "Index value for cmb_tree_show", user_id),
            ("report_tree_tbl_tree_col_width0", "Table column width", 150, datum, "Report table column width, tree view", user_id),
            ("report_tree_tbl_tree_col_width1", "Table column width", 450, datum, "Report table column width, tree view", user_id),
            ("report_tree_indent_char", ".", 0, datum, "Indent character", user_id),
            ("web_add_win_x", "Add Web, Window geometry", 100, datum, "Add Web, Window geometry", user_id),
            ("web_add_win_y", "Add Web, Window geometry", 100, datum, "Add Web, Window geometry", user_id),
            ("web_add_win_w", "Add Web, Window geometry", 800, datum, "Add Web, Window geometry", user_id),
            ("web_add_win_h", "Add Web, Window geometry", 380, datum, "Add Web, Window geometry", user_id),
            ("web_win_x", "Web, Window geometry", 100, datum, "Web, Window geometry", user_id),
            ("web_win_y", "Web, Window geometry", 100, datum, "Web, Window geometry", user_id),
            ("web_win_w", "Web, Window geometry", 1060, datum, "Web, Window geometry", user_id),
            ("web_win_h", "Web, Window geometry", 430, datum, "Web, Window geometry", user_id),
            ("wallet_win_x", "Wallet, Window geometry", 100, datum, "Wallet, Window geometry", user_id),
            ("wallet_win_y", "Wallet, Window geometry", 100, datum, "Wallet, Window geometry", user_id),
            ("wallet_win_w", "Wallet, Window geometry", 1040, datum, "Wallet, Window geometry", user_id),
            ("wallet_win_h", "Wallet, Window geometry", 450, datum, "Wallet, Window geometry", user_id),
            ("wallet_btn_total_state", "Total RSD", 0, datum, "Wallet, btn_total state", user_id),
            ("wallet_delimiter_pos_x", "Delimiter", 250, datum, "Wallet, delimiter line", user_id),
            ("wallet_add_win_x", "Wallet add, Window geometry", 100, datum, "Wallet add, Window geometry", user_id),
            ("wallet_add_win_y", "Wallet add, Window geometry", 100, datum, "Wallet add, Window geometry", user_id),
            ("wallet_add_win_w", "Wallet add, Window geometry", 550, datum, "Wallet add, Window geometry", user_id),
            ("wallet_add_win_h", "Wallet add, Window geometry", 330, datum, "Wallet add, Window geometry", user_id),
            ("wallet_transfer_vrsta_id", "Wallet transfer", 0, datum, "Wallet transfer vrsta_id", user_id),
            ("wallet_transfer_mesto_id", "Wallet transfer", 0, datum, "Wallet transfer mesto_id", user_id),
            ("chart_container_win_x", "Chart container, Window geometry", 100, datum, "Chart container, Window geometry", user_id),
            ("chart_container_win_y", "Chart container, Window geometry", 100, datum, "Chart container, Window geometry", user_id),
            ("chart_container_win_w", "Chart container, Window geometry", 500, datum, "Chart container, Window geometry", user_id),
            ("chart_container_win_h", "Chart container, Window geometry", 400, datum, "Chart container, Window geometry", user_id)
            ]
        for i in s:
            qry = f"INSERT INTO podesavanje(funkcija, vrednost, parametar, datum, opis, user_id) VALUES ('{i[0]}', '{i[1]}', {i[2]}, '{i[3]}', '{i[4]}', {i[5]}) ;"
            self.cur.execute(qry)
        self.conn.commit()
        self.log.write_log(f"Created new user: {username}")
        return True

    def get_users_all(self, user_id=0):
        # Returns all users and users data as a list.
        if user_id == 0:
            q = "SELECT * FROM user ;"
        else:
            q = f"SELECT * FROM user WHERE user_id = {user_id} ;"

        self.cur.execute(q)
        return self.cur.fetchall()

    def get_language_all(self):
        q = "SELECT * FROM jezik ;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        return result

    def set_user(self, user_id, user_object):
        o = user_object
        q = f"""
            UPDATE user
            SET 
                password = '{o["password"]}',
                baza_id  = {o["baza_id"]},
                ime = ?,
                prezime = ?,
                adresa = ?,
                email = ?,
                telefon = ?,
                opis = ?,
                jezik_id = {o["jezik_id"]},
                datum = '{o["datum"]}'
            WHERE
                user_id = {user_id}
            ;
        """
        self.cur.execute(q, (o["ime"], o["prezime"], o["adresa"], o["email"], o["telefon"], o["opis"]))
        self.conn.commit()
        self.log.write_log("User data changed !")

    def set_user_password(self, user_id, new_password):
        psw = self._encrypt_user_password(new_password)
        q = f"UPDATE user SET password = '{psw}' WHERE user_id = {user_id} ;"
        self.cur.execute(q)
        self.conn.commit()
        self.log.write_log("User password changed !")

    def _get_user_name(self, user_id_to_name):
        # Returns user_name as string.
        users = self.get_users_all()
        for i in users:
            if i[0] == user_id_to_name:
                return i[1]
        return ""

    def _get_user_id(self, user_name_to_id):
        # Returns user_id as integer.
        users = self.get_users_all()
        for i in users:
            if i[1] == user_name_to_id:
                return i[0]
        return ""

    def check_user_password(self, user_id, user_password, user_name=""):
        """ Checks if username and password match. 
        Optional user_name, if omitted user_id will be used.
        Returns boolean.
        """
        if user_name != "":
            user_id = self._get_user_id(user_name)
        users = self.get_users_all()
        for i in users:
            if i[0] == user_id:
                if self._encrypt_user_password(user_password) == i[2]:
                    return True
                else:
                    return False
        
    def _encrypt_user_password(self, passwordText):
        # Returns encrypted string representing given password text.
        enc = ""
        ascii_code = ""
        random.seed(29)
        for i in passwordText:
            ascii_code = str(ord(i))
            if len(ascii_code) < 3:
                ascii_code = "0" + ascii_code
            enc = enc + ascii_code + str(random.randint(10000, 99999))
        return enc
    
    def _decrypt_user_password(self, encryptedPassword):
        # Returns password text (string) for given encrypted password.
        if (len(encryptedPassword) % 8) != 0:
            self.log.write_log("Error. Pasword Decryption. MODULE: connection._decrypt_user_password. LEN mismatch.")
            return ""
        result = ""
        n = ""
        for i in range(0,len(encryptedPassword), 8):
            n = encryptedPassword[i:i+8]
            result = result + chr(int(n[:3]))
        return result

    def _add_path(self, file_name):
        # Returns the absolute path to working directory and adds file_name.
        a = os.path.abspath(os.getcwd())
        c = r" \ "
        c = c.strip()
        a = a + c + file_name
        return a

    def get_user_database_name(self, user_id):
        query = f"SELECT baza.name, baza.path FROM baza, user WHERE user.baza_id = baza.baza_id AND user.user_id = {str(user_id)};"
        self.cur.execute(query)
        result = self.cur.fetchall()
        if len(result) != 1:
            self.log.write_log("Error. MODULE: get_user_database_name   Query result <> 1  Open user database failed.")
            return ""
        else:
            db_name = result[0][0]
            db_path = result[0][1]
            db_path.strip()
            if db_path == "":
                return db_name
            else:
                return db_path

    def get_databases(self, user_id=0):
        q = "SELECT * FROM baza "
        if user_id != "":
            qq = f"SELECT username, baza_id FROM user WHERE user_id = {str(user_id)} ;"
            self.cur.execute(qq)
            baze = self.cur.fetchall()
            q = q + f"WHERE baza_id = {str(baze[0][1])} ;"
        else:
            q = q + ";"
        self.cur.execute(q)
        result = self.cur.fetchall()
        return result

    def date_to_integer(self, date_str):
        datum = date_str
        if len(datum) < 10:
            return 0
        d = int(datum[:2])
        m = int(datum[3:5])
        y = int(datum[6:10])
        if d < 10:
            dd = "0" + str(d)
        else:
            dd = str(d)
        if m < 10:
            mm = "0" + str(m)
        else:
            mm = str(m)

        datum = str(y) + mm + dd
        return int(datum)

    def is_date_valid(self, datum):
        if len(datum) < 10:
            return False
        try:
            d = int(datum[:2])
            m = int(datum[3:5])
            y = int(datum[6:10])
        except:
            return False
        if d < 10:
            dd = "0" + str(d)
        else:
            dd = str(d)
        if m < 10:
            mm = "0" + str(m)
        else:
            mm = str(m)

        datum = str(y) + mm + dd
        if int(datum) < 19000000:
            return False
        return True
        

class User:

    def __init__(self, user_id):
        """ Connection to user's database"""
        self.log = log_cls.LogData()
        self.start_base = ConnStart()
        self.user_database = self.start_base.get_user_database_name(user_id)
        if self.user_database == "":
            self.log.write_log(f"Fatal Error. User - Database relation is not unique or does not exists !  User_id {user_id}")
            raise "User - Database relation is not unique or does not exists !"
        if os.path.exists(self.user_database) is not True:
            self.log.write_log(f"Fatal Error. User's Database does not exists !  User_id {user_id}")
            raise "User's Database does not exists !"
        self.active_lang = self.start_base.user_language(user_id)
        self.user_id = user_id
        self.user_name = self.start_base._get_user_name(user_id)
        user_database = UserDatabaseConection(self.user_id)
        self.conn = user_database.get_connection()
        self.cur = self.conn.cursor()
        self.isConnected = True

    def _get_uredjaj_id(self):
        b = uuid.getnode()
        if b == None:
            c_mac = ""
        else:
            c_mac = str(b)
        a = platform.uname()
        naziv = a[1]
        opis = a[0] + " " + a[2] + " ver(" + a[3] + "), CPU: " + a[4] + ", " + a[5]
        if naziv == None:
            naziv = ""
        if opis == None:
            opis = ""
        
        q = f"SELECT * FROM uredjaj WHERE id = '{c_mac}';"
        self.cur.execute(q)
        result = self.cur.fetchall()
        if len(result) == 0:
            q = f"INSERT INTO uredjaj(naziv, id, tip, opis) VALUES (?, '{c_mac}', '', ?) ;"
            self.cur.execute(q, (naziv, opis))
            self.conn.commit()

        q = f"SELECT * FROM uredjaj WHERE id = '{c_mac}';"
        self.cur.execute(q)
        result = self.cur.fetchall()
        return result[0][0]

    def __del__(self):
        self.conn.close()

    def get_event_all(self):
        q = "SELECT * FROM trosak WHERE trosak.wallet_id = 0;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        return result
    
    def get_event_id_all(self):
        q = "SELECT trosak_id FROM trosak WHERE trosak.wallet_id = 0 ;"
        self.cur.execute(q)
        a = self.cur.fetchall()
        result = []
        for i in a:
            result.append(a[i][0])
        return result
        
    def get_filter_data(self, group_by):
        # Select group method and define SQL command
        if group_by == "event_type":
            q = self._get_SQL_group_event_type()
        elif group_by == "partner":
            q = self._get_SQL_group_parter()
        elif group_by == "description":
            q = self._get_SQL_group_description()
        elif group_by == "place":
            q = self._get_SQL_group_place()
        elif group_by == "days":
            q = self._get_SQL_group_days()
        elif group_by == "weeks":
            q = self._get_SQL_group_weeks()
        elif group_by == "months":
            q = self._get_SQL_group_months()
        elif group_by == "years":
            q = self._get_SQL_group_years()
        else:
            q = self._get_SQL_group_none()

        # Get data
        self.cur.execute(q)
        result = self.cur.fetchall()
        return result

    def get_filter_details_data(self, group, events_list, index_n):
        q = """
            SELECT
                trosak_id,
                datum,
                prihod_rsd,
                rashod_rsd,
                prihod_eur,
                rashod_eur,
                vrsta_naziv,
                partner,
                mesto_naziv,
                opis,
                kurs
            FROM 
                filter_data
            WHERE 

        """
        if group == "":
            return
        elif group == "days":
            datum = events_list[index_n][9]
            q = q + "datum = '" + datum + "' ;"
        elif group == "weeks":
            week = events_list[index_n][9]
            year = events_list[index_n][10]
            q = q + "nedelja = " + str(week) + " AND godina = " + str(year) + " ORDER BY datum_int ;"
        elif group == "months":
            month = events_list[index_n][9]
            year = events_list[index_n][10]
            q = q + "mesec_broj = " + str(month) + " AND godina = " + str(year) + " ORDER BY datum_int ;"
        elif group == "years":
            year = events_list[index_n][9]
            q = q + "godina = " + str(year) + " ORDER BY datum_int ;"

        if q.find(";") > 0:
            self.cur.execute(q)
            result = self.cur.fetchall()
            return result
        
        if group == "event_type":
            data_to_filter = events_list[index_n][9]
            q = q + "vrsta_naziv = ? ORDER BY datum_int ;"
        elif group == "place":
            data_to_filter = events_list[index_n][9]
            q = q + "mesto_naziv = ? ORDER BY datum_int ;"
        elif group == "partner":
            data_to_filter = events_list[index_n][9]
            q = q + "partner = ? ORDER BY datum_int ;"
        elif group == "description":
            data_to_filter = events_list[index_n][9]
            q = q + "opis = ? ORDER BY datum_int ;"
        self.cur.execute(q, (data_to_filter,))
        result = self.cur.fetchall()
        return result

    def _get_SQL_group_weeks(self):
        a = self.start_base.lang("report_filter_data_by_weeks", self.active_lang)
        q = f"""
        SELECT
            COUNT(trosak_id),
            '{a}'||nedelja||' ('||godina||')',
            SUM(prihod_rsd),
            SUM(rashod_rsd),
            (SUM(prihod_rsd) - SUM(rashod_rsd)),
            SUM(prihod_eur),
            SUM(rashod_eur),
            (SUM(prihod_eur)-  SUM(rashod_eur)),
            ((SUM(prihod_rsd) - SUM(rashod_rsd)) + (SUM(prihod_eur)-  SUM(rashod_eur)) * kurs),
            nedelja,
            godina
        FROM
            filter_data
        GROUP BY
            godina, nedelja
        ORDER BY
            godina, nedelja
            ;
        """
        return q

    def _get_SQL_group_months(self):
        a = self.start_base.lang("report_filter_data_by_months", self.active_lang)
        q = f"""
        SELECT
            COUNT(trosak_id),
            mesec_broj||'. '||'{a}'||mesec_naziv||' ('||godina||')',
            SUM(prihod_rsd),
            SUM(rashod_rsd),
            (SUM(prihod_rsd) - SUM(rashod_rsd)),
            SUM(prihod_eur),
            SUM(rashod_eur),
            (SUM(prihod_eur)-  SUM(rashod_eur)),
            ((SUM(prihod_rsd) - SUM(rashod_rsd)) + (SUM(prihod_eur)-  SUM(rashod_eur)) * kurs),
            mesec_broj,
            godina
        FROM
            filter_data
        GROUP BY
            godina, mesec_broj
        ORDER BY
            godina, mesec_broj
            ;
        """
        return q

    def _get_SQL_group_years(self):
        a = self.start_base.lang("report_filter_data_by_years", self.active_lang)
        q = f"""
        SELECT
            COUNT(trosak_id),
            '{a}'||godina,
            SUM(prihod_rsd),
            SUM(rashod_rsd),
            (SUM(prihod_rsd) - SUM(rashod_rsd)),
            SUM(prihod_eur),
            SUM(rashod_eur),
            (SUM(prihod_eur)-  SUM(rashod_eur)),
            ((SUM(prihod_rsd) - SUM(rashod_rsd)) + (SUM(prihod_eur)-  SUM(rashod_eur)) * kurs),
            godina
        FROM
            filter_data
        GROUP BY
            godina
        ORDER BY
            godina
            ;
        """
        return q

    def _get_SQL_group_days(self):
        q = """
        SELECT
            COUNT(trosak_id),
            datum||' '||dan_naziv,
            SUM(prihod_rsd),
            SUM(rashod_rsd),
            (SUM(prihod_rsd) - SUM(rashod_rsd)),
            SUM(prihod_eur),
            SUM(rashod_eur),
            (SUM(prihod_eur)-  SUM(rashod_eur)),
            ((SUM(prihod_rsd) - SUM(rashod_rsd)) + (SUM(prihod_eur)-  SUM(rashod_eur)) * kurs),
            datum
        FROM
            filter_data
        GROUP BY
            datum
        ORDER BY
            datum_int
            ;
        """
        return q

    def _get_SQL_group_description(self):
        q = """
        SELECT
            COUNT(trosak_id),
            opis,
            SUM(prihod_rsd),
            SUM(rashod_rsd),
            (SUM(prihod_rsd) - SUM(rashod_rsd)),
            SUM(prihod_eur),
            SUM(rashod_eur),
            (SUM(prihod_eur)-  SUM(rashod_eur)),
            ((SUM(prihod_rsd) - SUM(rashod_rsd)) + (SUM(prihod_eur)-  SUM(rashod_eur)) * kurs),
            opis
        FROM
            filter_data
        GROUP BY
            opis
        ORDER BY
            opis
            ;
        """
        return q

    def _get_SQL_group_place(self):
        q = """
        SELECT
            COUNT(trosak_id),
            mesto_naziv,
            SUM(prihod_rsd),
            SUM(rashod_rsd),
            (SUM(prihod_rsd) - SUM(rashod_rsd)),
            SUM(prihod_eur),
            SUM(rashod_eur),
            (SUM(prihod_eur)-  SUM(rashod_eur)),
            ((SUM(prihod_rsd) - SUM(rashod_rsd)) + (SUM(prihod_eur)-  SUM(rashod_eur)) * kurs),
            mesto_naziv
        FROM
            filter_data
        GROUP BY
            mesto_naziv
        ORDER BY
            mesto_naziv
            ;
        """
        return q

    def _get_SQL_group_parter(self):
        q = """
        SELECT
            COUNT(trosak_id),
            partner,
            SUM(prihod_rsd),
            SUM(rashod_rsd),
            (SUM(prihod_rsd) - SUM(rashod_rsd)),
            SUM(prihod_eur),
            SUM(rashod_eur),
            (SUM(prihod_eur)-  SUM(rashod_eur)),
            ((SUM(prihod_rsd) - SUM(rashod_rsd)) + (SUM(prihod_eur)-  SUM(rashod_eur)) * kurs),
            partner
        FROM
            filter_data
        GROUP BY
            partner
        ORDER BY
            partner
            ;
        """
        return q

    def _get_SQL_group_event_type(self):
        q = """
        SELECT
            COUNT(trosak_id),
            vrsta_naziv,
            SUM(prihod_rsd),
            SUM(rashod_rsd),
            (SUM(prihod_rsd) - SUM(rashod_rsd)),
            SUM(prihod_eur),
            SUM(rashod_eur),
            (SUM(prihod_eur)-  SUM(rashod_eur)),
            ((SUM(prihod_rsd) - SUM(rashod_rsd)) + (SUM(prihod_eur)-  SUM(rashod_eur)) * kurs),
            vrsta_naziv
        FROM
            filter_data
        GROUP BY
            vrsta_naziv
        ORDER BY
            vrsta_naziv
            ;
        """
        return q

    def _get_SQL_group_none(self):
        q = """
        SELECT
            trosak_id,
            datum_int,
            dan_naziv,
            nedelja,
            mesec_naziv,
            mesec_broj,
            godina,
            vreme_upisa,
            uredjaj_id,
            vrsta_id,
            mesto_id,
            wallet_id,
            wallet_naziv,

            datum,
            prihod_rsd,
            rashod_rsd,
            prihod_eur,
            rashod_eur,
            vrsta_naziv,
            partner,
            mesto_naziv,
            opis,
            kurs
        FROM
            filter_data
            ;
        """
        return q

    def create_filter_table(self, id_list):
        event_ids_list = id_list
        # Clear previous data in table filter
        q = "DELETE FROM filter_id ;"
        self.cur.execute(q)
        self.conn.commit()
        q = "DELETE FROM filter_data ;"
        self.cur.execute(q)
        self.conn.commit()
        # Save event_ids to table filter
        q = "INSERT INTO filter_id(event_id) VALUES "
        for i in event_ids_list:
            id_data = "(" + str(i) + "),"
            q = q + id_data
        q = q[:-1]
        q = q + " ;"
        self.cur.execute(q)
        self.conn.commit()
        # Insert into table filter_data all selected from trosak, vrsta and mesto
        q = """
            INSERT INTO filter_data (
            trosak_id, 
            prihod_rsd, 
            rashod_rsd, 
            prihod_eur, 
            rashod_eur, 
            datum, 
            datum_int, 
            vreme_upisa, 
            kurs, 
            opis, 
            partner, 
            uredjaj_id, 
            vrsta_id, 
            mesto_id, 
            wallet_id, 
            vrsta_naziv, 
            mesto_naziv,
            dan_naziv,
            nedelja,
            mesec_naziv,
            mesec_broj,
            godina
            ) 

            SELECT 
            trosak.trosak_id, 
            trosak.prihod_rsd, 
            trosak.rashod_rsd, 
            trosak.prihod_eur, 
            trosak.rashod_eur, 
            trosak.datum, 
            trosak.datum_int, 
            trosak.vreme_upisa, 
            trosak.kurs, 
            trosak.opis, 
            trosak.partner, 
            trosak.uredjaj_id, 
            trosak.vrsta_id, 
            trosak.mesto_id, 
            trosak.wallet_id, 
            vrsta.naziv, 
            mesto.naziv,
            trosak_datum_extra.dan_naziv,
            trosak_datum_extra.nedelja,
            trosak_datum_extra.mesec_naziv,
            trosak_datum_extra.mesec_broj,
            trosak_datum_extra.godina
            FROM 
            trosak, vrsta, mesto, filter_id, trosak_datum_extra
            WHERE trosak.mesto_id = mesto.mesto_id AND trosak.vrsta_id = vrsta.vrsta_id AND trosak.trosak_id = filter_id.event_id AND trosak.datum = trosak_datum_extra.datum AND trosak.wallet_id = 0
            ;
        """
        self.cur.execute(q)
        self.conn.commit()

    def _create_trosak_datum_extra_table(self):
        # This is function that i used one time, for developing purporses
        q = "DELETE FROM trosak_datum_extra ;"
        self.cur.execute(q)
        self.conn.commit()
        q = """
            INSERT INTO
                trosak_datum_extra(datum)
            SELECT trosak.datum
            FROM trosak
            WHERE trosak.wallet_id = 0
            GROUP BY trosak.datum
            ;"""
        self.cur.execute(q)
        self.conn.commit()
        q = "SELECT * FROM trosak_datum_extra ;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        for i in result:
            datum = self.date_info_obj(i[0])
            q = "UPDATE trosak_datum_extra SET "
            q = q + "dan_naziv = '" + datum["day_name"] + "', "
            q = q + "nedelja = " + str(datum["week_in_year"]) + ", "
            q = q + "mesec_naziv = '" + datum["month_name"] + "', "
            q = q + "mesec_broj = " + str(datum["month"]) + ", "
            q = q + "godina = " + str(datum["year"])
            q = q + " WHERE datum = '" + i[0] + "' ;"
            self.cur.execute(q)
            self.conn.commit()
    
    def update_table_trosak_datum_extra(self, date_str):
        q = f"SELECT * FROM trosak_datum_extra WHERE datum = '{date_str}' ;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        if len(result) == 1:
            # Data is already in table
            return
        elif len(result) > 1:
            self.log.write_log(f"Warning. trosak_datum_extra table is corrupted. Multiple records with same datum value. {str(len(result))} records. connection.user.update_table_trosak_datum_extra")
            self.log.write_log("Performing data fix by calling function connection.user._create_trosak_datum_extra_table")
            self._create_trosak_datum_extra_table()
            return
        datum = self.date_info_obj(date_str)
        q = f"""
            INSERT INTO trosak_datum_extra(
                datum, 
                dan_naziv,
                nedelja,
                mesec_naziv,
                mesec_broj,
                godina)
            VALUES (
                '{date_str}',
                '{datum["day_name"]}',
                {str(datum["week_in_year"])},
                '{datum["month_name"]}',
                {str(datum["month"])},
                {str(datum["year"])} )
            ;"""
        self.cur.execute(q)
        self.conn.commit()

    def date_info_obj(self, date):
        result = {}
        act_lang = self.active_lang
        y, m, d = self.parse_date_y_m_d(date)
        datum = datetime.date(y,m,d)
        day = datum.isoweekday()
        day_in_year = int(datum.strftime("%j"))
        q = "week_day" + str(day)
        day_name = self.start_base.lang(q, act_lang)
        new_year_date = datetime.date(y,1,1)
        prvi = new_year_date.isoweekday()
        n = (prvi-2) + int(day_in_year)
        nedelja = int(n/7)
        q = "month_name" + str(m)
        month_name = self.start_base.lang(q, act_lang)

        result["day_name"] = day_name
        result["day"] = d
        result["month"] = m
        result["year"] = y
        result["day_in_week"] = day
        result["day_in_year"] = day_in_year
        result["week_in_year"] = nedelja
        result["month_name"] = month_name

        return result

    def parse_date_y_m_d(self, date_str):
        datum = date_str
        if len(datum) < 10:
            self.log.write_log("Error. Invalid date. LEN < 10  connection.user.parse_date_y_m_d")
            return 0,0,0
        d = int(datum[:2])
        m = int(datum[3:5])
        y = int(datum[6:10])
        return y,m,d

    def get_data_trosak_for_main_win(self, trosak_id=0):
        if trosak_id == 0:
            # Get data for main window
            sql_command = """
                SELECT 
                    datum,
                    prihod_rsd, 
                    rashod_rsd,
                    prihod_eur,
                    rashod_eur,
                    vrsta.naziv,
                    opis,
                    partner,
                    mesto.naziv,
                    datum_int,
                    trosak_id
                FROM
                    trosak, vrsta, mesto
                WHERE
                    vrsta.vrsta_id = trosak.vrsta_id AND
                    mesto.mesto_id = trosak.mesto_id AND 
                    wallet_id = 0;
            """
            self.cur.execute(sql_command)
            result = self.cur.fetchall()
            return result
        else:
            q = f"SELECT * FROM trosak WHERE trosak_id = {trosak_id} AND trosak.wallet_id = 0;"
            self.cur.execute(q)
            result = self.cur.fetchall()
            return result

    def get_balance_rsd(self, wallet_id=0):
        # Returns balance in main wallet
        q = f""" SELECT SUM(prihod_rsd), SUM(rashod_rsd)
                FROM trosak
                WHERE wallet_id = {str(wallet_id)};"""
        self.cur.execute(q)
        q_result = self.cur.fetchall()
        if q_result[0][0] is None:
            result = 0.0
        else:
            result = q_result[0][0] - q_result[0][1]
        return result

    def get_balance_eur(self, wallet_id=0):
        # Returns balance in main wallet
        q = f""" SELECT SUM(prihod_eur), SUM(rashod_eur)
                FROM trosak
                WHERE wallet_id = {str(wallet_id)};"""
        self.cur.execute(q)
        q_result = self.cur.fetchall()
        if q_result[0][0] is None:
            result = 0.0
        else:
            result = q_result[0][0] - q_result[0][1]
        return result

    def get_partner_list_unique(self, sort_data=False):
        q = "SELECT DISTINCT(partner) FROM trosak WHERE trosak.wallet_id = 0 "
        if sort_data:
            q = q + "ORDER BY partner COLLATE NOCASE;"
        else:
            q = q + ";"
        self.cur.execute(q)
        result = self.cur.fetchall()
        return result
   
    def get_event_type_all(self, event_type_id=0, event_type_naziv=""):
        if event_type_id == 0 and event_type_naziv == "":
            q = "SELECT vrsta_id, naziv FROM vrsta;"
            self.cur.execute(q)
            result = self.cur.fetchall()
            return result
        elif event_type_id != 0:
            q = f"SELECT vrsta_id, naziv FROM vrsta WHERE vrsta_id = {event_type_id} ;"
            self.cur.execute(q)
            result = self.cur.fetchall()
            if len(result) > 1:
                self.log.write_log("Error. event_type returns multiple rows for ID")
            return result
        elif event_type_naziv != "":
            q = f"SELECT vrsta_id, naziv FROM vrsta WHERE naziv = ? ;"
            self.cur.execute(q, (event_type_naziv,))
            result = self.cur.fetchall()
            if len(result) > 1:
                self.log.write_log("Warrning. event_type returns multiple rows for 'naziv'")
            return result

    def get_place_all(self, place_id=0, place_naziv=""):
        q = "SELECT mesto_id, naziv FROM mesto "
        if place_id == 0 and place_naziv == "":
            q = q + ";"
            self.cur.execute(q)
        elif place_id != 0:
            q = q + "WHERE mesto_id = ? ;"
            self.cur.execute(q, (place_id,))
        elif place_naziv != "":
            q = q + "WHERE naziv = ? ;"
            self.cur.execute(q, (place_naziv,))

        result = self.cur.fetchall()
        return result

    def set_event(self, event_object):
        o = event_object
        # Check is there event with that ID
        q = f"""SELECT * FROM trosak WHERE trosak_id = {str(o["trosak_id"])} ;"""
        self.cur.execute(q)
        result = self.cur.fetchall()
        if len(result) != 1:
            self.log.write_log("Error. Event ID not found. Can't update event. connection.user.set_event")
            return
        # Update event
        c_date_time = self.start_base.get_current_date(get_date_and_time=True)
        device_id = self._get_uredjaj_id()
        q = f"""
            UPDATE
                trosak
            SET 
                prihod_rsd = {float(o["prihod_rsd"])},
                rashod_rsd = {float(o["rashod_rsd"])},
                prihod_eur = {float(o["prihod_eur"])},
                rashod_eur = {float(o["rashod_eur"])},
                datum = '{o["datum"]}',
                datum_int = {int(o["datum_int"])},
                vreme_upisa = '{c_date_time}',
                kurs = {float(o["kurs"])},
                opis = ?,
                partner = ?,
                uredjaj_id = {int(device_id)},
                vrsta_id = {int(o["vrsta_id"])},
                mesto_id = {int(o["mesto_id"])},
                wallet_id = {int(o["wallet_id"])}
            
            WHERE 
                trosak_id = {int(o["trosak_id"])}
            ;
        """
        self.cur.execute(q, (o["opis"], o["partner"]))
        self.conn.commit()
        self.update_table_trosak_datum_extra(o["datum"])
        self.log.write_log("Updated event in user database. connection.user.set_event")

    def add_event(self, event_object):
        o = event_object
        c_date_time = self.start_base.get_current_date(get_date_and_time=True)
        device_id = self._get_uredjaj_id()
        q = f"""
            INSERT INTO
            trosak( prihod_rsd,
                    rashod_rsd,
                    prihod_eur,
                    rashod_eur,
                    datum,
                    datum_int,
                    vreme_upisa,
                    kurs,
                    opis,
                    partner,
                    uredjaj_id,
                    vrsta_id,
                    mesto_id,
                    wallet_id
                    )
            VALUES (
                {float(o["prihod_rsd"])},
                {float(o["rashod_rsd"])},
                {float(o["prihod_eur"])},
                {float(o["rashod_eur"])},
                '{o["datum"]}',
                {int(o["datum_int"])},
                '{c_date_time}',
                {float(o["kurs"])},
                ?,
                ?,
                {int(device_id)},
                {int(o["vrsta_id"])},
                {int(o["mesto_id"])},
                {int(o["wallet_id"])}
            ) ;
        """
        self.cur.execute(q, (o["opis"], o["partner"]))
        self.conn.commit()
        result = self.cur.lastrowid
        self.update_table_trosak_datum_extra(o["datum"])
        self.log.write_log("Added event to user database. connection.user.add_event")
        return result

    def set_event_type(self, evnt_type_id, event_type_new_name):
        if len(self.get_event_type_all(event_type_id=evnt_type_id)) > 0:
            q = f"UPDATE vrsta SET naziv = ? WHERE vrsta_id = {evnt_type_id} ;"
            self.cur.execute(q, (event_type_new_name,))
            self.conn.commit()
            self.log.write_log("Updated event type.")
        else:
            self.log.write_log("Warning. Event type not updated. Record does not exist. connection.set_event_type")

    def add_event_type(self, e_t_name):
        if len(self.get_event_type_all(event_type_naziv=e_t_name)) == 0:
            q = f"INSERT INTO vrsta(naziv) VALUES (?) ;"
            self.cur.execute(q, (e_t_name,))
            self.conn.commit()
            self.log.write_log("Added new event type.")
        else:
            self.log.write_log("Warning. Event type not added. Record already exist. connection.add_event_type")
        return self.cur.lastrowid

    def delete_event_type(self, e_t_id):
        e = e_t_id
        if not self.is_safe_to_delete_event_type(e):
            self.log.write_log("Warning. Event type not Deleted. Record is in use. connection.delete_event_type")
            return
        if len(self.get_event_type_all(event_type_id=e_t_id)) != 0:
            q = f"DELETE FROM vrsta WHERE vrsta_id = {e_t_id} ;"
            self.cur.execute(q)
            self.conn.commit()
            self.log.write_log("Deleted event type.")
        else:
            self.log.write_log("Warning. Event type not Deleted. Record does not exist. connection.delete_event_type")

    def is_safe_to_delete_event_type(self, e_t_id):
        q = f"SELECT * from trosak WHERE vrsta_id = {e_t_id} ;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        if len(result) == 0:
            return True
        else:
            return False

    def set_place(self, plac_id, place_new_name):
        if len(self.get_place_all(place_id=plac_id)) > 0:
            q = f"UPDATE mesto SET naziv = ? WHERE mesto_id = {plac_id} ;"
            self.cur.execute(q, (place_new_name,))
            self.conn.commit()
            self.log.write_log("Updated place.")
        else:
            self.log.write_log("Warning. Place not updated. Record does not exist. connection.set_place")

    def add_place(self, new_place_name):
        if len(self.get_place_all(place_naziv=new_place_name)) == 0:
            q = f"INSERT INTO mesto(naziv) VALUES (?) ;"
            self.cur.execute(q, (new_place_name,))
            self.conn.commit()
            self.log.write_log("Added new place.")
        else:
            self.log.write_log("Warning. Place not added. Record already exist. connection.add_place")
        return self.cur.lastrowid

    def delete_place(self, old_place_id):
        e = old_place_id
        if not self.is_safe_to_delete_place(e):
            self.log.write_log("Warning. Place not Deleted. Record is in use. connection.delete_place")
            return
        if len(self.get_place_all(place_id=old_place_id)) != 0:
            q = f"DELETE FROM mesto WHERE mesto_id = {old_place_id} ;"
            self.cur.execute(q)
            self.conn.commit()
            self.log.write_log("Deleted place.")
        else:
            self.log.write_log("Warning. Place not Deleted. Record does not exist. connection.delete_place")

    def is_safe_to_delete_place(self, place_id):
        q = f"SELECT * from trosak WHERE mesto_id = {place_id} ;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        if len(result) == 0:
            return True
        else:
            return False

    def delete_event(self, event_id):
        result = self.get_data_trosak_for_main_win(trosak_id=event_id)
        if len(result) == 0:
            self.log.write_log(f"Error. Unable to delete event. Event does not exist. Event_ID = {event_id}")
            return
        q = f"DELETE FROM trosak WHERE trosak_id = {event_id} ;"
        self.cur.execute(q)
        self.conn.commit()
        return

    def get_device_all(self, device_id=0):
        q = "SELECT * FROM uredjaj "
        if device_id == 0:
            q = q + ";"
        else:
            q = q + f"WHERE uredjaj_id = {str(device_id)} ;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        return result

    def _write_all_datum_int(self):
        # Upisuje u bazu sve datum integer podatke
        q = "SELECT trosak_id, datum, datum_int FROM trosak;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        for i in result:
            a = self.start_base.date_to_integer(i[1])
            q = f"UPDATE trosak SET datum_int = {str(a)} WHERE trosak_id = {str(i[0])} ;"
            self.cur.execute(q)
            self.conn.commit()
        
    def _StaraBazaTranslate(self):
        self.cur.execute("SELECT * FROM troskovi;")
        stara = self.cur.fetchall()
        
        for data in stara:
            print (data)
            if self.start_base.is_decimal(data[1]):
                prihod_rsd = float(data[1])
            else:
                prihod_rsd = 0.0
            if self.start_base.is_decimal(data[2]):
                rashod_rsd = float(data[2])
            else:
                rashod_rsd = 0.0
            if self.start_base.is_date_valid(data[0]):
                datum_int = self.start_base.date_to_integer(data[0])
            datum = data[0]
            opis = data[3]
            partner = data[4]
            vreme = self.start_base.get_current_date(get_date_and_time=True)


            q = f"""INSERT INTO trosak(
                prihod_rsd,
                rashod_rsd,
                prihod_eur,
                rashod_eur,
                datum,
                datum_int,
                vreme_upisa,
                kurs,
                opis,
                partner,
                uredjaj_id,
                vrsta_id,
                mesto_id,
                wallet_id
            )
            VALUES (
                {prihod_rsd},
                {rashod_rsd},
                0,
                0,
                '{datum}',
                {datum_int},
                '{vreme}',
                116,
                ?,
                ?,
                1,
                1,
                1,
                0
            ) ;
            """
            self.cur.execute(q, (opis, partner))
            self.conn.commit()

        
class WebPages():
    def __init__(self, user_id):
        # Setup enviroment variables
        self.active_user_id = user_id
        self.log = log_cls.LogData()
        self.start_base  = ConnStart()
        self.user = User(self.active_user_id)
        user_database = UserDatabaseConection(self.active_user_id)
        self.conn = user_database.get_connection()
        self.cur = self.conn.cursor()

    def add_web_page(self, web_page_object):
        wp = web_page_object
        vreme = self.start_base.get_current_date(get_date_and_time=True)
        password = self.start_base._encrypt_user_password(wp["password"])
        q = f"""
            INSERT INTO
                web(
                    naslov,
                    stranica,
                    opis,
                    username,
                    password,
                    vreme_upisa
                )
            VALUES (?,
                    ?,
                    ?,
                    ?,
                    '{password}',
                    '{vreme}' 
                    ) ;
        """
        self.cur.execute(q, (wp["naslov"], wp["stranica"], wp["opis"], wp["username"]))
        self.conn.commit()
        self.log.write_log("1 item added. WebPages.add_web_page")

    def get_web_pages(self, filter_criteria=""):
        q = "SELECT * FROM web ;"
        self.cur.execute(q)
        res = self.cur.fetchall()
        result = []
        if filter_criteria == "":
            result = res
        else:
            for i in res:
                data = i[1] + i[2] + i[3] + i[4] + i[5]
                if data.find(filter_criteria) >= 0:
                    result.append(i)
        return result

    def get_web_page(self, web_id):
        q = f"SELECT * FROM web WHERE web_id = {web_id} ;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        return result

    def decript_password(self, password):
        result = self.start_base._decrypt_user_password(password)
        return result
    
    def set_web_page(self, web_page_object):
        wp = web_page_object
        is_valid = self.get_web_page(wp["web_id"])
        if len(is_valid) != 1:
            return
        vreme = self.start_base.get_current_date(get_date_and_time=True)
        password = self.start_base._encrypt_user_password(wp["password"])
        q = f"""
            UPDATE 
                web
            SET
                naslov = ?,
                stranica = ?,
                opis = ?,
                username = ?,
                password = '{password}',
                vreme_upisa = '{vreme}' 
            WHERE
                web_id = {wp["web_id"]} ;
        """
        self.cur.execute(q, (wp["naslov"], wp["stranica"], wp["opis"], wp["username"]))
        self.conn.commit()
        self.log.write_log("1 item edited. WebPages.set_web_page")

    def delete_web_page(self, web_page_id):
        is_valid = self.get_web_page(web_page_id)
        if len(is_valid) != 1:
            return False
        q = f"DELETE FROM web WHERE web_id = {web_page_id} ;"
        self.cur.execute(q)
        self.conn.commit()
        self.log.write_log("1 item deleted. WebPages.delete_web_page")
        return True


class Wallets():
    def __init__(self, user_id):
        # Create enviroment variables
        self.active_user_id = user_id
        self.log = log_cls.LogData()
        self.user = User(self.active_user_id)
        self.start_base = ConnStart()
        user_database = UserDatabaseConection(self.active_user_id)
        self.conn = user_database.get_connection()
        self.cur = self.conn.cursor()

    def add_wallet(self, wallet_dic):
        w = wallet_dic
        w_today = self.start_base.get_current_date(get_date_and_time=True)
        q = f"INSERT INTO wallet(name, description, created_at) VALUES (?,?,'{w_today}') ;"
        self.cur.execute(q, (w["name"], w["description"]))
        self.conn.commit()
        self.log.write_log("Wallet added.")

    def set_wallet(self, wallet_dic):
        w_id = wallet_dic["wallet_id"]
        w_today = self.start_base.get_current_date(get_date_and_time=True)
        q = f"UPDATE wallet SET name = ?, description = ?, created_at = '{w_today}' WHERE wallet_id = {w_id} ;"
        self.cur.execute(q, (wallet_dic["name"], wallet_dic["description"]))
        self.conn.commit()
        self.log.write_log("Wallet updated.")

    def delete_wallet(self, wallet_id):
        q = f"DELETE FROM wallet WHERE wallet_id = {wallet_id} ;"
        self.cur.execute(q)
        self.conn.commit()
        self.log.write_log("Wallet deleted.")

    def is_safe_to_delete_wallet(self, wallet_id):
        ev = self.get_events(wallet_id)
        if len(ev) == 0:
            return True
        else:
            return False

    def get_wallet_all(self, wallet_id=0):
        q = "SELECT * FROM wallet "
        if wallet_id != 0:
            qq = f"WHERE wallet_id = {wallet_id} ;"
        else:
            qq = ";"
        q = q + qq
        self.cur.execute(q)
        result = self.cur.fetchall()
        return result

    def get_events(self, wallet_id):
        q = f"SELECT * FROM trosak WHERE wallet_id = {wallet_id} ORDER BY datum_int ;"
        self.cur.execute(q)
        result = self.cur.fetchall()
        return result

    def transfer_from_main_wallet(self, wallet_id, rsd, eur):
        kurs = self.start_base.get_setting_data("kurs", user_id=self.active_user_id)
        evnt = {}
        evnt["prihod_rsd"] = 0
        evnt["rashod_rsd"] = rsd
        evnt["prihod_eur"] = 0
        evnt["rashod_eur"] = eur
        evnt["datum"] = self.start_base.get_current_date()
        evnt["datum_int"] = self.start_base.date_to_integer(evnt["datum"])
        if self.start_base.is_decimal(kurs):
            evnt["kurs"] = float(kurs)
        else:
            evnt["kurs"] = 0
        evnt["opis"] = "TRANSFER"
        evnt["partner"] = "TRANSFER"
        evnt["vrsta_id"] = self._get_event_type()
        evnt["mesto_id"] = self._get_place()
        evnt["wallet_id"] = 0
        last_id = self.user.add_event(evnt)
        evnt["partner"] = str(last_id)
        evnt["prihod_rsd"] = rsd
        evnt["rashod_rsd"] = 0
        evnt["prihod_eur"] = eur
        evnt["rashod_eur"] = 0
        evnt["wallet_id"] = wallet_id
        self.user.add_event(evnt)
        self.log.write_log("Transfer from main wallet completed.")

    def transfer_to_main_wallet(self, wallet_id, rsd, eur):
        kurs = self.start_base.get_setting_data("kurs", user_id=self.active_user_id)
        evnt = {}
        evnt["prihod_rsd"] = rsd
        evnt["rashod_rsd"] = 0
        evnt["prihod_eur"] = eur
        evnt["rashod_eur"] = 0
        evnt["datum"] = self.start_base.get_current_date()
        evnt["datum_int"] = self.start_base.date_to_integer(evnt["datum"])
        if self.start_base.is_decimal(kurs):
            evnt["kurs"] = float(kurs)
        else:
            evnt["kurs"] = 0
        evnt["opis"] = "TRANSFER"
        evnt["partner"] = "TRANSFER"
        evnt["vrsta_id"] = self._get_event_type()
        evnt["mesto_id"] = self._get_place()
        evnt["wallet_id"] = 0
        last_id = self.user.add_event(evnt)
        evnt["partner"] = str(last_id)
        evnt["prihod_rsd"] = 0
        evnt["rashod_rsd"] = rsd
        evnt["prihod_eur"] = 0
        evnt["rashod_eur"] = eur
        evnt["wallet_id"] = wallet_id
        self.user.add_event(evnt)
        self.log.write_log("Transfer from main wallet completed.")

    def _get_place(self):
        place_id = self.start_base.get_setting_data("wallet_transfer_mesto_id", getParametar=True, user_id=self.active_user_id)
        if place_id == 0:
            result = self.user.add_place("TRANSFER")
            self.start_base.set_setting_data("wallet_transfer_mesto_id", "Wallet transfer", result, self.active_user_id)
        else:
            result = place_id
        return result
        
    def _get_event_type(self):
        evt_id = self.start_base.get_setting_data("wallet_transfer_vrsta_id", getParametar=True, user_id=self.active_user_id)
        if evt_id == 0:
            result = self.user.add_event_type("TRANSFER")
            self.start_base.set_setting_data("wallet_transfer_vrsta_id", "Wallet transfer", result, self.active_user_id)
        else:
            result = evt_id
        return result


class Chart():
    def __init__(self, user_id):
        # Create enviroment variables
        self.active_user_id = user_id
        self.start_base = ConnStart()
        self.user = User(self.active_user_id)
        user_database = UserDatabaseConection(self.active_user_id)
        self.conn = user_database.get_connection()
        self.cur = self.conn.cursor()
        self.log = log_cls.LogData()

    def get_charts_all(self, chart_id=0, chart_name=""):
        q = "SELECT * FROM chart "
        if chart_id != 0:
            q = q + f"WHERE chart_id = {str(chart_id)} ;"
        elif chart_name != "":
            q = q + f"WHERE name = ? ;"
        else:
            q = q + ";"
        if chart_name != "":
            self.cur.execute(q, (chart_name,))
        else:
            self.cur.execute(q)
        result = self.cur.fetchall()
        return result

    def set_chart_name(self, chart_id, chart_name):
        q = f"UPDATE chart SET name = ? WHERE chart_id = {str(chart_id)} ;"
        self.cur.execute(q, (chart_name,))
        self.conn.commit()
        return

    def delete_chart_and_data(self, chart_id):
        q = f"DELETE FROM chart WHERE chart_id = {str(chart_id)} ;"
        self.cur.execute(q)
        self.conn.commit()
        self._delete_chart_data(chart_id)

    def _add_chart_to_chart_table(self, name, description):
        # Save chart in chart table
        q = """
        INSERT INTO
            chart(name, description)
        VALUES
            (?, ?)
            ;"""
        self.cur.execute(q, (name, description))
        self.conn.commit()
        result = self.cur.lastrowid
        return result

    def _delete_chart_data(self, chart_id):
        q = f"DELETE FROM chart_data WHERE chart_id = {str(chart_id)} ;"
        self.cur.execute(q)
        self.conn.commit()

    def get_chart_data(self, chart_id):
        c = {}
        # Get data from chart database
        d = self.get_charts_all(chart_id=chart_id)
        c["name"] = d[0][1]
        c["description"] = d[0][2]
        # Get data from chart_data database
        q = f"SELECT * FROM chart_data WHERE chart_id = {str(chart_id)} ;"
        self.cur.execute(q)
        d = self.cur.fetchall()
        # Make chart dictionary
        c["event_type"] = []
        c["partner"] = []
        c["location"] = []
        c["headline_font"] = []
        c["X_font"] = []
        c["Y_font"] = []
        # Load data
        for i in d:
            if i[2] == "event_type":
                if i[3] == "all" and i[5] == 1:
                    c["event_type"] = "all"
                else:
                    c["event_type"].append(i[4])
            elif i[2] == "partner":
                if i[3] == "all" and i[5] == 1:
                    c["partner"] = "all"
                else:
                    c["partner"].append(i[3])
            elif i[2] == "location":
                if i[3] == "all" and i[5] == 1:
                    c["location"] = "all"
                else:
                    c["location"].append(i[4])
            elif i[2] == "group":
                c["group"] = i[3]
            elif i[2] == "headline":
                c["headline"] = i[3]
            elif i[2] == "headline_font_name":
                c["headline_font"].append(i[3])
            elif i[2] == "headline_font_size":
                c["headline_font"].append(i[4])
            elif i[2] == "headline_font_bold":
                if i[4] == 1:
                    c["headline_font"].append(True)
                else:
                    c["headline_font"].append(False)
            elif i[2] == "headline_font_italic":
                if i[4] == 1:
                    c["headline_font"].append(True)
                else:
                    c["headline_font"].append(False)
            elif i[2] == "headline_font_underline":
                if i[4] == 1:
                    c["headline_font"].append(True)
                else:
                    c["headline_font"].append(False)
            elif i[2] == "headline_font_strikeout":
                if i[4] == 1:
                    c["headline_font"].append(True)
                else:
                    c["headline_font"].append(False)
            elif i[2] == "headline_color":
                c["headline_color"] = i[3]
            elif i[2] == "X":
                c["X"] = i[3]
            elif i[2] == "X_font_name":
                c["X_font"].append(i[3])
            elif i[2] == "X_font_size":
                c["X_font"].append(i[4])
            elif i[2] == "X_font_bold":
                if i[4] == 1:
                    c["X_font"].append(True)
                else:
                    c["X_font"].append(False)
            elif i[2] == "X_font_italic":
                if i[4] == 1:
                    c["X_font"].append(True)
                else:
                    c["X_font"].append(False)
            elif i[2] == "X_font_underline":
                if i[4] == 1:
                    c["X_font"].append(True)
                else:
                    c["X_font"].append(False)
            elif i[2] == "X_font_strikeout":
                if i[4] == 1:
                    c["X_font"].append(True)
                else:
                    c["X_font"].append(False)
            elif i[2] == "X_color":
                c["X_color"] = i[3]
            elif i[2] == "Y":
                c["Y"] = i[3]
            elif i[2] == "Y_font_name":
                c["Y_font"].append(i[3])
            elif i[2] == "Y_font_size":
                c["Y_font"].append(i[4])
            elif i[2] == "Y_font_bold":
                if i[4] == 1:
                    c["Y_font"].append(True)
                else:
                    c["Y_font"].append(False)
            elif i[2] == "Y_font_italic":
                if i[4] == 1:
                    c["Y_font"].append(True)
                else:
                    c["Y_font"].append(False)
            elif i[2] == "Y_font_underline":
                if i[4] == 1:
                    c["Y_font"].append(True)
                else:
                    c["Y_font"].append(False)
            elif i[2] == "Y_font_strikeout":
                if i[4] == 1:
                    c["Y_font"].append(True)
                else:
                    c["Y_font"].append(False)
            elif i[2] == "Y_color":
                c["Y_color"] = i[3]
            elif i[2] == "Y_type":
                c["Y_type"] = [i[3], i[4]]
            elif i[2] == "g_type":
                c["g_type"] = i[3]
            elif i[2] == "g_color":
                c["g_color"] = i[3]
            elif i[2] == "g_marker":
                c["g_marker"] = i[3]
            elif i[2] == "g_pattern":
                c["g_pattern"] = i[3]
        return c

    def add_chart(self, chart_dict, chart_name=""):
        c = chart_dict
        # Save chart in chart table
        if chart_name == "":
            c_id = self._add_chart_to_chart_table(c["name"], c["description"])
        else:
            is_exist_chart = self.get_charts_all(chart_name=chart_name)
            if len(is_exist_chart) > 0:
                c_id = is_exist_chart[0][0]
                self._delete_chart_data(c_id)
            else:
                c_id = self._add_chart_to_chart_table(c["name"], c["description"])
        # Save all data to chart_data table
        c_data = []  # Create list to be saved
        if c["event_type"] == "all":
            c_data.append([c_id, "event_type", "all", 1, 1])
        else:
            for i in c["event_type"]:
                c_data.append([c_id, "event_type", "", i, 0])
        if c["partner"] == "all":
            c_data.append([c_id, "partner", "all", 1, 1])
        else:
            for i in c["partner"]:
                c_data.append([c_id, "partner", i, 0, 0])
        if c["location"] == "all":
            c_data.append([c_id, "location", "all", 1, 1])
        else:
            for i in c["location"]:
                c_data.append([c_id, "location", "", i, 0])
        c_data.append([c_id, "group", c["group"], 0, 0])
        # Add headline
        c_data.append([c_id, "headline", c["headline"], 0, 0])
        result = self._add_font_to_list(c_id, "headline_font", c["headline_font"])
        for i in result:
            c_data.append(i)
        c_data.append([c_id, "headline_color", c["headline_color"], 0, 0])
        # Add X axis
        c_data.append([c_id, "X", c["X"], 0, 0])
        result = self._add_font_to_list(c_id, "X_font", c["X_font"])
        for i in result:
            c_data.append(i)
        c_data.append([c_id, "X_color", c["X_color"], 0, 0])
        # Add Y axis
        c_data.append([c_id, "Y", c["Y"], 0, 0])
        result = self._add_font_to_list(c_id, "Y_font", c["Y_font"])
        for i in result:
            c_data.append(i)
        c_data.append([c_id, "Y_color", c["Y_color"], 0, 0])
        c_data.append([c_id, "Y_type", c["Y_type"][0], c["Y_type"][1], 0])
        # Add other stuff
        c_data.append([c_id, "g_type", c["g_type"], 0, 0])
        c_data.append([c_id, "g_color", c["g_color"], 0, 0])
        c_data.append([c_id, "g_marker", c["g_marker"], 0, 0])
        c_data.append([c_id, "g_pattern", c["g_pattern"], 0, 0])
        # Save data to chart_data
        for i in c_data:
            q = f"""
                INSERT INTO 
                    chart_data(
                        chart_id,
                        data,
                        val_txt,
                        val_int,
                        val_real)
                VALUES (
                    {str(i[0])},
                    '{i[1]}',
                    ?,
                    {str(i[3])},
                    {str(i[4])}) ;"""
            self.cur.execute(q, (i[2],))
            self.conn.commit()

    def _add_font_to_list(self, chart_id, data, font_lst):
        f = font_lst
        c_id = chart_id
        c_data = []
        c_data.append([c_id, data + "_name", f[0], 0, 0])
        c_data.append([c_id, data + "_size", "", f[1], 0])
        if f[2]:
            c_data.append([c_id, data + "_bold", "", 1, 0])
        else:
            c_data.append([c_id, data + "_bold", "", 0, 0])
        if f[3]:
            c_data.append([c_id, data + "_italic", "", 1, 0])
        else:
            c_data.append([c_id, data + "_italic", "", 0, 0])
        if f[4]:
            c_data.append([c_id, data + "_underline", "", 1, 0])
        else:
            c_data.append([c_id, data + "_underline", "", 0, 0])
        if f[5]:
            c_data.append([c_id, data + "_strikeout", "", 1, 0])
        else:
            c_data.append([c_id, data + "_strikeout", "", 0, 0])
        return c_data

    def get_filter_data(self, chart_dictionary):
        if chart_dictionary["group"] == "datum":
            sql_select = "dan_naziv||' '||datum"
            sql_group = "datum_int"
        elif chart_dictionary["group"] == "nedelja":
            sql_select = "nedelja||' - '||godina"
            sql_group = "godina, nedelja"
        elif chart_dictionary["group"] == "mesec_broj":
            sql_select = "mesec_naziv||','||godina"
            sql_group = "godina, mesec_broj"
        elif chart_dictionary["group"] == "godina":
            sql_select = "godina"
            sql_group = "godina"
        q = f"""
        SELECT
            {sql_select},
            prihod_rsd,
            rashod_rsd,
            (prihod_rsd - rashod_rsd),
            prihod_eur,
            rashod_eur,
            (prihod_eur - rashod_eur),
            vrsta_id,
            partner,
            mesto_id
        FROM
            filter_data
        ORDER BY
            datum_int ;"""
        self.cur.execute(q)
        result = self.cur.fetchall()
        return result



# a = ConnStart()
# a.proba()

# a=  User(12)
# a.get_balance_rsd(1)

