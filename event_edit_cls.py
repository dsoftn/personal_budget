from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

# import login  # Login screen
import log_cls  # Handle 'log.txt' file
import connection  # Handle 'start_up.db' and user database
import add_cls  # Handle add eventplace, add eventtype, pick date...
import event_edit_ui  # GUI for editi/view events


class ViewEditEvent(QtWidgets.QDialog):
    def __init__(self, user_id, user_name, user_language, event_id, open_for_view=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setup variables
        self.active_user_id = user_id
        self.active_user_name = user_name
        self.active_lang = user_language
        self.active_event_id = event_id
        self.opened_for_view = open_for_view
        self.events_list_all = []  # List of all events
        self.active_event_data = []  # Active event from events_list
        self.active_user_list_of_event_ids = []  # List od event ID-s provided by caller function
        self.active_event_data_index = 0
        self.confirm_edit = False  # If Save is clicked this is true and returns record
        # Setup db connection, log, language...
        self.conn = connection.ConnStart()
        self.user = connection.User(self.active_user_id)
        self.log = log_cls.LogData()
        # Load gui
        self.ui = event_edit_ui.Ui_Dialog()
        self.ui.setupUi(self)


    def setup_gui(self, list_of_IDs_to_show=[]):
        # Set window size fixed
        self.setFixedSize(957, 500)
        self.setWindowFlag(QtCore.Qt.Dialog)
        self.setWindowModality(Qt.ApplicationModal)
        # Load all events if list of IDs not provided
        if len(list_of_IDs_to_show) == 0:
            self.active_user_list_of_event_ids = [self.active_event_id]
        else:
            self.active_user_list_of_event_ids = list_of_IDs_to_show
        # Set widgets visible if edit or view mode is selected
        self.enable_needed_widgets()
        # Set connections for buttons and other widgets
        self.ui.btn_left.clicked.connect(self.btn_left_click)
        self.ui.btn_right.clicked.connect(self.btn_right_click)
        self.ui.btn_date_pick.clicked.connect(self.btn_date_pick_click)
        self.ui.btn_new_event_type.clicked.connect(self.btn_new_event_type_click)
        self.ui.btn_new_place.clicked.connect(self.btn_new_place_click)
        self.ui.btn_cancel.clicked.connect(self.btn_cancel_click)
        self.ui.btn_save.clicked.connect(self.btn_save_click)
        self.installEventFilter(self)
        # Set text to widgets
        self.retranslateUi()
        # Load all events and select one to edit/view
        number_of_records = self.get_event_data_from_database()                
        if number_of_records != 1:
            self.log.write_log(f"Error. Event data is not loaded. Number of events selected = {str(len(self.active_event_data))}")
            self.close()
            return
        # Display selected event in dialog
        if self.opened_for_view:
            self.log.write_log("View event started.")
            self.view_load_event()
            self.ui.cmb_event_type.setFocus()
        else:
            self.log.write_log("Edit event started.")
            self.edit_load_event()


        self.show()
        self.exec_()
        
        if self.opened_for_view:
            self.log.write_log("View event finished.")
            return self.active_event_id
        else:
            self.log.write_log("Edit event finished.")
            if self.confirm_edit:
                return self.active_event_data
            else:
                return ""


    def eventFilter(self, a0: QtCore.QObject, a1: QtCore.QEvent) -> bool:
        if a1.type() == QtCore.QEvent.KeyPress:
            if a1.key() == QtCore.Qt.Key_Escape:
                self.btn_cancel_click()
            elif a1.key() == QtCore.Qt.Key_Left:
                self.btn_left_click()
            elif a1.key() == QtCore.Qt.Key_Right:
                self.btn_right_click()
        return super().eventFilter(a0, a1)

    def btn_save_click(self):
        # Fill event object with data
        ev = {}
        ev["trosak_id"] = self.active_event_id
        msg_title = self.conn.lang("event_edit_win_title", self.active_lang)
        msg_text = self.conn.lang("edit_event_save_msg_number", self.active_lang)
        # Income RSD
        a = self.ui.txt_income_rsd.text()
        if not self.conn.is_decimal(a):
            msg = QtWidgets.QMessageBox()
            msg1 = self.conn.lang("add_event_lbl_income_rsd", self.active_lang) + msg_text
            result = msg.information(None, msg_title, msg1, QtWidgets.QMessageBox.Ok)
            return
        ev["prihod_rsd"] = float(self.ui.txt_income_rsd.text())
        # Outcome RSD
        a = self.ui.txt_outcome_rsd.text()
        if not self.conn.is_decimal(a):
            msg = QtWidgets.QMessageBox()
            msg1 = self.conn.lang("add_event_lbl_outcome_rsd", self.active_lang) + msg_text
            result = msg.information(None, msg_title, msg1, QtWidgets.QMessageBox.Ok)
            return
        ev["rashod_rsd"] = float(self.ui.txt_outcome_rsd.text())
        # Income EUR
        a = self.ui.txt_income_eur.text()
        if not self.conn.is_decimal(a):
            msg = QtWidgets.QMessageBox()
            msg1 = self.conn.lang("add_event_lbl_income_eur", self.active_lang) + msg_text
            result = msg.information(None, msg_title, msg1, QtWidgets.QMessageBox.Ok)
            return
        ev["prihod_eur"] = float(self.ui.txt_income_eur.text())
        # Outcome EUR
        a = self.ui.txt_outcome_eur.text()
        if not self.conn.is_decimal(a):
            msg = QtWidgets.QMessageBox()
            msg1 = self.conn.lang("add_event_lbl_outcome_eur", self.active_lang) + msg_text
            result = msg.information(None, msg_title, msg1, QtWidgets.QMessageBox.Ok)
            return
        ev["rashod_eur"] = float(self.ui.txt_outcome_eur.text())
        # Exchange rate
        a = self.ui.txt_exchange.text()
        if not self.conn.is_decimal(a):
            msg = QtWidgets.QMessageBox()
            msg1 = self.conn.lang("add_event_lbl_exchange", self.active_lang) + msg_text
            result = msg.information(None, msg_title, msg1, QtWidgets.QMessageBox.Ok)
            return
        ev["kurs"] = float(self.ui.txt_exchange.text())
        # Date
        ev["datum"] = add_cls.EventAdd.get_date_from_dt_date(self)
        ev["datum_int"] = self.conn.date_to_integer(ev["datum"])
        # Description, partner
        ev["opis"] = self.ui.txt_description.text()
        ev["partner"] = self.ui.cmb_partner.currentText()
        # Event type, place, wallet
        ev["vrsta_id"] = self.ui.cmb_event_type.currentData()
        ev["mesto_id"] = self.ui.cmb_place.currentData()
        ev["wallet_id"] = 0
        # Update data
        self.user.set_event(ev)
        # Write log and confirm edit
        self.log.write_log(f"Event updated. Event ID: {str(self.active_event_id)}  User: {self.active_user_name}")
        self.confirm_edit = True
        # Load event again with updated data
        events = self.user.get_event_all()
        for i in events:
            if i[0] == self.active_event_id:
                self.active_event_data = i
                break
        self.close()


    def btn_cancel_click(self):
        self.close()

    def btn_new_event_type_click(self):
        event_type = add_cls.AddEventType(self.active_user_id, self.active_lang)
        event_type.setup_ui()
        self.populate_cmb_event_type()

    def btn_new_place_click(self):
        place = add_cls.AddPlace(self.active_user_id, self.active_lang)
        place.setup_ui()
        self.populate_places()

    def btn_date_pick_click(self):
        calendar_obj = add_cls.Calendar()
        datum = calendar_obj.setup_ui(self.ui.dt_date.date(), self.active_lang)
        if datum != "":
            self.ui.dt_date.setDate(datum)

    def edit_load_event(self):
        # Set labels in blue frame:
        self.ui.lbl_event_id.setText(self.conn.lang("event_edit_lbl_event_id", self.active_lang) + str(self.active_event_id))
        self.ui.lbl_user_data.setText(self.active_user_name)
        self.ui.lbl_created_data.setText(self.active_event_data[7])
        q = self.conn.lang("event_edit_created", self.active_lang) + self.user.date_info_obj(self.active_event_data[7][:11])["day_name"]
        self.ui.lbl_created.setText(q)
        devices = self.user.get_device_all(device_id=self.active_event_data[11])
        q = f"ID: {devices[0][2]}, {devices[0][1]}"
        self.ui.lbl_device_id.setText(q)
        q = devices[0][4]
        self.ui.lbl_device_description.setText(q)
        if self.active_event_data[14] == 0:
            wallet = self.conn.lang("add_event_lbl_main_wallet", self.active_lang)
        else:
            print ("DODATI ako je drugi wallet sta da radi")
        self.ui.lbl_wallet_data.setText(wallet)
        # Set date
        y,m,d = self.user.parse_date_y_m_d(self.active_event_data[5])
        datum_obj = QtCore.QDate(y,m,d)
        self.ui.dt_date.setDate(datum_obj)
        # Set income/outcome data
        self.ui.txt_income_rsd.setText(str(self.active_event_data[1]))
        self.ui.txt_outcome_rsd.setText(str(self.active_event_data[2]))
        self.ui.txt_income_eur.setText(str(self.active_event_data[3]))
        self.ui.txt_outcome_eur.setText(str(self.active_event_data[4]))
        # Set partner, description data
        self.ui.txt_description.setText(self.active_event_data[9])
        self.populate_partners()
        self.ui.cmb_partner.setCurrentText(self.active_event_data[10])
        # Set data for exchange
        self.ui.txt_exchange.setText(str(self.active_event_data[8]))
        # Set data for event_type and place comboboxes
        self.populate_cmb_event_type(current_id=self.active_event_data[12])
        self.populate_places(current_id=self.active_event_data[13])

    def populate_cmb_event_type(self, current_id=0):
        self.ui.cmb_event_type.clear()
        self.event_types = self.user.get_event_type_all()
        for i in range(len(self.event_types)):
            self.ui.cmb_event_type.addItem(self.event_types[i][1], self.event_types[i][0])
        for i in range(self.ui.cmb_event_type.count()):
            if int(self.ui.cmb_event_type.itemData(i)) == current_id:
                self.ui.cmb_event_type.setCurrentIndex(i)
                break

    def populate_places(self, current_id=0):
        self.ui.cmb_place.clear()
        self.places = self.user.get_place_all()
        for i in range(len(self.places)):
            self.ui.cmb_place.addItem(self.places[i][1], self.places[i][0])
        for i in range(self.ui.cmb_place.count()):
            if int(self.ui.cmb_place.itemData(i)) == current_id:
                self.ui.cmb_place.setCurrentIndex(i)
                break

    def populate_partners(self):
        partner_list = self.user.get_partner_list_unique(sort_data=True)
        for i in partner_list:
            self.ui.cmb_partner.addItem(i[0])


    def btn_left_click(self):
        # Check if we at beginning of list
        if self.active_event_data_index == 0:
            return
        # Load previous event from list
        self.active_event_data_index -= 1
        self.active_event_data = self.events_list_all[self.active_event_data_index]
        self.active_event_id = self.events_list_all[self.active_event_data_index][0]
        # Populate widgets
        self.view_load_event()

    def btn_right_click(self):
        # Check if we at the end of list
        if self.active_event_data_index == (len(self.events_list_all) - 1):
            return
        # Load next event from list
        self.active_event_data_index += 1
        self.active_event_data = self.events_list_all[self.active_event_data_index]
        self.active_event_id = self.events_list_all[self.active_event_data_index][0]
        # Populate widgets
        self.view_load_event()


    def get_event_data_from_database(self):
        # Load events from database and select needed one
        result = self.user.get_event_all()
        number_of_records = 0
        index_num = -1
        for i in result:
            if i[0] in self.active_user_list_of_event_ids:
                index_num += 1
                self.events_list_all.append(i)
            if i[0] == self.active_event_id:
                self.active_event_data = i
                number_of_records += 1
                self.active_event_data_index = index_num
            
        return number_of_records


    def view_load_event(self):
        # Set enabled or disabled navigation buttons
        self.ui.btn_left.setEnabled(True)
        self.ui.btn_right.setEnabled(True)
        if self.active_event_data_index == 0:
            self.ui.btn_left.setEnabled(False)
        elif self.active_event_data_index == (len(self.events_list_all) - 1):
            self.ui.btn_right.setEnabled(False)
        # Update lbl_event_position
        lbl_pos = self.conn.lang("view_event_lbl_position", self.active_lang) + str(self.active_event_data_index + 1) + " / " + str(len(self.events_list_all))
        self.ui.lbl_event_position.setText(lbl_pos)
        # Populate widgets with event data and set BG color for each
        # Set labels in blue frame:
        self.ui.lbl_event_id.setText(self.conn.lang("event_edit_lbl_event_id", self.active_lang) + str(self.active_event_id))
        self.ui.lbl_user_data.setText(self.active_user_name)
        self.ui.lbl_created_data.setText(self.active_event_data[7])
        q = self.conn.lang("event_edit_created", self.active_lang) + self.user.date_info_obj(self.active_event_data[7][:11])["day_name"] 
        self.ui.lbl_created.setText(q)
        devices = self.user.get_device_all(device_id=self.active_event_data[11])
        q = f"ID: {devices[0][2]}, {devices[0][1]}"
        self.ui.lbl_device_id.setText(q)
        q = devices[0][4]
        self.ui.lbl_device_description.setText(q)
        if self.active_event_data[14] == 0:
            wallet = self.conn.lang("add_event_lbl_main_wallet", self.active_lang)
        else:
            print ("DODATI ako je drugi wallet sta da radi")
        self.ui.lbl_wallet_data.setText(wallet)
        # Set date
        y,m,d = self.user.parse_date_y_m_d(self.active_event_data[5])
        datum_obj = QtCore.QDate(y,m,d)
        self.ui.dt_date.setDate(datum_obj)
        # Set income/outcome bg color and data
        self._set_widget_bg_color(self.ui.txt_income_rsd, self.active_event_data[1])
        self.ui.txt_income_rsd.setText(str(self.active_event_data[1]))
        self._set_widget_bg_color(self.ui.txt_outcome_rsd, self.active_event_data[2])
        self.ui.txt_outcome_rsd.setText(str(self.active_event_data[2]))
        self._set_widget_bg_color(self.ui.txt_income_eur, self.active_event_data[3])
        self.ui.txt_income_eur.setText(str(self.active_event_data[3]))
        self._set_widget_bg_color(self.ui.txt_outcome_eur, self.active_event_data[4])
        self.ui.txt_outcome_eur.setText(str(self.active_event_data[4]))
        # Set partner, description bg color and data
        self._set_widget_bg_color(self.ui.lbl_view_counterpart, self.active_event_data[10])
        self.ui.lbl_view_counterpart.setText(self.active_event_data[10])
        self.ui.lbl_view_counterpart.setToolTip(self.active_event_data[10])
        self._set_widget_bg_color(self.ui.lbl_view_description, self.active_event_data[9])
        self.ui.lbl_view_description.setText(self.active_event_data[9])
        self.ui.lbl_view_description.setToolTip(self.active_event_data[9])
        # Set data for exchange
        self.ui.txt_exchange.setText(str(self.active_event_data[8]))
        # Set data for event_type and place comboboxes
        self.ui.cmb_event_type.clear()
        event_type_name = self.user.get_event_type_all(event_type_id=self.active_event_data[12])
        self.ui.cmb_event_type.addItem(event_type_name[0][1])
        self.ui.cmb_place.clear()
        place_name = self.user.get_place_all(place_id=self.active_event_data[13])
        self.ui.cmb_place.addItem(place_name[0][1])


    def _set_widget_bg_color(self, widget_obj, data):
        if isinstance(data, str):
            if data == "":
                result = self._inactive_obj(widget_obj, False)
            else:
                result = self._inactive_obj(widget_obj, True)
        else:
            if data == 0:
                result = self._inactive_obj(widget_obj, False)
            else:
                result = self._inactive_obj(widget_obj, True)
        return widget_obj


    def _inactive_obj(self, widget_object, set_active):
        if set_active:
            clr = 255
        else:
            clr = 85
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(clr, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(clr, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(clr, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(clr, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(clr, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(clr, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)
        widget_object.setPalette(palette)

        return widget_object

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        if a0.key() == QtCore.Qt.Key_Enter or a0.key() == QtCore.Qt.Key_Return:
            msg_title = self.conn.lang("event_edit_win_title", self.active_lang)
            msg_text = self.conn.lang("event_edit_msg_save_confirm_text", self.active_lang)
            result = QtWidgets.QMessageBox.question(None, msg_title, msg_text, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.Yes:
                self.btn_save_click()
                
    def enable_needed_widgets(self):
        if self.opened_for_view:
            self.ui.btn_save.setVisible(False)
            self.ui.btn_date_pick.setVisible(False)
            self.ui.btn_new_event_type.setVisible(False)
            self.ui.btn_new_place.setVisible(False)
        else:
            self.ui.btn_left.setVisible(False)
            self.ui.btn_right.setVisible(False)
            self.ui.lbl_view_counterpart.setVisible(False)
            self.ui.lbl_view_description.setVisible(False)
            self.ui.lbl_event_position.setVisible(False)
        self.ui.dt_date.setDisplayFormat("dd.MM.yyyy")
        
        
    def retranslateUi(self):
        if self.opened_for_view:
            self.setWindowTitle(self.conn.lang("event_edit_win_title_view", self.active_lang))
        else:
            self.setWindowTitle(self.conn.lang("event_edit_win_title", self.active_lang))
        self.ui.lbl_event_id.setText(self.conn.lang("event_edit_lbl_event_id", self.active_lang))
        self.ui.lbl_user.setText(self.conn.lang("event_edit_user", self.active_lang))
        self.ui.lbl_user_data.setText("")
        self.ui.lbl_created.setText(self.conn.lang("event_edit_created", self.active_lang))
        self.ui.lbl_created_data.setText("")
        self.ui.lbl_wallet_data.setText("")
        self.ui.lbl_wallet.setText(self.conn.lang("event_edit_wallet", self.active_lang))
        self.ui.lbl_app.setText(self.conn.lang("add_event_lbl_app", self.active_lang))
        self.ui.lbl_income_rsd.setText(self.conn.lang("add_event_lbl_income_rsd", self.active_lang))
        self.ui.lbl_outcome_rsd.setText(self.conn.lang("add_event_lbl_outcome_rsd", self.active_lang))
        self.ui.lbl_income_eur.setText(self.conn.lang("add_event_lbl_income_eur", self.active_lang))
        self.ui.lbl_outcome_eur.setText(self.conn.lang("add_event_lbl_outcome_eur", self.active_lang))
        self.ui.lbl_place.setText(self.conn.lang("add_event_lbl_place", self.active_lang))
        self.ui.lbl_event_type.setText(self.conn.lang("add_event_lbl_event_type", self.active_lang))
        self.ui.btn_new_event_type.setText(self.conn.lang("add_event_btn_new_event_type", self.active_lang))
        self.ui.btn_new_place.setText(self.conn.lang("add_event_btn_new_place", self.active_lang))
        self.ui.lbl_partner.setText(self.conn.lang("add_event_lbl_partner", self.active_lang))
        self.ui.lbl_description.setText(self.conn.lang("add_event_lbl_description", self.active_lang))
        self.ui.lbl_date.setText(self.conn.lang("add_event_lbl_date", self.active_lang))
        self.ui.btn_date_pick.setText(self.conn.lang("add_event_btn_date_pick", self.active_lang))
        self.ui.lbl_exchange.setText(self.conn.lang("add_event_lbl_exchange", self.active_lang))
        self.ui.btn_cancel.setText(self.conn.lang("btn_cancel", self.active_lang))
        self.ui.btn_save.setText(self.conn.lang("add_event_btn_save", self.active_lang))
        self.ui.grp_device.setTitle(self.conn.lang("add_event_grp_device", self.active_lang))







