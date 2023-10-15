from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QThread, pyqtSignal

import connection
import log_cls
import web_ui  # GUI for view web records
import web_add_ui  # GUI for add web record


class Web(QtWidgets.QDialog):
    def __init__(self, language, user_id, user_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setup enviroment variables
        self.active_lang = language
        self.active_user_id = user_id
        self.active_user_name = user_name
        self.ui = web_ui.Ui_Dialog()
        self.conn = connection.ConnStart()
        self.web_conn = connection.WebPages(self.active_user_id)
        self.log = log_cls.LogData()
        self.active_list = []  # List of web pages
        self.log.write_log("View web pages dialog started...")

    def setup_ui(self):
        # Setup GUI
        self.ui.setupUi(self)
        self.setWindowFlag(QtCore.Qt.Dialog)
        self.setWindowModality(Qt.ApplicationModal)
        self.retranslateUi()
        # Load window size and position, and setup widgets
        self.load_win_size()
        # Connect events with slots
        self.closeEvent = self.save_win_size
        self.ui.btn_add_new.clicked.connect(self.btn_add_new_click)
        self.ui.btn_filter_apply.clicked.connect(self.btn_filter_apply_click)
        self.ui.btn_show_all.clicked.connect(self.btn_show_all_click)
        self.ui.txt_filter.textChanged.connect(self.txt_filter_text_changed)
        self.ui.tbl_data.cellClicked.connect(self.tbl_data_current_cell_changed)
        self.ui.tbl_data.selectionChanged = self.tbl_data_current_cell_changed
        self.ui.chk_show_password.stateChanged.connect(self.chk_show_password_changed)
        self.ui.txt_filter.returnPressed.connect(self.btn_filter_apply_click)
        self.ui.btn_view.clicked.connect(self.btn_view_click)
        self.ui.btn_edit.clicked.connect(self.btn_edit_click)
        self.ui.btn_delete.clicked.connect(self.btn_delete_click)
        # Populate table
        self.populate_data()
        self.no_data_disable_buttons()


        self.show()
        self.exec_()

    
    def btn_delete_click(self):
        itm = int(self.ui.tbl_data.item(self.ui.tbl_data.currentRow(), 0).text())
        itm_name = self.ui.tbl_data.item(self.ui.tbl_data.currentRow(), 1).text()
        msg_title = self.conn.lang("web_delete_msg_q_title", self.active_lang)
        msg_text = self.conn.lang("web_delete_msg_q_text", self.active_lang) + "\n" + itm_name
        result = QtWidgets.QMessageBox.information(None, msg_title, msg_text, QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if result == QtWidgets.QMessageBox.No:
            return
        result = self.web_conn.delete_web_page(itm)
        if result:
            self.log.write_log("1 item from 'web' table successfully deleted.")
        else:
            self.log.write_log("Warrning. Unable to delete item from 'web' table.")
        msg_title = self.conn.lang("web_delete_msg_i_title", self.active_lang)
        msg_text = self.conn.lang("web_delete_msg_i_text", self.active_lang) + "\n" + itm_name
        result = QtWidgets.QMessageBox.information(None, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
        self.populate_data()        

    def btn_edit_click(self):
        itm = int(self.ui.tbl_data.item(self.ui.tbl_data.currentRow(), 0).text())
        new_web = WebAdd(self.active_user_id, self.active_user_name, self.active_lang, open_mode="edit", item_id=itm)
        new_web.setup_ui()
        self.populate_data()


    def btn_view_click(self):
        itm = int(self.ui.tbl_data.item(self.ui.tbl_data.currentRow(), 0).text())
        new_web = WebAdd(self.active_user_id, self.active_user_name, self.active_lang, open_mode="view", item_id=itm)
        new_web.setup_ui()
        self.populate_data()

    
    def chk_show_password_changed(self):
        self.update_item_details()

    def tbl_data_current_cell_changed(self, x, y):
        self.no_data_disable_buttons()
        self.update_item_details()

    def txt_filter_text_changed(self):
        if self.ui.txt_filter.text() == "":
            self.ui.btn_filter_apply.setDisabled(True)
        else:
            self.ui.btn_filter_apply.setEnabled(True)

    def btn_filter_apply_click(self):
        self.populate_data()
        self.ui.btn_show_all.setEnabled(True)
        self.ui.btn_filter_apply.setDisabled(True)
        self.no_data_disable_buttons()

    def btn_show_all_click(self):
        self.ui.txt_filter.setText("")
        self.populate_data()
        self.ui.btn_show_all.setDisabled(True)
        self.ui.btn_filter_apply.setEnabled(False)
        self.no_data_disable_buttons()

    def btn_add_new_click(self):
        new_web = WebAdd(self.active_user_id, self.active_user_name, self.active_lang)
        new_web.setup_ui()
        self.populate_data()

    def populate_data(self):
        # Get data
        self.active_list.clear()
        self.active_list = self.web_conn.get_web_pages(self.ui.txt_filter.text())
        # Define table
        self.ui.tbl_data.setRowCount(len(self.active_list))
        self.ui.tbl_data.setColumnCount(7)
        # Populate tbl_data
        for x in range(len(self.active_list)):
            for y in range(self.ui.tbl_data.columnCount()):
                self.ui.tbl_data.setItem(x, y, QtWidgets.QTableWidgetItem(str(self.active_list[x][y])))
        # Set headers
        h = ["Hidden",
            self.conn.lang("web_tbl_data_header0", self.active_lang),
            self.conn.lang("web_tbl_data_header1", self.active_lang),
            self.conn.lang("web_tbl_data_header2", self.active_lang),
            self.conn.lang("web_tbl_data_header3", self.active_lang),
            self.conn.lang("web_tbl_data_header4", self.active_lang),
            self.conn.lang("web_lbl_created", self.active_lang)]
        self.ui.tbl_data.setHorizontalHeaderLabels(h)
        # Hide column 0 and 6
        self.ui.tbl_data.setColumnHidden(0, True)
        self.ui.tbl_data.setColumnHidden(6, True)
        # Update record count label
        txt = self.conn.lang("web_lbl_records", self.active_lang) + str(len(self.active_list))
        self.ui.lbl_records.setText(txt)
        self.ui.tbl_data.setSortingEnabled(True)
        self.update_item_details()

    def update_item_details(self):
        row = self.ui.tbl_data.currentRow()
        if row < 0:
            return
        for i in self.active_list:
            aa = self.ui.tbl_data.item(row, 0).text()
            if i[0] == int(self.ui.tbl_data.item(row, 0).text()):
                self.ui.lbl_item_caption.setText(i[1])
                self.ui.lbl_item_web_page.setText(i[2])
                self.ui.lbl_item_description.setText(i[3])
                self.ui.lbl_username.setText(self.conn.lang("web_tbl_data_header3", self.active_lang) + ": " + i[4])
                self.ui.lbl_created_data.setText(i[6]) 
                if self.ui.chk_show_password.isChecked():
                    pssw = self.conn._decrypt_user_password(i[5])
                else:
                    pssw = " - - -"
                pssw = self.conn.lang("web_tbl_data_header4", self.active_lang) + ": " + pssw
                self.ui.lbl_password.setText(pssw)
                break

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        w = self.width()
        h = self.height()
        self.ui.frm_options.resize(w-250, self.ui.frm_options.height())
        self.ui.lbl_item_caption.resize(self.ui.frm_options.width(), self.ui.lbl_item_caption.height())
        self.ui.lbl_item_web_page.resize(self.ui.frm_options.width() - 20, self.ui.lbl_item_web_page.height())
        self.ui.lbl_item_description.resize(self.ui.frm_options.width() - 20, self.ui.lbl_item_description.height())
        self.ui.line.resize(self.ui.frm_options.width()-20, self.ui.line.height())
        self.ui.tbl_data.resize(w, h-230)

        return super().resizeEvent(a0)
    
    def load_win_size(self):
        # Setup window size and position
        self.setMinimumSize(1060, 430)
        x = self.conn.get_setting_data("web_win_x", getParametar=True, user_id=self.active_user_id)
        y = self.conn.get_setting_data("web_win_y", getParametar=True, user_id=self.active_user_id)
        w = self.conn.get_setting_data("web_win_w", getParametar=True, user_id=self.active_user_id)
        h = self.conn.get_setting_data("web_win_h", getParametar=True, user_id=self.active_user_id)
        # Set buttons disabled/enabled
        self.ui.btn_show_all.setDisabled(True)
        self.ui.btn_filter_apply.setDisabled(True)

    def no_data_disable_buttons(self):
        if len(self.ui.tbl_data.selectedItems()) > 0:
            self.ui.btn_view.setDisabled(False)
            self.ui.btn_edit.setDisabled(False)
            self.ui.btn_delete.setDisabled(False)
        else:
            self.ui.btn_view.setDisabled(True)
            self.ui.btn_edit.setDisabled(True)
            self.ui.btn_delete.setDisabled(True)
        if len(self.active_list) == 0:
            self.ui.btn_filter_apply.setDisabled(True)

    def save_win_size(self, event):
        x = self.pos().x()
        y = self.pos().y()
        w = self.width()
        h = self.height()
        self.conn.set_setting_data("web_win_x", "Web, Window geometry", x, self.active_user_id)
        self.conn.set_setting_data("web_win_y", "Web, Window geometry", y, self.active_user_id)
        self.conn.set_setting_data("web_win_w", "Web, Window geometry", w, self.active_user_id)
        self.conn.set_setting_data("web_win_h", "Web, Window geometry", h, self.active_user_id)
        self.log.write_log("View web pages dialog finished.")

    def retranslateUi(self):
        self.setWindowTitle(self.conn.lang("web_win_title", self.active_lang))
        self.ui.lbl_info_user_caption.setText(self.conn.lang("web_info_user_caption", self.active_lang))
        self.ui.lbl_info_user_name.setText(self.active_user_name)
        self.ui.lbl_info_description.setText(self.conn.lang("web_info_description", self.active_lang))
        self.ui.chk_show_password.setText(self.conn.lang("web_info_chk_show_password", self.active_lang))
        self.ui.btn_show_all.setText(self.conn.lang("main_btn_show_all", self.active_lang))
        self.ui.btn_view.setText(self.conn.lang("web_btn_view", self.active_lang))
        self.ui.btn_edit.setText(self.conn.lang("web_btn_edit", self.active_lang))
        self.ui.btn_delete.setText(self.conn.lang("web_btn_delete", self.active_lang))
        self.ui.btn_add_new.setText(self.conn.lang("web_btn_add_new", self.active_lang))
        self.ui.lbl_records.setText(self.conn.lang("web_lbl_records", self.active_lang))
        self.ui.btn_filter_apply.setText(self.conn.lang("web_btn_filter_apply", self.active_lang))
        self.ui.lbl_created.setText(self.conn.lang("web_lbl_created", self.active_lang))


class WebAdd(QtWidgets.QDialog):
    def __init__(self, user_id, user_name, language, open_mode="", item_id="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setup enviroment variables
        self.open_mode = open_mode
        self.active_item_id = item_id
        self.active_user_id =user_id
        self.active_user_name = user_name
        self.active_lang = language
        self.web_conn = connection.WebPages(self.active_user_id)
        self.conn = connection.ConnStart()
        self.log = log_cls.LogData()
        self.ui = web_add_ui.Ui_Dialog()
        self.log.write_log("Add web dialog started...")

    def setup_ui(self):
        # Set minimum window size
        self.setMinimumSize(550, 380)
        self.setWindowFlag(QtCore.Qt.Dialog)
        self.setWindowModality(Qt.ApplicationModal)
        # Setup GUI
        self.ui.setupUi(self)
        self.retranslateUi()
        # Load win size and position
        self.load_win_size()
        # Setup widgets for current open_mode
        self.open_mode_setup()
        # Connect events with slots
        self.closeEvent = self.save_win_size
        self.ui.btn_show_password.clicked.connect(self.btn_show_password_click)
        self.ui.btnbox.clicked.connect(self.btnbox_click)
        

        self.show()
        self.exec_()


    def open_mode_setup(self):
        if self.open_mode == "view":
            self.ui.lbl_title.setText(self.active_user_name + ", " + self.conn.lang("web_view_lbl_title", self.active_lang))
            self.ui.btnbox.clear()
            self.ui.btnbox.addButton(QtWidgets.QDialogButtonBox.Ok)
            itm = self.web_conn.get_web_page(self.active_item_id)
            self.ui.txt_caption.setText(itm[0][1])
            self.ui.txt_web_page.setText(itm[0][2])
            self.ui.txt_description.setText(itm[0][3])
            self.ui.txt_username.setText(itm[0][4])
            self.ui.txt_password.setText(self.web_conn.decript_password(itm[0][5]))
        elif self.open_mode == "edit":
            self.ui.lbl_title.setText(self.active_user_name + ", " + self.conn.lang("web_edit_lbl_title", self.active_lang))
            self.ui.btnbox.clear()
            self.ui.btnbox.addButton(QtWidgets.QDialogButtonBox.Apply)
            self.ui.btnbox.addButton(QtWidgets.QDialogButtonBox.Cancel)
            itm = self.web_conn.get_web_page(self.active_item_id)
            self.ui.txt_caption.setText(itm[0][1])
            self.ui.txt_web_page.setText(itm[0][2])
            self.ui.txt_description.setText(itm[0][3])
            self.ui.txt_username.setText(itm[0][4])
            self.ui.txt_password.setText(self.web_conn.decript_password(itm[0][5]))


    def btnbox_click(self, btn):
        # Check button type
        if btn == self.ui.btnbox.button(QtWidgets.QDialogButtonBox.Save):
            # Is data valid
            if len(self.ui.txt_password.text()) > 30:
                msg_title = self.conn.lang("add_web_msg_password_too_long_title", self.active_lang)
                msg_text = self.conn.lang("add_web_msg_password_too_long_text", self.active_lang)
                result = QtWidgets.QMessageBox.critical(None, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
                return
            elif len(self.ui.txt_caption.text()) > 255:
                msg_title = self.conn.lang("add_web_msg_caption_too_long_title", self.active_lang)
                msg_text = self.conn.lang("add_web_msg_caption_too_long_text", self.active_lang)
                result = QtWidgets.QMessageBox.critical(None, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
                return
            elif len(self.ui.txt_web_page.text()) > 255:
                msg_title = self.conn.lang("add_web_msg_web_page_too_long_title", self.active_lang)
                msg_text = self.conn.lang("add_web_msg_web_page_too_long_text", self.active_lang)
                result = QtWidgets.QMessageBox.critical(None, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
                return
            elif len(self.ui.txt_username.text()) > 255:
                msg_title = self.conn.lang("add_web_msg_username_too_long_title", self.active_lang)
                msg_text = self.conn.lang("add_web_msg_username_too_long_text", self.active_lang)
                result = QtWidgets.QMessageBox.critical(None, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
                return
            
            web_obj = {}
            web_obj["naslov"] = self.ui.txt_caption.text()
            web_obj["stranica"] = self.ui.txt_web_page.text()
            web_obj["opis"] = self.ui.txt_description.toPlainText()
            web_obj["username"] = self.ui.txt_username.text()
            web_obj["password"] = self.ui.txt_password.text()
            if web_obj["naslov"] == "" and web_obj["stranica"] == "" and web_obj["opis"] == "" and web_obj["username"] == "" and web_obj["password"] == "":
                msg_title = self.conn.lang("add_web_msg_no_data_title", self.active_lang)
                msg_text = self.conn.lang("add_web_msg_no_data_text", self.active_lang)
                result = QtWidgets.QMessageBox.information(None, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
                return
            self.web_conn.add_web_page(web_obj)
            self.close()


        elif btn == self.ui.btnbox.button(QtWidgets.QDialogButtonBox.Cancel):
            self.close()
        elif btn == self.ui.btnbox.button(QtWidgets.QDialogButtonBox.Ok):
            self.close()
        elif btn == self.ui.btnbox.button(QtWidgets.QDialogButtonBox.Apply):
            # Is data valid
            if len(self.ui.txt_password.text()) > 30:
                msg_title = self.conn.lang("add_web_msg_password_too_long_title", self.active_lang)
                msg_text = self.conn.lang("add_web_msg_password_too_long_text", self.active_lang)
                result = QtWidgets.QMessageBox.critical(None, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
                return
            elif len(self.ui.txt_caption.text()) > 255:
                msg_title = self.conn.lang("add_web_msg_caption_too_long_title", self.active_lang)
                msg_text = self.conn.lang("add_web_msg_caption_too_long_text", self.active_lang)
                result = QtWidgets.QMessageBox.critical(None, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
                return
            elif len(self.ui.txt_web_page.text()) > 255:
                msg_title = self.conn.lang("add_web_msg_web_page_too_long_title", self.active_lang)
                msg_text = self.conn.lang("add_web_msg_web_page_too_long_text", self.active_lang)
                result = QtWidgets.QMessageBox.critical(None, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
                return
            elif len(self.ui.txt_username.text()) > 255:
                msg_title = self.conn.lang("add_web_msg_username_too_long_title", self.active_lang)
                msg_text = self.conn.lang("add_web_msg_username_too_long_text", self.active_lang)
                result = QtWidgets.QMessageBox.critical(None, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
                return
            web_obj = {}
            web_obj["web_id"] = self.active_item_id
            web_obj["naslov"] = self.ui.txt_caption.text()
            web_obj["stranica"] = self.ui.txt_web_page.text()
            web_obj["opis"] = self.ui.txt_description.toPlainText()
            web_obj["username"] = self.ui.txt_username.text()
            web_obj["password"] = self.ui.txt_password.text()
            if web_obj["naslov"] == "" and web_obj["stranica"] == "" and web_obj["opis"] == "" and web_obj["username"] == "" and web_obj["password"] == "":
                msg_title = self.conn.lang("add_web_msg_no_data_title", self.active_lang)
                msg_text = self.conn.lang("add_web_msg_no_data_text", self.active_lang)
                result = QtWidgets.QMessageBox.information(None, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
                return
            self.web_conn.set_web_page(web_obj)
            self.close()


    def btn_show_password_click(self):
        password_echo = self.ui.txt_password.EchoMode.Password
        normal_echo = self.ui.txt_password.EchoMode.Normal
        if self.ui.txt_password.echoMode() == password_echo:
            self.ui.txt_password.setEchoMode(normal_echo)
        else:
            self.ui.txt_password.setEchoMode(password_echo)
    
    def load_win_size(self):
        x = self.conn.get_setting_data("web_add_win_x", getParametar=True, user_id=self.active_user_id)
        y = self.conn.get_setting_data("web_add_win_y", getParametar=True, user_id=self.active_user_id)
        w = self.conn.get_setting_data("web_add_win_w", getParametar=True, user_id=self.active_user_id)
        h = self.conn.get_setting_data("web_add_win_h", getParametar=True, user_id=self.active_user_id)
        self.move(x, y)
        self.resize(w, h)

    def save_win_size(self, event):
        x = self.pos().x()
        y = self.pos().y()
        w = self.width()
        h = self.height()
        self.conn.set_setting_data("web_add_win_x", "Add Web, Window geometry", x, self.active_user_id)
        self.conn.set_setting_data("web_add_win_y", "Add Web, Window geometry", y, self.active_user_id)
        self.conn.set_setting_data("web_add_win_w", "Add Web, Window geometry", w, self.active_user_id)
        self.conn.set_setting_data("web_add_win_h", "Add Web, Window geometry", h, self.active_user_id)
        self.log.write_log("Add web dialog finished.")

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        # Create variables
        scale = self.height() / 380
        w = self.width()
        h = self.height()
        # Change sizes to each widget
        # Caption and lines
        self.ui.lbl_title.resize(w, int(31*scale))
        self.ui.line.resize(w-60, self.ui.line.height())
        self.ui.line_2.resize(w-60, self.ui.line.height())
        self.ui.line_2.move(self.ui.line_2.pos().x(), int(330*scale))
        # Labels
        self.ui.lbl_caption.move(self.ui.lbl_caption.pos().x(), int(85*scale))
        self.ui.lbl_web_page.move(self.ui.lbl_web_page.pos().x(), int(125*scale))
        self.ui.lbl_description.move(self.ui.lbl_description.pos().x(), int(165*scale))
        self.ui.lbl_username.move(self.ui.lbl_username.pos().x(), int(260*scale))
        self.ui.lbl_password.move(self.ui.lbl_password.pos().x(), int(295*scale))
        # LineEdit boxes
        self.ui.txt_caption.move(self.ui.txt_caption.pos().x(), int(80*scale))
        self.ui.txt_caption.resize(w-220, self.ui.txt_caption.height())
        self.ui.txt_web_page.move(self.ui.txt_web_page.pos().x(), int(120*scale))
        self.ui.txt_web_page.resize(w-220, self.ui.txt_web_page.height())
        self.ui.txt_description.move(self.ui.txt_description.pos().x(), int(160*scale))
        self.ui.txt_description.resize(w-220, self.ui.txt_description.height())
        self.ui.txt_username.move(self.ui.txt_username.pos().x(), int(255*scale))
        self.ui.txt_username.resize(w-490, self.ui.txt_username.height())
        self.ui.txt_password.move(self.ui.txt_password.pos().x(), int(290*scale))
        self.ui.txt_password.resize(w-490, self.ui.txt_password.height())
        # Buttons
        self.ui.btn_show_password.move(w-280, int(290*scale))
        self.ui.btnbox.move(w-170, h-30)

        return super().resizeEvent(a0)

    def retranslateUi(self):
        self.setWindowTitle(self.conn.lang("web_add_win_title", self.active_lang))
        txt = self.active_user_name + ", " + self.conn.lang("web_add_lbl_title", self.active_lang)
        self.ui.lbl_title.setText(txt)
        self.ui.lbl_caption.setText(self.conn.lang("web_add_lbl_caption", self.active_lang))
        self.ui.lbl_web_page.setText(self.conn.lang("web_add_lbl_web_page", self.active_lang))
        self.ui.lbl_description.setText(self.conn.lang("web_add_lbl_description", self.active_lang))
        self.ui.lbl_username.setText(self.conn.lang("web_add_lbl_username", self.active_lang))
        self.ui.lbl_password.setText(self.conn.lang("web_add_lbl_password", self.active_lang))

