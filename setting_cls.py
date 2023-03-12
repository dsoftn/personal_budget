from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
import log_cls
import connection
import user_info_ui
import user_info_pass_ui


class UserInfo(QtWidgets.QDialog):
    def __init__(self, user_id, user_name, language, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set enviroment variables
        self.active_user_id = user_id
        self.active_user_name = user_name
        self.active_lang = language
        self.user_list = []
        # Setup database connection
        self.conn = connection.ConnStart()
        # self.user = connection.User(self.active_user_id)
        self.log = log_cls.LogData()

    def setup_gui(self):
        # Setup Gui
        self.setFixedSize(725, 405)
        self.setWindowFlag(QtCore.Qt.Dialog)
        self.ui = user_info_ui.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowModality(Qt.ApplicationModal)
        self.retranslateUi(self.active_lang)
        # Populate widgets
        self.populate_widgets()
        # Connect events with slots
        self.ui.cmb_lang.currentTextChanged.connect(self.cmb_lang_changed)
        self.ui.btn_cancel.clicked.connect(self.btn_cancel_click)
        self.ui.txt_forename.textChanged.connect(self.text_changed_event)
        self.ui.txt_surname.textChanged.connect(self.text_changed_event)
        self.ui.txt_address.textChanged.connect(self.text_changed_event)
        self.ui.txt_mail.textChanged.connect(self.text_changed_event)
        self.ui.txt_phone.textChanged.connect(self.text_changed_event)
        self.ui.txt_description.textChanged.connect(self.text_changed_event)
        self.ui.btn_confirm.clicked.connect(self.btn_confirm_click)
        self.ui.btn_change_password.clicked.connect(self.btn_change_password_click)

        self.show()
        self.exec_()


    def btn_change_password_click(self):
        rst = PasswordChange(self.active_user_id, self.active_user_name, self.user_list[0][2], self.active_lang)
        result = rst.setup_gui()
        self.user_list = self.conn.get_users_all(self.active_user_id)
    
    def btn_confirm_click(self):
        # Create user dictionary
        user = {}
        user["user_id"] = self.active_user_id
        user["username"] = self.active_user_name
        user["password"] = self.user_list[0][2]
        user["baza_id"] = self.user_list[0][3]
        user["ime"] = self.ui.txt_forename.text()
        user["prezime"] = self.ui.txt_surname.text()
        user["adresa"] = self.ui.txt_address.toPlainText()
        user["email"] = self.ui.txt_mail.text()
        user["telefon"] = self.ui.txt_phone.text()
        user["opis"] = self.ui.txt_description.toPlainText()
        user["jezik_id"] = self.ui.cmb_lang.currentData()
        user["datum"] = self.user_list[0][11]
        # Check is data valid
        msg_text = ""
        if len(user["ime"]) > 255:
            msg_text = self.conn.lang("setting_user_update_ime_too_long", self.active_lang)
        elif len(user["prezime"]) > 255:
            msg_text = self.conn.lang("setting_user_update_prezime_too_long", self.active_lang)
        elif len(user["adresa"]) > 255:
            msg_text = self.conn.lang("setting_user_update_adresa_too_long", self.active_lang)
        elif len(user["email"]) > 255:
            msg_text = self.conn.lang("setting_user_update_email_too_long", self.active_lang)
        elif len(user["telefon"]) > 255:
            msg_text = self.conn.lang("setting_user_update_telefon_too_long", self.active_lang)
        elif len(user["opis"]) > 255:
            msg_text = self.conn.lang("setting_user_update_opis_too_long", self.active_lang)
        if msg_text != "":
            msg_title = self.conn.lang("setting_user_update_too_long_msg_title", self.active_lang)
            result = QtWidgets.QMessageBox.information(self, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
            return
        # Update user
        self.conn.set_user(self.active_user_id, user)
        if self.active_lang != self.ui.cmb_lang.currentData():
            msg_title = self.conn.lang("setting_user_info_win_title", self.active_lang)
            msg_text = self.conn.lang("setting_user_info_msg_lang_changed", self.active_lang)
            result = QtWidgets.QMessageBox.information(self, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
        # Create trosak_datum_extra_table
        if self.ui.cmb_lang.currentData() != self.user_list[0][10]:
            tmp_user = connection.User(self.active_user_id)
            tmp_user._create_trosak_datum_extra_table()

        self.close()

    def text_changed_event(self):
        self.ui.btn_confirm.setEnabled(True)

    def btn_cancel_click(self):
        self.close()

    def cmb_lang_changed(self):
        self.ui.btn_confirm.setEnabled(True)
        self.retranslateUi(self.ui.cmb_lang.currentData())

    def populate_widgets(self):
        self.ui.btn_confirm.setEnabled(False)
        # Get data for active user_id
        self.user_list = self.conn.get_users_all(user_id=self.active_user_id)
        # Populate txt boxes
        self.ui.txt_forename.setText(self.user_list[0][4])
        self.ui.txt_surname.setText(self.user_list[0][5])
        self.ui.txt_address.setText(self.user_list[0][6])
        self.ui.txt_mail.setText(self.user_list[0][7])
        self.ui.txt_phone.setText(self.user_list[0][8])
        self.ui.txt_description.setText(self.user_list[0][9])
        # Populate combo box for languages
        langs = self.conn.get_language_all()
        self.ui.cmb_lang.clear()
        for i in langs:
            self.ui.cmb_lang.addItem(i[1], i[0])
            if i[0] == self.user_list[0][10]:
                cur_lang = i[1]
        self.ui.cmb_lang.setCurrentText(cur_lang)





    def retranslateUi(self, lang):
        self.setWindowTitle(self.conn.lang("setting_user_info_win_title", lang))
        self.ui.lbl_caption.setText(self.conn.lang("setting_user_info_caption", lang) + self.active_user_name)
        self.ui.lbl_forename.setText(self.conn.lang("setting_user_info_forename", lang))
        self.ui.lbl_surname.setText(self.conn.lang("setting_user_info_surname", lang))
        self.ui.lbl_address.setText(self.conn.lang("setting_user_info_address", lang))
        self.ui.lbl_mail.setText(self.conn.lang("setting_user_info_mail", lang))
        self.ui.lbl_phone.setText(self.conn.lang("setting_user_info_phone", lang))
        self.ui.lbl_description.setText(self.conn.lang("setting_user_info_description", lang))
        self.ui.btn_change_password.setText(self.conn.lang("setting_user_info_btn_change_password", lang))
        self.ui.btn_change_database.setText(self.conn.lang("setting_user_info_btn_change_database", lang))
        self.ui.lbl_lang.setText(self.conn.lang("setting_user_info_lbl_lang", lang))
        self.ui.btn_confirm.setText(self.conn.lang("btn_confirm", lang))
        self.ui.btn_cancel.setText(self.conn.lang("btn_cancel", lang))


class PasswordChange(QtWidgets.QDialog):
    def __init__(self, user_id, user_name, old_password, language, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set enviroment variables
        self.active_user_id = user_id
        self.active_user_name = user_name
        self.active_lang = language
        # Setup database connection
        self.conn = connection.ConnStart()
        self.log = log_cls.LogData()
        self.old_pass = self.conn._decrypt_user_password(old_password)
        self.page = 1  # Current page 1, 2, 3
        self.password_echo = QtWidgets.QLineEdit.EchoMode.Password
        self.normal_echo = QtWidgets.QLineEdit.EchoMode.Normal

    def setup_gui(self):
        # Setup Gui
        self.setFixedSize(480, 180)
        self.setWindowFlag(QtCore.Qt.Dialog)
        self.ui = user_info_pass_ui.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowModality(Qt.ApplicationModal)
        self.retranslateUi()
        # Setup widgets
        self.update_widgets()
        # Connect events with slots
        self.ui.btn_next.clicked.connect(self.btn_next_click)
        self.ui.btn_back.clicked.connect(self.btn_back_click)
        self.ui.btn_confirm.clicked.connect(self.btn_confirm_click)
        self.ui.btn_cancel.clicked.connect(self.btn_cancel_click)
        self.ui.btn_show_password.clicked.connect(self.btn_show_pass1_click)
        self.ui.btn_show_password_2.clicked.connect(self.btn_show_pass2_click)
        self.ui.btn_show_password_3.clicked.connect(self.btn_show_pass3_click)
        self.show()
        self.exec_()
        return self.old_pass

    def btn_cancel_click(self):
        self.close()
    
    def btn_show_pass2_click(self):
        if self.ui.txt_new_password.echoMode() == self.password_echo:
            self.ui.txt_new_password.setEchoMode(self.normal_echo)
        else:
            self.ui.txt_new_password.setEchoMode(self.password_echo)

    def btn_show_pass3_click(self):
        if self.ui.txt_confirm_password.echoMode() == self.password_echo:
            self.ui.txt_confirm_password.setEchoMode(self.normal_echo)
        else:
            self.ui.txt_confirm_password.setEchoMode(self.password_echo)

    def btn_show_pass1_click(self):
        if self.ui.txt_password.echoMode() == self.password_echo:
            self.ui.txt_password.setEchoMode(self.normal_echo)
        else:
            self.ui.txt_password.setEchoMode(self.password_echo)

    def btn_next_click(self):
        if self.page == 1:
            if self.ui.txt_password.text() == self.old_pass:
                self.page = 2
            else:
                self.ui.txt_password.setText("")
                self.ui.txt_password.setPlaceholderText(self.conn.lang("msg_login_wrong_password_title", self.active_lang))
        elif self.page == 2:
            if self.ui.txt_new_password.text() == self.ui.txt_confirm_password.text():
                self.page = 3
            else:
                self.ui.txt_confirm_password.setText("")
                self.ui.txt_confirm_password.setPlaceholderText(self.conn.lang("msg_login_wrong_password_title", self.active_lang))
        self.update_widgets()

    def btn_back_click(self):
        if self.page == 2:
            self.page = 1
        elif self.page == 3:
            self.page = 2
        self.update_widgets()

    def btn_confirm_click(self):
        self.conn.set_user_password(self.active_user_id, self.ui.txt_confirm_password.text())
        msg_title = self.conn.lang("password_changed_information_msg_title", self.active_lang)
        msg_text = self.conn.lang("password_changed_information_msg_text", self.active_lang)
        result = QtWidgets.QMessageBox.information(self, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
        self.old_pass = self.conn._encrypt_user_password(self.ui.txt_confirm_password.text())
        self.close()

    def update_widgets(self):
        if self.page == 1:
            self.ui.frm_confirm.setVisible(False)
            self.ui.frm_finish.setVisible(False)
            self.ui.btn_back.setVisible(False)
            self.ui.btn_confirm.setVisible(False)
            self.ui.btn_next.setVisible(True)
        elif self.page == 2:
            self.ui.frm_confirm.setVisible(True)
            self.ui.frm_finish.setVisible(False)
            self.ui.btn_back.setVisible(True)
            self.ui.btn_confirm.setVisible(False)
            self.ui.btn_next.setVisible(True)
        elif self.page == 3:
            self.ui.frm_confirm.setVisible(False)
            self.ui.frm_finish.setVisible(True)
            self.ui.btn_back.setVisible(True)
            self.ui.btn_confirm.setVisible(True)
            self.ui.btn_next.setVisible(False)

    def retranslateUi(self):
        self.setWindowTitle(self.conn.lang("pass_change_win_title", self.active_lang))
        self.ui.lbl_old_password.setText(self.conn.lang("pass_change_lbl_old_password", self.active_lang))
        self.ui.lbl_new_password.setText(self.conn.lang("pass_change_lbl_new_password", self.active_lang))
        self.ui.lbl_confirm_password.setText(self.conn.lang("pass_change_lbl_confirm_password", self.active_lang))
        self.ui.lbl_password_info1.setText(self.conn.lang("pass_change_lbl_password_info1", self.active_lang))
        self.ui.lbl_password_info2.setText(self.conn.lang("pass_change_lbl_password_info2", self.active_lang))
        self.ui.btn_back.setText(self.conn.lang("btn_back", self.active_lang))
        self.ui.btn_next.setText(self.conn.lang("btn_next", self.active_lang))
        self.ui.btn_cancel.setText(self.conn.lang("btn_cancel", self.active_lang))
        self.ui.btn_confirm.setText(self.conn.lang("btn_confirm", self.active_lang))

