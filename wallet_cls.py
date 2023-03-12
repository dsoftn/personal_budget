from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

import connection
import log_cls
import wallet_ui
import wallet_add_ui
import wallet_transfer_ui



class Wallet(QtWidgets.QDialog):
    def __init__(self, user_id, user_name, language, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create variables
        self.active_user_id = user_id
        self.active_user_name = user_name
        self.active_lang = language
        self.btn_total_state = 0  # Button state 0=RSD, 1=EUR, will be loaded on start
        self.drag_mode = False  # Drag mode for line
        self.wallets_list = []  # List of all wallets
        self.events_list = []  # List of events for selected wallet
        self.balance = {}  # Balance for wallet(i_rsd, o_rsd, t_rsd, i_eur, o_eur, t_eur)
        # Create connection with databases
        self.conn = connection.ConnStart()
        self.user = connection.User(self.active_user_id)
        self.log = log_cls.LogData()
        self.wallet_base = connection.Wallets(self.active_user_id)

    def setup_gui(self):
        # Setup widgets
        self.ui = wallet_ui.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowFlag(QtCore.Qt.Dialog)
        self.setWindowModality(Qt.ApplicationModal)
        self.load_settings()
        # Setup widgets language
        self.retranslateUi()
        # Connect events with slots
        self.closeEvent = self.save_settings
        self.ui.btn_add_new.clicked.connect(self.btn_add_new_click)
        self.ui.btn_total.clicked.connect(self.btn_total_click)
        self.ui.tbl_walets.selectionChanged = self.tbl_wallets_selection_changed
        self.ui.btn_transfer.clicked.connect(self.mnu_tbl_wallets_transfer_trigger)
        # Define context menus
        self.tbl_wallets_context_mnu()

        # Populate data
        self.populate_wallets()

        self.show()
        self.exec_()
        

    def tbl_wallets_context_mnu(self):
        # Create Menu
        self.mnu_tbl_wallets = QtWidgets.QMenu(self.ui.tbl_walets)
        # Create Items
        self.mnu_tbl_wallets_view = QtWidgets.QAction(self.conn.lang("mnu_context_view", self.active_lang), self.ui.tbl_walets)
        self.mnu_tbl_wallets_edit = QtWidgets.QAction(self.conn.lang("mnu_context_edit", self.active_lang), self.ui.tbl_walets)
        self.mnu_tbl_wallets_delete = QtWidgets.QAction(self.conn.lang("mnu_context_delete", self.active_lang), self.ui.tbl_walets)
        self.mnu_tbl_wallets_transfer = QtWidgets.QAction(self.conn.lang("wallet_btn_transfer", self.active_lang), self.ui.tbl_walets)
        # Add items to menu
        self.mnu_tbl_wallets.addAction(self.mnu_tbl_wallets_view)
        self.mnu_tbl_wallets.addAction(self.mnu_tbl_wallets_edit)
        self.mnu_tbl_wallets.addAction(self.mnu_tbl_wallets_delete)
        self.mnu_tbl_wallets.addAction(self.mnu_tbl_wallets_transfer)
        # Connect mnu actions with slots
        self.mnu_tbl_wallets_view.triggered.connect(self.mnu_tbl_wallets_view_trigger)
        self.mnu_tbl_wallets_edit.triggered.connect(self.mnu_tbl_wallets_edit_trigger)
        self.mnu_tbl_wallets_delete.triggered.connect(self.mnu_tbl_wallets_delete_trigger)
        self.mnu_tbl_wallets_transfer.triggered.connect(self.mnu_tbl_wallets_transfer_trigger)
        # Connect tbl_wallets request menu with slot
        self.ui.tbl_walets.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.tbl_walets.customContextMenuRequested.connect(self.mnu_tbl_wallet_show)
        self.ui.tbl_events.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        
    def mnu_tbl_wallets_delete_trigger(self):
        # Check is there some events joined with that wallet
        wal_id = self.wallets_list[self.ui.tbl_walets.currentRow()][0]
        is_safe = self.wallet_base.is_safe_to_delete_wallet(wal_id)
        if not is_safe:
            msg_title = self.conn.lang("mnu_context_delete", self.active_lang)
            msg_text = self.conn.lang("mnu_context_delete_wallet_msg_text_not safe", self.active_lang) + "\n" + self.ui.tbl_walets.item(self.ui.tbl_walets.currentRow(), 1).text()
            result = QtWidgets.QMessageBox.information(None, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
            return
        # Confirm deleting
        msg_title = self.conn.lang("mnu_context_delete", self.active_lang)
        msg_text = self.conn.lang("mnu_context_delete_wallet_msg_text", self.active_lang) + "\n" + self.ui.tbl_walets.item(self.ui.tbl_walets.currentRow(), 1).text()
        result = QtWidgets.QMessageBox.question(None, msg_title, msg_text, QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if result == QtWidgets.QMessageBox.No:
            return
        # Delete wallet
        self.wallet_base.delete_wallet(wal_id)
        self.populate_wallets()

    def mnu_tbl_wallets_view_trigger(self):
        view_wall = WalletAdd(self.active_user_id, self.active_user_name, self.active_lang)
        view_wall.setup_gui(open_mode="view", wallet_id=self.wallets_list[self.ui.tbl_walets.currentRow()][0])

    def mnu_tbl_wallets_edit_trigger(self):
        view_wall = WalletAdd(self.active_user_id, self.active_user_name, self.active_lang)
        view_wall.setup_gui(open_mode="edit", wallet_id=self.wallets_list[self.ui.tbl_walets.currentRow()][0])
        self.populate_wallets(self.ui.tbl_walets.currentRow())

    def mnu_tbl_wallets_transfer_trigger(self):
        if self.ui.tbl_walets.currentRow() < 0:
            return
        wal_id = self.wallets_list[self.ui.tbl_walets.currentRow()][0]
        trans = WalletTransfer(self.active_user_id, self.active_user_name, self.active_lang, wal_id)
        trans.setup_gui()
        self.update_details()

    def mnu_tbl_wallet_show(self, position):
        self.mnu_tbl_wallets.exec_(self.ui.tbl_walets.mapToGlobal(position))

    def tbl_wallets_selection_changed(self, x, y):
        self.update_details()

    def populate_wallets(self, row_position=-1):
        tbl = self.ui.tbl_walets
        # Clear data
        tbl.clear()
        # Get wallets list
        self.wallets_list = self.wallet_base.get_wallet_all()
        # Select current row
        cur_row = row_position
        if row_position == -1 and len(self.wallets_list) > 0:
            cur_row = 0
        # Define table size
        tbl.setRowCount(len(self.wallets_list))
        tbl.setColumnCount(3)
        # Set headers labels
        h = ["Hidden",
            self.conn.lang("wallet_view_wallet_table_header1", self.active_lang),
            self.conn.lang("wallet_view_wallet_table_header2", self.active_lang)]
        tbl.setHorizontalHeaderLabels(h)
        # Fill table with data
        for x in range(len(self.wallets_list)):
            tbl.setItem(x, 0, QtWidgets.QTableWidgetItem(str(self.wallets_list[x][0])))
            tbl.setItem(x, 1, QtWidgets.QTableWidgetItem(self.wallets_list[x][1]))
            tbl.setItem(x, 2, QtWidgets.QTableWidgetItem(self.wallets_list[x][2]))
        # Hide column with wallet_id and description
        tbl.setColumnHidden(0, True)
        tbl.setColumnHidden(2, True)
        # Set column width to table width
        tbl.setColumnWidth(1, tbl.width())
        # Set current row if possible
        if cur_row >= 0:
            if len(self.wallets_list) > 0:
                tbl.setCurrentCell(cur_row, 1)
        # Enable sorting
        tbl.setSortingEnabled(True)
        # Populate wallet details, and wallet events table
        self.update_details()

        

    def update_details(self):
        # Clear all data
        self.ui.tbl_events.clear()
        self.ui.lbl_info_wallet.setText("")
        self.ui.lbl_info_description.setText("")
        self.ui.lbl_wallet_name.setText("")
        self.ui.lbl_total_income_data.setText("-.--")
        self.ui.lbl_total_outcome_data.setText("-.--")
        # Is current row exists
        cur_r = self.ui.tbl_walets.currentRow()
        if cur_r < 0:
            return
        # Get events for selected wallet
        self.events_list = self.wallet_base.get_events(self.wallets_list[cur_r][0])
        # Setup table dimension and header labels
        self.ui.tbl_events.setRowCount(len(self.events_list))
        self.ui.tbl_events.setColumnCount(15)
        # Populate table
        i_rsd = 0
        o_rsd = 0
        i_eur = 0
        o_eur = 0
        for x in range(len(self.events_list)):
            i_rsd += self.events_list[x][1]
            o_rsd += self.events_list[x][2]
            i_eur += self.events_list[x][3]
            o_eur += self.events_list[x][4]
            for y in range(15):
                self.ui.tbl_events.setItem(x, y, QtWidgets.QTableWidgetItem(str(self.events_list[x][y])))
        # Set headers labels
        h = ["Hidden",
            self.conn.lang("main_tbl_header_prihod_rsd", self.active_lang),
            self.conn.lang("main_tbl_header_rashod_rsd", self.active_lang),
            self.conn.lang("main_tbl_header_prihod_eur", self.active_lang),
            self.conn.lang("main_tbl_header_rashod_eur", self.active_lang),
            self.conn.lang("main_tbl_header_datum", self.active_lang),
            "Hidden",
            "Hidden",
            "Hidden",
            self.conn.lang("main_tbl_header_opis", self.active_lang),
            "Hidden",
            "Hidden",
            "Hidden",
            "Hidden",
            "Hidden"]
        self.ui.tbl_events.setHorizontalHeaderLabels(h)
        self.ui.tbl_events.setSortingEnabled(True)
        # Populate labels with data
        self.balance["i_rsd"] = f"{i_rsd:,.2f}"
        self.balance["o_rsd"] = f"{o_rsd:,.2f}"
        self.balance["t_rsd"] = f"{(i_rsd-o_rsd):,.2f}"
        self.balance["i_eur"] = f"{i_eur:,.2f}"
        self.balance["o_eur"] = f"{o_eur:,.2f}"
        self.balance["t_eur"] = f"{(i_eur-o_eur):,.2f}"
        self.ui.lbl_wallet_name.setText(self.ui.tbl_walets.item(cur_r, 1).text())
        txt = self.conn.lang("event_edit_wallet", self.active_lang) + " " + self.ui.tbl_walets.item(cur_r, 1).text()
        txt = txt + "   " + self.conn.lang("wallet_btn_total_0", self.active_lang) + " " + self.balance["t_rsd"]
        txt = txt + "   " + self.conn.lang("wallet_btn_total_1", self.active_lang) + " " + self.balance["t_eur"]
        txt = txt + "   " + self.conn.lang("wallet_view_lbl_info_wallet", self.active_lang) + str(len(self.events_list))
        self.ui.lbl_info_wallet.setText(txt)
        self.ui.lbl_info_description.setText(self.wallets_list[cur_r][2])
        # Set not needed columns to hidden
        for i in range(15):
            self.ui.tbl_events.setColumnHidden(i, True)
        self.ui.tbl_events.setColumnHidden(5, False)
        self.ui.tbl_events.setColumnHidden(9, False)
        self.update_total()

    def update_total(self):
        if self.btn_total_state == 0:
            self.ui.btn_total.setText(self.conn.lang("wallet_btn_total_0", self.active_lang))
            self.ui.lbl_total_income_data.setText(self.balance["i_rsd"])
            self.ui.lbl_total_outcome_data.setText(self.balance["o_rsd"])
            self.ui.tbl_events.setColumnHidden(1, False)
            self.ui.tbl_events.setColumnHidden(2, False)
            self.ui.tbl_events.setColumnHidden(3, True)
            self.ui.tbl_events.setColumnHidden(4, True)
        else:
            self.ui.btn_total.setText(self.conn.lang("wallet_btn_total_1", self.active_lang))
            self.ui.lbl_total_income_data.setText(self.balance["i_eur"])
            self.ui.lbl_total_outcome_data.setText(self.balance["o_eur"])
            self.ui.tbl_events.setColumnHidden(1, True)
            self.ui.tbl_events.setColumnHidden(2, True)
            self.ui.tbl_events.setColumnHidden(3, False)
            self.ui.tbl_events.setColumnHidden(4, False)

    def btn_total_click(self):
        if self.btn_total_state == 0:
            self.btn_total_state = 1
            self.update_total()
        else:
            self.btn_total_state = 0
            self.update_total()
    
    def btn_add_new_click(self):
        add_new = WalletAdd(self.active_user_id, self.active_user_name, self.active_lang)
        add_new.setup_gui()
        self.populate_wallets(self.ui.tbl_walets.currentRow())

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        x = a0.localPos().x()
        drag_point = self.ui.lin_delimiter.pos().x()
        if a0.button() == QtCore.Qt.LeftButton and x == drag_point:
            self.drag_mode = True
        return super().mousePressEvent(a0)
    
    def mouseMoveEvent(self, a0: QtGui.QMouseEvent) -> None:
        x = a0.localPos().x()
        if self.drag_mode and x > 100 and x < (self.width()-300):
            self.resize_widgets(x)
        return super().mouseMoveEvent(a0)
    
    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        if a0.button() == QtCore.Qt.LeftButton:
            self.drag_mode = False
        return super().mouseReleaseEvent(a0)

    def load_settings(self):
        self.log.write_log("Wallet view started...")
        # Set dic balance to default values
        self.balance["i_rsd"] = "-.--"
        self.balance["o_rsd"] = "-.--"
        self.balance["t_rsd"] = "-.--"
        self.balance["i_eur"] = "-.--"
        self.balance["o_eur"] = "-.--"
        self.balance["t_eur"] = "-.--"
        # Set minimum win size
        self.setMinimumSize(1040, 450)
        # Load win position and size
        x = self.conn.get_setting_data("wallet_win_x", getParametar=True, user_id=self.active_user_id)
        y = self.conn.get_setting_data("wallet_win_y", getParametar=True, user_id=self.active_user_id)
        w = self.conn.get_setting_data("wallet_win_w", getParametar=True, user_id=self.active_user_id)
        h = self.conn.get_setting_data("wallet_win_h", getParametar=True, user_id=self.active_user_id)
        self.move(x,y)
        self.resize(w,h)
        # Load btn_total state
        self.btn_total_state = self.conn.get_setting_data("wallet_btn_total_state", getParametar=True, user_id=self.active_user_id)
        self.update_total()
        # Load delimiter line position
        delim = self.conn.get_setting_data("wallet_delimiter_pos_x", getParametar=True, user_id=self.active_user_id)
        self.ui.lin_delimiter.move(delim, 60)
        self.resize_widgets(0)

    def save_settings(self, x):
        self.log.write_log("Wallet view finished.")
        x = self.pos().x()
        y = self.pos().y()
        w = self.width()
        h = self.height()
        btn = self.ui.btn_total.text()
        # Save window position and size
        self.conn.set_setting_data("wallet_win_x", "Wallet Win Geometry", x, self.active_user_id)
        self.conn.set_setting_data("wallet_win_y", "Wallet Win Geometry", y, self.active_user_id)
        self.conn.set_setting_data("wallet_win_w", "Wallet Win Geometry", w, self.active_user_id)
        self.conn.set_setting_data("wallet_win_h", "Wallet Win Geometry", h, self.active_user_id)
        # Save btn_total state
        self.conn.set_setting_data("wallet_btn_total_state", btn, self.btn_total_state, self.active_user_id)
        # Save delimiter position
        self.conn.set_setting_data("wallet_delimiter_pos_x", "Delimiter", self.ui.lin_delimiter.pos().x(), self.active_user_id)

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        self.resize_widgets(0)
        return super().resizeEvent(a0)

    def resize_widgets(self, x):
        w = self.width()
        h = self.height()
        self.ui.lin_delimiter.resize(1, h-60)
        if self.drag_mode:
            self.ui.lin_delimiter.move(x, 60)
        dx = self.ui.lin_delimiter.pos().x()
        self.ui.lbl_caption.resize(w, self.ui.lbl_caption.height())
        self.ui.tbl_walets.resize(dx, h-60)
        self.ui.frm_options.resize(w-dx, self.ui.frm_options.height())
        self.ui.frm_options.move(dx, self.ui.frm_options.pos().y())
        self.ui.lbl_wallet_name.resize(w-dx, self.ui.lbl_wallet_name.height())
        self.ui.lbl_wallet_name.move(dx, self.ui.lbl_wallet_name.pos().y())
        self.ui.tbl_events.resize(w-dx, h-250)
        self.ui.tbl_events.move(dx, self.ui.tbl_events.pos().y())
        self.ui.frm_details_2.resize(w-dx, self.ui.frm_details_2.height())
        self.ui.frm_details_2.move(dx, h-40)


    def retranslateUi(self):
        self.setWindowTitle(self.conn.lang("wallet_win_title", self.active_lang))
        self.ui.lbl_caption.setText(self.conn.lang("wallet_lbl_caption", self.active_lang))
        self.ui.btn_add_new.setText(self.conn.lang("wallet_btn_add_new", self.active_lang))
        self.ui.lbl_total_income.setText(self.conn.lang("wallet_lbl_total_income", self.active_lang))
        self.ui.lbl_total_outcome.setText(self.conn.lang("wallet_lbl_total_outcome", self.active_lang))
        self.ui.btn_transfer.setText(self.conn.lang("wallet_btn_transfer", self.active_lang))


class WalletAdd(QtWidgets.QDialog):
    def __init__(self, user_id, user_name, language, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Define enviroment variables
        self.active_user_id = user_id
        self.active_user_name = user_name
        self.active_lang = language
        self.conn = connection.ConnStart()
        self.user = connection.User(self.active_user_id)
        self.log = log_cls.LogData()
        self.wallet_base = connection.Wallets(self.active_user_id)

    def setup_gui(self, open_mode="", wallet_id=0):
        self.open_mode = open_mode
        self.wallet_id = wallet_id
        # Load GUI
        self.ui = wallet_add_ui.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowFlag(QtCore.Qt.Dialog)
        self.setWindowModality(Qt.ApplicationModal)
        self.retranslateUi()
        # Load size and position
        self.load_settings()
        # Connect events with slots
        self.closeEvent = self.save_settings
        self.ui.btn_cancel.clicked.connect(self.btn_cancel_click)
        self.ui.btn_save.clicked.connect(self.btn_save_click)
        # Populate widgets if open mode is selected
        self.populate_data()
        self.show()
        self.exec_()

    def populate_data(self):
        # Return if no wallet_id is defined
        if self.wallet_id == 0:
            return
        # Populate txt with data
        result = self.wallet_base.get_wallet_all(wallet_id=self.wallet_id)
        self.ui.txt_name.setText(result[0][1])
        self.ui.txt_description.setText(result[0][2])
        # Setup caption and buttons
        if self.open_mode == "view":
            self.ui.lbl_caption.setText(self.conn.lang("add_wallet_open_mode_view_caption", self.active_lang))
            self.setWindowTitle(self.conn.lang("add_wallet_open_mode_view_caption", self.active_lang))
            self.ui.btn_save.setVisible(False)
        elif self.open_mode == "edit":
            self.ui.lbl_caption.setText(self.conn.lang("add_wallet_open_mode_edit_caption", self.active_lang))
            self.setWindowTitle(self.conn.lang("add_wallet_open_mode_edit_caption", self.active_lang))

    def btn_save_click(self):
        # Check is there any data to save
        if len(self.ui.txt_name.text()) == 0 and len(self.ui.txt_description.toPlainText()) == 0:
            return
        # Check is data valid
        msg_title = self.conn.lang("wallet_add_too_many_char_msg_title", self.active_lang)
        if len(self.ui.txt_name.text()) > 255:
            msg_text = self.conn.lang("wallet_add_too_many_char_name_msg_text", self.active_lang)
        elif len(self.ui.txt_description.toPlainText()) > 255:
            msg_text = self.conn.lang("wallet_add_too_many_char_description_msg_text", self.active_lang)
        # Make wall dictionary
        wall = {}
        wall["name"] = self.ui.txt_name.text()
        wall["description"] = self.ui.txt_description.toPlainText()
        if self.open_mode == "":
            # Add new wallet
            self.wallet_base.add_wallet(wall)
        elif self.open_mode == "edit":
            # Update wallet data
            wall["wallet_id"] = self.wallet_id
            self.wallet_base.set_wallet(wall)
        self.close()

    def btn_cancel_click(self):
        self.close()

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        w = self.width()
        h = self.height()
        scale = h / 330
        self.ui.lbl_caption.resize(w, self.ui.lbl_caption.height())
        self.ui.lbl_name.move(self.ui.lbl_name.pos().x(), 60*scale)
        self.ui.lbl_description.move(self.ui.lbl_description.pos().x(), 140*scale)
        self.ui.txt_name.move(self.ui.txt_name.pos().x(), 90*scale)
        self.ui.txt_name.resize(w-40, self.ui.txt_name.height())
        self.ui.txt_description.move(self.ui.txt_description.pos().x(), 170*scale)
        self.ui.txt_description.resize(w-40, self.ui.txt_description.height())
        self.ui.line.move(self.ui.line.pos().x(), h-50)
        self.ui.line.resize(w-40, self.ui.line.height())
        self.ui.btn_save.move(w-180, h-30)
        self.ui.btn_cancel.move(w-90, h-30)

        return super().resizeEvent(a0)

    def load_settings(self):
        self.setMinimumSize(550, 330)
        if self.open_mode == "":
            self.log.write_log("Wallet add started...")
        elif self.open_mode == "view":
            self.log.write_log("Wallet view started...")
        elif self.open_mode == "edit":
            self.log.write_log("Wallet edit started...")
        # Set minimum win size
        self.setMinimumSize(550, 330)
        # Load win position and size
        x = self.conn.get_setting_data("wallet_add_win_x", getParametar=True, user_id=self.active_user_id)
        y = self.conn.get_setting_data("wallet_add_win_y", getParametar=True, user_id=self.active_user_id)
        w = self.conn.get_setting_data("wallet_add_win_w", getParametar=True, user_id=self.active_user_id)
        h = self.conn.get_setting_data("wallet_add_win_h", getParametar=True, user_id=self.active_user_id)
        self.move(x,y)
        self.resize(w,h)

    def save_settings(self, argg):
        if self.open_mode == "":
            self.log.write_log("Wallet add finished.")
        elif self.open_mode == "view":
            self.log.write_log("Wallet view finished.")
        elif self.open_mode == "edit":
            self.log.write_log("Wallet edit finished.")
        x = self.pos().x()
        y = self.pos().y()
        w = self.width()
        h = self.height()
        # Save window position and size
        self.conn.set_setting_data("wallet_add_win_x", "Wallet add, Win Geometry", x, self.active_user_id)
        self.conn.set_setting_data("wallet_add_win_y", "Wallet add, Win Geometry", y, self.active_user_id)
        self.conn.set_setting_data("wallet_add_win_w", "Wallet add, Win Geometry", w, self.active_user_id)
        self.conn.set_setting_data("wallet_add_win_h", "Wallet add, Win Geometry", h, self.active_user_id)

    def retranslateUi(self):
        self.setWindowTitle(self.conn.lang("wallet_add_win_title", self.active_lang))
        self.ui.lbl_caption.setText(self.conn.lang("wallet_add_lbl_caption_add", self.active_lang))
        self.ui.lbl_name.setText(self.conn.lang("wallet_add_lbl_name", self.active_lang))
        self.ui.lbl_description.setText(self.conn.lang("wallet_add_lbl_description", self.active_lang))
        self.ui.btn_save.setText(self.conn.lang("add_event_btn_save", self.active_lang))
        self.ui.btn_cancel.setText(self.conn.lang("btn_cancel", self.active_lang))


class WalletTransfer(QtWidgets.QDialog):
    def __init__(self, user_id, user_name, language, wallet_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create variables 
        self.active_user_id = user_id
        self.active_user_name = user_name
        self.active_lang = language
        self.active_wallet_id = wallet_id
        self.from_wall = ""  # Tracks which wallet the funds are transferred from
        # Create connection to database
        self.conn = connection.ConnStart()
        self.user = connection.User(self.active_user_id)
        self.wallet_base = connection.Wallets(self.active_user_id)
        self.log = log_cls.LogData()

    def setup_gui(self):
        # Setup Gui
        self.ui = wallet_transfer_ui.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowFlag(QtCore.Qt.Dialog)
        self.setWindowModality(Qt.ApplicationModal)
        self.retranslateUi()
        # Load settings
        self.load_settings()
        # Connect events with slots
        self.ui.btn_from_main.clicked.connect(self.btn_from_main_click)
        self.ui.btn_to_main.clicked.connect(self.btn_to_main_click)
        self.ui.txt_rsd.textChanged.connect(self.txt_boxes_text_changed)
        self.ui.txt_eur.textChanged.connect(self.txt_boxes_text_changed)
        self.ui.btn_cancel.clicked.connect(self.btn_cancel_click)
        self.ui.btn_save.clicked.connect(self.btn_save_click)

        self.show()
        self.exec_()

    def btn_save_click(self):
        if self.conn.is_decimal(self.ui.txt_rsd.text()):
            rsd = float(self.ui.txt_rsd.text())
        else:
            rsd = 0
        if self.conn.is_decimal(self.ui.txt_eur.text()):
            eur = float(self.ui.txt_eur.text())
        else:
            eur = 0
        if rsd < 0 or eur < 0:
            msg_title = self.conn.lang("wallet_transfer_caption", self.active_lang)
            msg_text = self.conn.lang("wallet_transfer_msg_negative_text", self.active_lang)
            result = QtWidgets.QMessageBox.information(None, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
            return

        if self.from_wall == "main":
            self.wallet_base.transfer_from_main_wallet(self.active_wallet_id, rsd, eur)
        else:
            self.wallet_base.transfer_to_main_wallet(self.active_wallet_id, rsd, eur)
        self.close()

    def btn_cancel_click(self):
        self.close()
    
    def txt_boxes_text_changed(self):
        if self.conn.is_decimal(self.ui.txt_rsd.text()) or self.conn.is_decimal(self.ui.txt_eur.text()):
            self.ui.btn_save.setEnabled(True)
        else:
            self.ui.btn_save.setEnabled(False)

    def btn_to_main_click(self):
        self.from_wall = "custom"
        self.ui.btn_from_main.setStyleSheet("background-color: rgb(255,255,255)")
        self.ui.btn_to_main.setStyleSheet("background-color: rgb(0,255,0)")
        self.ui.frm_transfer.setVisible(True)
        txt = self.conn.lang("wallet_transfer_frm_caption2", self.active_lang)
        self.ui.lbl_frm_caption.setText(txt)


    def btn_from_main_click(self):
        self.from_wall = "main"
        self.ui.btn_from_main.setStyleSheet("background-color: rgb(0,255,0)")
        self.ui.btn_to_main.setStyleSheet("background-color: rgb(255,255,255)")
        self.ui.frm_transfer.setVisible(True)
        result = self.wallet_base.get_wallet_all(self.active_wallet_id)
        txt = self.conn.lang("wallet_transfer_frm_caption1", self.active_lang) + result[0][1]
        self.ui.lbl_frm_caption.setText(txt)

    def load_settings(self):
        self.ui.btn_save.setDisabled(True)
        self.ui.frm_transfer.setVisible(False)

    def retranslateUi(self):
        self.setWindowTitle(self.conn.lang("wallet_transfer_caption", self.active_lang))
        self.ui.lbl_caption.setText(self.conn.lang("wallet_transfer_caption", self.active_lang))
        result = self.wallet_base.get_wallet_all(self.active_wallet_id)
        txt = self.conn.lang("wallet_transfer_btn_from_main", self.active_lang) + result[0][1]
        self.ui.btn_from_main.setText(txt)
        txt = self.conn.lang("wallet_transfer_btn_to_main1", self.active_lang) + result[0][1] + self.conn.lang("wallet_transfer_btn_to_main2", self.active_lang)
        self.ui.btn_to_main.setText(txt)
        self.ui.btn_save.setText(self.conn.lang("add_event_btn_save", self.active_lang))
        self.ui.btn_cancel.setText(self.conn.lang("btn_cancel", self.active_lang))
        self.ui.lbl_eur.setText("EUR:")
        self.ui.lbl_rsd.setText("RSD:")

