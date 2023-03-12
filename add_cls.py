from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

# import login  # Login screen
import log_cls  # Handle 'log.txt' file
import connection  # Handle 'start_up.db' and user database
import add_ui  # GUI for add event
import cal_ui  # Calendar GUI
import add_type_ui  # GUI for add event type
import add_place_ui  # GUI for add place


class EventAdd(QtWidgets.QDialog):
    
    def __init__(self, user_name, user_id, active_lang, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_user_name = user_name
        self.active_user_id = user_id
        self.active_lang = active_lang
        self.conn = connection.ConnStart()
        self.user = connection.User(self.active_user_id)
        self.log = log_cls.LogData()
        self.ui = add_ui.Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.btn_save.setEnabled(False)

        self.log.write_log("Add event started...")
        self.retranslateUi()
        self.setWindowFlag(QtCore.Qt.Dialog)
        self.event_types = []
        self.places = []
        self.ui.tbl_items.setColumnCount(10)
        
    def setup_ui(self):
        # Set Add button disabled, will be enabled if conditions are meet
        self.ui.btn_add.setEnabled(False)
        # Events in dialog
        self.ui.btn_add.clicked.connect(self.btn_add_click)
        self.ui.btn_cancel.clicked.connect(self.btn_cancel_click)
        self.ui.btn_save.clicked.connect(self.btn_save_click)
        self.ui.btn_date_pick.clicked.connect(self.btn_date_pick_click)
        self.ui.tbl_items.keyPressEvent = self.tbl_items_key_press
        self.ui.btn_new_event_type.clicked.connect(self.btn_new_event_type_click)
        self.ui.btn_new_place.clicked.connect(self.btn_new_place_click)
        # Setup custom menu for table
        self.add_custom_menu_to_table()
        # Set Dialog and set focus to rashod_rsd
        self.setFixedSize(900,330)
        self.setWindowTitle(self.conn.lang("add_event_caption", self.active_lang))
        # Set color for table
        self.ui.tbl_items.horizontalHeader().setStyleSheet("background-color: #55ffff;")
        self.ui.tbl_items.verticalHeader().setStyleSheet("background-color: #55ffff;")
        # Populate widgets with data
        self.ui.txt_income_rsd.setText("0.00")
        self.ui.txt_outcome_rsd.setText("0.00")
        self.ui.txt_income_eur.setText("0.00")
        self.ui.txt_outcome_eur.setText("0.00")
        self.ui.dt_date.setDate(self.date_today_object())
        self.ui.dt_date.setDisplayFormat("dd.MM.yyyy")
        self.ui.txt_income_rsd.selectAll()
        self.populate_cmb_event_type(current_id=int(self.conn.get_setting_data("add_event_cmb_event_type", getParametar=True, user_id=self.active_user_id)))
        self.populate_places(current_id=int(self.conn.get_setting_data("add_event_cmb_places", getParametar=True, user_id=self.active_user_id)))
        self.populate_partners(current_id=self.conn.get_setting_data("add.event_cmb_partner", getParametar=True, user_id=self.active_user_id))
        self.ui.txt_exchange.setText(self.conn.get_setting_data("kurs", user_id=self.active_user_id))

    
    def add_custom_menu_to_table(self):
        # Create menu object
        self.mnu_table = QtWidgets.QMenu(self.ui.tbl_items)
        # Create items for menu
        self.mnu_table_delete = QtWidgets.QAction(self.conn.lang("btn_delete", self.active_lang), self.ui.tbl_items)
        # Add items to menu
        self.mnu_table.addAction(self.mnu_table_delete)
        # Connect menu and menu items with slots
        self.mnu_table_delete.triggered.connect(self.mnu_table_delete_trigger)
        self.ui.tbl_items.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.tbl_items.customContextMenuRequested.connect(self.mnu_table_show)

    def mnu_table_show(self, position):
        self.mnu_table.exec_(self.ui.tbl_items.viewport().mapToGlobal(position))

    def mnu_table_delete_trigger(self):
        self.delete_item_from_table()

    def btn_date_pick_click(self):
        calendar_obj = Calendar()
        datum = calendar_obj.setup_ui(self.ui.dt_date.date(), self.active_lang)
        if datum != "":
            self.ui.dt_date.setDate(datum)

    def btn_new_event_type_click(self):
        event_type = AddEventType(self.active_user_id, self.active_lang)
        event_type.setup_ui()
        self.populate_cmb_event_type()

    def btn_new_place_click(self):
        place = AddPlace(self.active_user_id, self.active_lang)
        place.setup_ui()
        self.populate_places()

    
    def populate_partners(self, current_id=0):
        partner_list = self.user.get_partner_list_unique(sort_data=True)
        for i in partner_list:
            self.ui.cmb_partner.addItem(i[0])
        c = self.ui.cmb_partner.count()
        if c > 0 and current_id < c:
            self.ui.cmb_partner.setCurrentIndex(current_id)

    def check_tbl_item_has_data(self):
        if self.ui.tbl_items.rowCount() < 1:
            self.setFixedSize(900,330)
            self.ui.btn_save.setEnabled(False)
        else:
            has_row = -1
            for i in range(self.ui.tbl_items.rowCount()):
                if not self.ui.tbl_items.isRowHidden(i):
                    has_row = i
                    break
                    
            if has_row > -1:
                self.ui.btn_save.setEnabled(True)
                self.setFixedSize(900,530)
                self.ui.tbl_items.setCurrentCell(has_row, 0)
            else:
                self.ui.btn_save.setEnabled(False)
                self.setFixedSize(900,330)
                self.ui.txt_outcome_rsd.setFocus()


    def tbl_items_key_press(self, event):
        a = []
        row_n = 0
        j = 0
        x = self.ui.tbl_items.currentRow()
        y = self.ui.tbl_items.currentColumn()

        for i in range(self.ui.tbl_items.rowCount()):
            if not self.ui.tbl_items.isRowHidden(i):
                row_n += 1
                a.append((j, i))
            j += 1

        if event.key() == QtCore.Qt.Key_Delete:
            self.delete_item_from_table()
        elif event.key() == QtCore.Qt.Key_Up:
            if x > 0:
                for i in range(len(a)):
                    if a[i][1] == x:
                        if i != 0:
                            x = a[i-1][1]
                            break
                self.ui.tbl_items.setCurrentCell(x,y)
        elif event.key() == QtCore.Qt.Key_Down:
            if x < a[len(a)-1][1]:
                for i in range(len(a)):
                    if a[i][1] == x:
                        if i != len(a):
                            x = a[i+1][1]
                            break
                self.ui.tbl_items.setCurrentCell(x,y)
        elif event.key() == QtCore.Qt.Key_Left:
            if y > 0:
                y = y - 1
                self.ui.tbl_items.setCurrentCell(x,y)
        elif event.key() == QtCore.Qt.Key_Right:
            if y < 9:
                y = y + 1
                self.ui.tbl_items.setCurrentCell(x,y)
                

    def delete_item_from_table(self):
        if self.ui.tbl_items.currentRow() > -1:
            self.ui.tbl_items.hideRow(self.ui.tbl_items.currentRow())
            self.check_tbl_item_has_data()


    def btn_add_click(self):
        # Check if partner or description are too long
        msg_title = self.conn.lang("add_event_msg_too_many_char_title", self.active_lang)
        if len(self.ui.cmb_partner.currentText()) > 255:
            msg_text = self.conn.lang("add_event_msg_too_many_char_text_partner", self.active_lang)
            QtWidgets.QMessageBox.information(None, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
            return
        if len(self.ui.txt_description.text()) > 255:
            msg_text = self.conn.lang("add_event_msg_too_many_char_text_description", self.active_lang)
            QtWidgets.QMessageBox.information(None, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
            return

        # Expand window and set 'Save' button enabled
        self.setFixedSize(900,530)
        self.ui.btn_save.setEnabled(True)
        
        # Expand table for 1 row
        rows = self.ui.tbl_items.rowCount()
        self.ui.tbl_items.setRowCount(rows+1)

        # If any numeric data is empty fill with 0.00
        if self.ui.txt_income_rsd.text().strip() == "":
            self.ui.txt_income_rsd.setText("0.00")
        if self.ui.txt_outcome_rsd.text().strip() == "":
            self.ui.txt_outcome_rsd.setText("0.00")
        if self.ui.txt_income_eur.text().strip() == "":
            self.ui.txt_income_eur.setText("0.00")
        if self.ui.txt_outcome_eur.text().strip() == "":
            self.ui.txt_outcome_eur.setText("0.00")
        if self.ui.txt_exchange.text().strip() == "":
            self.ui.txt_exchange.setText("0")

        # Populate new row with current data
        row_n = self.ui.tbl_items.rowCount() - 1

        itm = QtWidgets.QTableWidgetItem
        self.ui.tbl_items.setItem(row_n, 0, itm(self.ui.txt_income_rsd.text()))
        self.ui.tbl_items.setItem(row_n, 1, itm(self.ui.txt_outcome_rsd.text()))
        self.ui.tbl_items.setItem(row_n, 2, itm(self.ui.txt_income_eur.text()))
        self.ui.tbl_items.setItem(row_n, 3, itm(self.ui.txt_outcome_eur.text()))
        
        a = self.get_date_from_dt_date()
        self.ui.tbl_items.setItem(row_n, 4, itm(a))
        
        self.ui.tbl_items.setItem(row_n, 5, itm(self.ui.txt_exchange.text()))
        self.ui.tbl_items.setItem(row_n, 6, itm(self.ui.txt_description.text()))
        self.ui.tbl_items.setItem(row_n, 7, itm(self.ui.cmb_event_type.currentText()))
        self.ui.tbl_items.setItem(row_n, 8, itm(self.ui.cmb_partner.currentText()))
        self.ui.tbl_items.setItem(row_n, 9, itm(self.ui.cmb_place.currentText()))

        # Populate horizontal header
        hd = []
        hd.append(self.conn.lang("add_event_lbl_income_rsd", self.active_lang))
        hd.append(self.conn.lang("add_event_lbl_outcome_rsd", self.active_lang))
        hd.append(self.conn.lang("add_event_lbl_income_eur", self.active_lang))
        hd.append(self.conn.lang("add_event_lbl_outcome_eur", self.active_lang))
        hd.append(self.conn.lang("add_event_lbl_date", self.active_lang))
        hd.append(self.conn.lang("add_event_lbl_exchange", self.active_lang))
        hd.append(self.conn.lang("add_event_lbl_description", self.active_lang))
        hd.append(self.conn.lang("add_event_lbl_event_type", self.active_lang))
        hd.append(self.conn.lang("add_event_lbl_partner", self.active_lang))
        hd.append(self.conn.lang("add_event_lbl_place", self.active_lang))
        self.ui.tbl_items.setHorizontalHeaderLabels(hd)
        self.ui.txt_outcome_rsd.setFocus()

        # Add value to cmb_partner if needed
        a = self.ui.cmb_partner.currentText()
        a_true = False
        for i in range(self.ui.cmb_partner.count()):
            if self.ui.cmb_partner.itemText(i) == a:
                a_true = True
                break
        if not a_true:
            self.ui.cmb_partner.addItem(a)
        # Clear money fields
        self.ui.txt_income_eur.setText("")
        self.ui.txt_income_rsd.setText("")
        self.ui.txt_outcome_eur.setText("")
        self.ui.txt_outcome_rsd.setText("")

    def get_date_from_dt_date(self):
        date_obj = self.ui.dt_date.date()
        d = str(date_obj.day())
        m = str(date_obj.month())
        y = str(date_obj.year())
        if len(d) == 1:
            d = "0" + d
        if len(m) == 1:
            m = "0" + m
        datum = d + "." + m + "." + y + "."
        return datum
    
    def populate_cmb_event_type(self, current_id=0):
        self.ui.cmb_event_type.clear()
        self.event_types = self.user.get_event_type_all()
        for i in range(len(self.event_types)):
            self.ui.cmb_event_type.addItem(self.event_types[i][1], self.event_types[i][0])
        self.ui.btn_add.setEnabled(False)
        if len(self.event_types) > 0 and len(self.places) > 0:
            self.ui.btn_add.setEnabled(True)
        for i in range(self.ui.cmb_event_type.count()):
            if int(self.ui.cmb_event_type.itemData(i)) == current_id:
                self.ui.cmb_event_type.setCurrentIndex(i)
                break

    def populate_places(self, current_id=0):
        self.ui.cmb_place.clear()
        self.places = self.user.get_place_all()
        for i in range(len(self.places)):
            self.ui.cmb_place.addItem(self.places[i][1], self.places[i][0])
        self.ui.btn_add.setEnabled(False)
        if len(self.event_types) > 0 and len(self.places) > 0:
            self.ui.btn_add.setEnabled(True)
        for i in range(self.ui.cmb_place.count()):
            if int(self.ui.cmb_place.itemData(i)) == current_id:
                self.ui.cmb_place.setCurrentIndex(i)
                break

    def date_today_object(self):
        datum = self.conn.get_current_date()
        d = int(datum[:2])
        m = int(datum[3:5])
        y = int(datum[6:10])
        dd = QtCore.QDate(y,m,d)
        return dd

    def btn_save_click(self):
        # Confirm save
        msg_title = self.conn.lang("add_event_caption", self.active_lang)
        msg_text = self.conn.lang("add_event_save_confirm_msg_text", self.active_lang)
        result = QtWidgets.QMessageBox.question(self, msg_title, msg_text, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if result == QtWidgets.QMessageBox.No:
            return
        # Save user position
        if self.ui.cmb_event_type.count() > 0:
            self.conn.set_setting_data("add_event_cmb_event_type", self.ui.cmb_event_type.currentText(), self.ui.cmb_event_type.currentData(), self.active_user_id)
        if self.ui.cmb_place.count() > 0:
            self.conn.set_setting_data("add_event_cmb_places", self.ui.cmb_place.currentText(), self.ui.cmb_place.currentData(), self.active_user_id)
        if self.ui.cmb_partner.count() > 0:
            self.conn.set_setting_data("add.event_cmb_partner", self.ui.cmb_partner.currentText(), int(self.ui.cmb_partner.currentIndex()), self.active_user_id)
        self.conn.set_setting_data("kurs", self.ui.txt_exchange.text(), user_id=self.active_user_id)

        # Check if data is valid
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(self.conn.lang("add_event_msg_caption", self.active_lang))
        for i in range(self.ui.tbl_items.rowCount()):
            if not self.ui.tbl_items.isRowHidden(i):
                i_rsd = self.ui.tbl_items.item(i,0).text().strip()
                o_rsd = self.ui.tbl_items.item(i,1).text().strip()
                i_eur = self.ui.tbl_items.item(i,2).text().strip()
                o_eur = self.ui.tbl_items.item(i,3).text().strip()
                kurs = self.ui.tbl_items.item(i,5).text().strip()
                datum = self.ui.tbl_items.item(i,4).text()
                vrsta = self.ui.tbl_items.item(i,7).text()
                mesto = self.ui.tbl_items.item(i,9).text()
                if not self.conn.is_decimal(i_rsd):
                    msg_txt = self.conn.lang("add_event_lbl_income_rsd", self.active_lang) + " - " + self.conn.lang("must_be_numeric", self.active_lang)
                    msg.setText(msg_txt)
                    msg.exec_()
                    return
                elif not self.conn.is_decimal(o_rsd):
                    msg_txt = self.conn.lang("add_event_lbl_outcome_rsd", self.active_lang) + " - " + self.conn.lang("must_be_numeric", self.active_lang)
                    msg.setText(msg_txt)
                    msg.exec_()
                    return
                elif not self.conn.is_decimal(i_eur):
                    msg_txt = self.conn.lang("add_event_lbl_income_eur", self.active_lang) + " - " + self.conn.lang("must_be_numeric", self.active_lang)
                    msg.setText(msg_txt)
                    msg.exec_()
                    return
                elif not self.conn.is_decimal(o_eur):
                    msg_txt = self.conn.lang("add_event_lbl_outcome_eur", self.active_lang) + " - " + self.conn.lang("must_be_numeric", self.active_lang)
                    msg.setText(msg_txt)
                    msg.exec_()
                    return
                elif not self.conn.is_decimal(kurs):
                    msg_txt = self.conn.lang("add_event_lbl_exchange", self.active_lang) + " - " + self.conn.lang("must_be_numeric", self.active_lang)
                    msg.setText(msg_txt)
                    msg.exec_()
                    return
                elif not self.conn.is_date_valid(datum):
                    msg_txt = self.conn.lang("add_event_lbl_date", self.active_lang) + " - " + self.conn.lang("date_must_be_in_format", self.active_lang)
                    msg.setText(msg_txt)
                    msg.exec_()
                    return
                elif len(self.user.get_event_type_all(event_type_naziv=vrsta)) == 0:
                    msg_txt = self.conn.lang("event_type_does_not_exist", self.active_lang) + " - " + vrsta
                    msg.setText(msg_txt)
                    msg.exec_()
                    return
                elif len(self.user.get_place_all(place_naziv=mesto)) == 0:
                    msg_txt = self.conn.lang("place_does_not_exist", self.active_lang) + " - " + mesto
                    msg.setText(msg_txt)
                    msg.exec_()
                    return

        # Fill dictionary with data for every record, and call add_event
        ev = {}
        for i in range(self.ui.tbl_items.rowCount()):
            if not self.ui.tbl_items.isRowHidden(i):
                ev.clear()
                ev["prihod_rsd"] = float(self.ui.tbl_items.item(i,0).text())
                ev["rashod_rsd"] = float(self.ui.tbl_items.item(i,1).text())
                ev["prihod_eur"] = float(self.ui.tbl_items.item(i,2).text())
                ev["rashod_eur"] = float(self.ui.tbl_items.item(i,3).text())
                ev["datum"] = self.ui.tbl_items.item(i,4).text()
                ev["datum_int"] = self.conn.date_to_integer(self.ui.tbl_items.item(i,4).text())
                ev["vreme_upisa"] = self.conn.get_current_date(get_date_and_time=True)
                ev["kurs"] = float(self.ui.tbl_items.item(i,5).text())
                ev["opis"] = self.ui.tbl_items.item(i,6).text()
                ev["uredjaj_id"] = 0
                vrsta = self.user.get_event_type_all(event_type_naziv=self.ui.tbl_items.item(i,7).text())
                ev["vrsta_id"] = vrsta[0][0]
                ev["partner"] = self.ui.tbl_items.item(i,8).text()
                mesto = self.user.get_place_all(place_naziv=self.ui.tbl_items.item(i,9).text())
                ev["mesto_id"] = mesto[0][0]
                ev["wallet_id"] = 0
                self.user.add_event(ev)
        self.log.write_log("Finished adding data to database. User: " + self.active_user_name)
        
        # Close Add event window
        self.close()



    def btn_cancel_click(self):
        self.log.write_log("Add event finished.")
        self.close()


    def retranslateUi(self):
        self.ui.lbl_caption.setText(self.conn.lang("add_event_lbl_caption", self.active_lang))
        self.ui.lbl_main_wallet.setText(self.conn.lang("add_event_lbl_main_wallet", self.active_lang))
        self.ui.lbl_user.setText(self.conn.lang("add_event_lbl_user", self.active_lang) + self.active_user_name)
        self.ui.lbl_app.setText(self.conn.lang("add_event_lbl_app", self.active_lang))
        self.ui.lbl_income_rsd.setText(self.conn.lang("add_event_lbl_income_rsd", self.active_lang))
        self.ui.lbl_outcome_rsd.setText(self.conn.lang("add_event_lbl_outcome_rsd", self.active_lang))
        self.ui.lbl_income_eur.setText(self.conn.lang("add_event_lbl_income_eur", self.active_lang))
        self.ui.lbl_outcome_eur.setText(self.conn.lang("add_event_lbl_outcome_eur", self.active_lang))
        self.ui.lbl_date.setText(self.conn.lang("add_event_lbl_date", self.active_lang))
        self.ui.lbl_description.setText(self.conn.lang("add_event_lbl_description", self.active_lang))
        self.ui.lbl_event_type.setText(self.conn.lang("add_event_lbl_event_type", self.active_lang))
        self.ui.lbl_place.setText(self.conn.lang("add_event_lbl_place", self.active_lang))
        self.ui.btn_new_event_type.setText(self.conn.lang("add_event_btn_new_event_type", self.active_lang))
        self.ui.btn_new_place.setText(self.conn.lang("add_event_btn_new_place", self.active_lang))
        self.ui.btn_save.setText(self.conn.lang("add_event_btn_save", self.active_lang))
        self.ui.btn_date_pick.setText(self.conn.lang("add_event_btn_date_pick", self.active_lang))
        self.ui.btn_cancel.setText(self.conn.lang("btn_cancel", self.active_lang))
        self.ui.btn_add.setText(self.conn.lang("add_event_btn_add", self.active_lang))
        self.ui.lbl_items.setText(self.conn.lang("add_event_lbl_items", self.active_lang))
        self.ui.lbl_exchange.setText(self.conn.lang("add_event_lbl_exchange", self.active_lang))
        self.ui.lbl_partner.setText(self.conn.lang("add_event_lbl_partner", self.active_lang))

class Calendar(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = cal_ui.Ui_Dialog()
        self.conn = connection.ConnStart()
        self.setWindowFlag(QtCore.Qt.Dialog)
        self.ui.setupUi(self)
    
    def setup_ui(self, date_obj, active_lang):
        # Set arguments passed
        self.active_lang = active_lang
        
        # Set events
        self.ui.btn_cancel.clicked.connect(self.btn_cancel_click)
        self.ui.btn_ok.clicked.connect(self.btn_ok_click)
        self.ui.cld_datum.activated.connect(self.calendar_activated)

        # Set Fixed size window
        self.setFixedSize(300, 260)

        # Fill labels        
        self.retranslateUi()

        # Set date in calendar
        self.ui.cld_datum.setSelectedDate(date_obj)

        # Create var to store date selected
        self.date_selected = ""

        self.show()
        self.exec_()
        
        return self.date_selected

    def setup_calendar(self):
        self.ui.cld_datum = CalendarWidg(self)
        self.ui.cld_datum.setGeometry(QtCore.QRect(0, 0, 300, 221))
        self.ui.cld_datum.setLocale(QtCore.QLocale(QtCore.QLocale.Serbian, QtCore.QLocale.Serbia))
        self.ui.cld_datum.setGridVisible(True)
        self.ui.cld_datum.setObjectName("cld_datum")

    def calendar_activated(self):
        self.btn_ok_click()

    def btn_ok_click(self):
        self.date_selected = self.ui.cld_datum.selectedDate()
        self.close()

    def btn_cancel_click(self):
        self.date_selected = ""
        self.close()

    def retranslateUi(self):
        self.setWindowTitle(self.conn.lang("date_select", self.active_lang))
        self.ui.btn_ok.setText(self.conn.lang("btn_ok", self.active_lang))
        self.ui.btn_cancel.setText(self.conn.lang("btn_cancel", self.active_lang))
    
class AddEventType(QtWidgets.QDialog):
    def __init__(self, user_id, user_lang, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set variables
        self.active_user_id = user_id
        self.active_lang = user_lang
        
        self.conn = connection.ConnStart()
        self.log = log_cls.LogData()
        self.user = connection.User(self.active_user_id)
        self.ui = add_type_ui.Ui_Dialog()

        self.event_type_list = []  # List of event types from database

        # Write log
        self.log.write_log("Add event type started...")


    def setup_ui(self):
        # Setup GUI
        self.ui.setupUi(self)
        self.setWindowFlag(QtCore.Qt.Dialog)
        self.ui.btn_add.setEnabled(False)
        # Events
        self.ui.btn_ok.clicked.connect(self.btn_ok_click)
        self.ui.txt_name.textEdited.connect(self.txt_name_changed)
        self.ui.btn_edit.clicked.connect(self.btn_edit_click)
        self.ui.lst_event_type.itemDoubleClicked.connect(self.btn_edit_click)
        self.ui.btn_add.clicked.connect(self.btn_add_click)
        self.ui.btn_delete.clicked.connect(self.btn_delete_click)
        # Fill GUI text
        self.retranslateUi()
        # Populate list
        self.populate_list()
        # Show dialog
        self.show()
        self.exec_()

    def btn_delete_click(self):
        if self.ui.lst_event_type.currentItem() == None:
            self.ui.lbl_warrning.setText(self.conn.lang("add_event_type_lbl_warrning1", self.active_lang))
            return
        row = self.ui.lst_event_type.row(self.ui.lst_event_type.currentItem())
        event_type_id = self.event_type_list[row][0]
        if not self.user.is_safe_to_delete_event_type(event_type_id):
            self.ui.lbl_warrning.setText(self.conn.lang("add_event_type_lbl_warrning3", self.active_lang))
            return
        msg_caption = self.conn.lang("add_event_type_delete_q_caption", self.active_lang)
        msg_text = self.conn.lang("add_event_type_delete_q_text", self.active_lang) + self.event_type_list[row][1] + " ?"
        result = QtWidgets.QMessageBox.question(None, msg_caption, msg_text, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if result == QtWidgets.QMessageBox.Yes:
            self.user.delete_event_type(e_t_id=event_type_id)
            self.populate_list()
        else:
            return

    def btn_add_click(self):
        text = self.ui.txt_name.text()
        if len(text) > 100:
            self.ui.lbl_warrning.setText(self.conn.lang("add_event_type_lbl_warrning4", self.active_lang))
            return
        self.ui.lbl_warrning.setText("")
        result = self.user.get_event_type_all(event_type_naziv=self.ui.txt_name.text())
        if len(result) > 0:
            self.ui.lbl_warrning.setText(self.conn.lang("add_event_type_lbl_warrning2", self.active_lang))
            return
        self.user.add_event_type(self.ui.txt_name.text())
        self.populate_list()
        self.ui.txt_name.setText("")
        self.ui.btn_add.setEnabled(False)

    def btn_edit_click(self):
        self.ui.lbl_warrning.setText("")
        
        msg_caption = self.conn.lang("add_event_type_msg_edit_caption", self.active_lang)
        msg_text = self.conn.lang("add_event_type_msg_edit_text", self.active_lang)
        if self.ui.lst_event_type.currentItem() == None:
            msg_place_text = ""
            self.ui.lbl_warrning.setText(self.conn.lang("add_event_type_lbl_warrning1", self.active_lang))
            return
        else:
            row = self.ui.lst_event_type.row(self.ui.lst_event_type.currentItem())
            ev_type_id = self.event_type_list[row][0]
            msg_place_text = self.ui.lst_event_type.currentItem().text()
            msg_caption = msg_caption + str(ev_type_id)
        
        text, ok = QtWidgets.QInputDialog.getText(self.ui.lst_event_type, msg_caption, msg_text, QtWidgets.QLineEdit.Normal, msg_place_text)
        if ok:
            if len(text) > 100:
                self.ui.lbl_warrning.setText(self.conn.lang("add_event_type_lbl_warrning4", self.active_lang))
                return
            self.user.set_event_type(evnt_type_id=ev_type_id, event_type_new_name=text)
            self.populate_list()
            self.log.write_log("Event type edited.")

    def txt_name_changed(self, event):
        if self.ui.txt_name.text() != "":
            self.ui.btn_add.setEnabled(True)
        else:
            self.ui.btn_add.setEnabled(False)
        self.ui.lbl_warrning.setText("")

    def populate_list(self):
        self.event_type_list.clear()
        self.event_type_list = self.user.get_event_type_all()
        self.ui.lst_event_type.clear()
        for i in self.event_type_list:
            self.ui.lst_event_type.addItem(i[1])
        if len(self.event_type_list) == 0:
            self.ui.btn_delete.setEnabled(False)
            self.ui.btn_edit.setEnabled(False)
        else:
            self.ui.btn_delete.setEnabled(True)
            self.ui.btn_edit.setEnabled(True)

    def btn_ok_click(self):
        self.close()

    def retranslateUi(self):
        self.setWindowTitle(self.conn.lang("add_event_type_caption", self.active_lang))
        self.ui.lbl_caption.setText(self.conn.lang("add_event_type_lbl_caption", self.active_lang))
        self.ui.lbl_help.setText(self.conn.lang("add_event_type_lbl_help", self.active_lang))
        self.ui.lbl_app.setText(self.conn.lang("add_event_lbl_app", self.active_lang))
        self.ui.lbl_new_type.setText(self.conn.lang("add_event_type_lbl_new_type", self.active_lang))
        self.ui.lbl_name.setText(self.conn.lang("add_event_type_lbl_name", self.active_lang))
        self.ui.btn_ok.setText(self.conn.lang("btn_ok", self.active_lang))
        self.ui.lbl_event_types.setText(self.conn.lang("add_event_type_lbl_event_types", self.active_lang))
        self.ui.btn_add.setText(self.conn.lang("main_btn_filter_add", self.active_lang))
        self.ui.lbl_warrning.setText("")
        self.ui.btn_delete.setText(self.conn.lang("btn_delete", self.active_lang))
        self.ui.btn_edit.setText(self.conn.lang("btn_edit", self.active_lang))

class AddPlace(QtWidgets.QDialog):
    def __init__(self, user_id, user_lang, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set variables
        self.active_user_id = user_id
        self.active_lang = user_lang
        
        self.conn = connection.ConnStart()
        self.log = log_cls.LogData()
        self.user = connection.User(self.active_user_id)
        self.ui = add_place_ui.Ui_Dialog()

        self.place_list = []  # List of event types from database

        # Write log
        self.log.write_log("Add event place started...")


    def setup_ui(self):
        # Setup GUI
        self.ui.setupUi(self)
        self.setWindowFlag(QtCore.Qt.Dialog)
        self.ui.btn_add.setEnabled(False)
        # Events
        self.ui.btn_ok.clicked.connect(self.btn_ok_click)
        self.ui.txt_name.textEdited.connect(self.txt_name_changed)
        self.ui.btn_edit.clicked.connect(self.btn_edit_click)
        self.ui.lst_place.itemDoubleClicked.connect(self.btn_edit_click)
        self.ui.btn_add.clicked.connect(self.btn_add_click)
        self.ui.btn_delete.clicked.connect(self.btn_delete_click)
        # Fill GUI text
        self.retranslateUi()
        # Populate list
        self.populate_list()
        # Show dialog
        self.show()
        self.exec_()

    def btn_delete_click(self):
        if self.ui.lst_place.currentItem() == None:
            self.ui.lbl_warrning.setText(self.conn.lang("add_place_lbl_warrning1", self.active_lang))
            return
        row = self.ui.lst_place.row(self.ui.lst_place.currentItem())
        place_id = self.place_list[row][0]
        if not self.user.is_safe_to_delete_place(place_id):
            self.ui.lbl_warrning.setText(self.conn.lang("add_place_lbl_warrning3", self.active_lang))
            return
        msg_caption = self.conn.lang("add_place_delete_q_caption", self.active_lang)
        msg_text = self.conn.lang("add_place_delete_q_text", self.active_lang) + self.place_list[row][1] + " ?"
        result = QtWidgets.QMessageBox.question(None, msg_caption, msg_text, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)        
        if result == QtWidgets.QMessageBox.Yes:
            self.user.delete_place(old_place_id=place_id)
            self.populate_list()
        else:
            return

    def btn_add_click(self):
        text = self.ui.txt_name.text()
        if len(text) > 255:
            self.ui.lbl_warrning.setText(self.conn.lang("add_place_lbl_warrning4", self.active_lang))
            return
        self.ui.lbl_warrning.setText("")
        result = self.user.get_place_all(place_naziv=self.ui.txt_name.text())
        if len(result) > 0:
            self.ui.lbl_warrning.setText(self.conn.lang("add_place_lbl_warrning2", self.active_lang))
            return
        self.user.add_place(self.ui.txt_name.text())
        self.populate_list()
        self.ui.txt_name.setText("")
        self.ui.btn_add.setEnabled(False)

    def btn_edit_click(self):
        self.ui.lbl_warrning.setText("")
        
        msg_caption = self.conn.lang("add_event_type_msg_edit_caption", self.active_lang)
        msg_text = self.conn.lang("add_event_type_msg_edit_text", self.active_lang)
        if self.ui.lst_place.currentItem() == None:
            msg_place_text = ""
            self.ui.lbl_warrning.setText(self.conn.lang("add_place_lbl_warrning1", self.active_lang))
            return
        else:
            row = self.ui.lst_place.row(self.ui.lst_place.currentItem())
            place_id = self.place_list[row][0]
            msg_place_text = self.ui.lst_place.currentItem().text()
            msg_caption = msg_caption + str(place_id)
        
        text, ok = QtWidgets.QInputDialog.getText(self.ui.lst_place, msg_caption, msg_text, QtWidgets.QLineEdit.Normal, msg_place_text)
        if ok:
            if len(text) > 255:
                self.ui.lbl_warrning.setText(self.conn.lang("add_place_lbl_warrning4", self.active_lang))
                return
            self.user.set_place(plac_id=place_id, place_new_name=text)
            self.populate_list()
            self.log.write_log("Place edited.")

    def txt_name_changed(self, event):
        if self.ui.txt_name.text() != "":
            self.ui.btn_add.setEnabled(True)
        else:
            self.ui.btn_add.setEnabled(False)
        self.ui.lbl_warrning.setText("")

    def populate_list(self):
        self.place_list.clear()
        self.place_list = self.user.get_place_all()
        self.ui.lst_place.clear()
        for i in self.place_list:
            self.ui.lst_place.addItem(i[1])
        if len(self.place_list) == 0:
            self.ui.btn_delete.setEnabled(False)
            self.ui.btn_edit.setEnabled(False)
        else:
            self.ui.btn_delete.setEnabled(True)
            self.ui.btn_edit.setEnabled(True)

    def btn_ok_click(self):
        self.close()

    def retranslateUi(self):
        self.setWindowTitle(self.conn.lang("add_place_caption", self.active_lang))
        self.ui.lbl_caption.setText(self.conn.lang("add_place_lbl_caption", self.active_lang))
        self.ui.lbl_help.setText(self.conn.lang("add_place_lbl_help", self.active_lang))
        self.ui.lbl_app.setText(self.conn.lang("add_event_lbl_app", self.active_lang))
        self.ui.lbl_new_place.setText(self.conn.lang("add_place_lbl_new_type", self.active_lang))
        self.ui.lbl_name.setText(self.conn.lang("add_place_lbl_name", self.active_lang))
        self.ui.btn_ok.setText(self.conn.lang("btn_ok", self.active_lang))
        self.ui.lbl_places.setText(self.conn.lang("add_place_lbl_places", self.active_lang))
        self.ui.btn_add.setText(self.conn.lang("main_btn_filter_add", self.active_lang))
        self.ui.lbl_warrning.setText("")
        self.ui.btn_delete.setText(self.conn.lang("btn_delete", self.active_lang))
        self.ui.btn_edit.setText(self.conn.lang("btn_edit", self.active_lang))

