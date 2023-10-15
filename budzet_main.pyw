from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
import sys

import login  # Login screen
import log_cls  # Handle 'log.txt' file
import connection  # Handle 'start_up.db' and user database
import main_ui  # GUI for main window
import add_cls  # Add EventAdd, EventTypeAdd, PlaceAdd
import event_edit_cls  # Edit/View events
import report_cls  # Shows reports
import web_cls  # Viev, Edit, Add web pages, apps...
import wallet_cls  # Wallets
import setting_cls  # User settings


def start_login_screen():
    Dialog = QtWidgets.QDialog()
    log.write_log("App started - User login...")
    ui = login.Ui_Dialog()
    user_name =  ui.setupUi(Dialog, app)
    if user_name != "":
        Dialog.close()
        log.write_log(f"Session started. User: {user_name}")
        return user_name
    else:
        Dialog.close()
        log.write_log("User login: App Quit. No session.")
        return ""


class StartMainWindow(QtWidgets.QMainWindow):
    def __init__(self, user,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = main_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self.active_user = user
        self.table_sort_order = [8, QtCore.Qt.AscendingOrder]  # User click on header
        self.filter_list = {}  # Describes filters from lst_filter
        self.opened_edit_win = 0  # Number of edit window opened
        self.ui.frm_wait.setVisible(False)  # Hide frm_wait

    def setup_main_win(self):
        self.conn = connection.ConnStart()
        self.log = log_cls.LogData()

        self.active_user_id = int(self.conn._get_user_id(self.active_user))
        self.active_lang =self.conn.user_language(self.active_user_id)
        self.log.write_log("Main window started ...")
        self.user_db = connection.User(self.active_user_id)

        self.setWindowTitle(self.conn.lang("main_win_caption", self.active_lang))
        self.retranslateUi()
        self.ui.actionExit.triggered.connect(self.mnu_user_exit_click)
        self.ui.statusbar.showMessage(self.conn.lang("main_stb_ready"))
        self.closeEvent = self._close_app_on_X
        self.ui.lcd_balance.display(float(self.user_db.get_balance_rsd()))
        main_win._set_main_window_geometry()
        self.table_populate()
        self.ui.tbl_trosak.horizontalHeader().sectionClicked.connect(self.sort_table)
        self.populate_filter_frame()
        self.ui.btn_filter_add.clicked.connect(self.btn_filter_add_click)
        self.ui.txt_filter_value.textChanged.connect(self.txt_filter_text_changed)
        self.cmb_operator_changed()
        self.ui.cmb_operator.currentIndexChanged.connect(self.cmb_operator_changed)
        self.ui.lst_filter.itemChanged.connect(self.lst_change_event)
        self.lst_change_event()
        self.ui.btn_filter_apply_or.clicked.connect(self.btn_apply_or_click)
        self.ui.btn_filter_apply_and.clicked.connect(self.btn_apply_and_click)
        self.ui.btn_show_all.clicked.connect(self.btn_show_all_click)
        self.update_total()
        self.ui.txt_filter_value.mousePressEvent = self.txt_filter_value_focused
        # Connect actions with slots
        self.ui.actionEvent.triggered.connect(self.mnu_actionEvent_click)
        self.ui.actionEvents.triggered.connect(self.mnu_actionEvents_click)
        self.ui.actionEvent.setShortcut("Ctrl+A")
        self.ui.actionEvent_type.triggered.connect(self.mnu_actionEvent_type_click)
        self.ui.actionEvent_type.setShortcut("Ctrl+T")
        self.ui.actionLocation.triggered.connect(self.mnu_actionPlace_click)
        self.ui.actionLocation.setShortcut("Ctrl+L")
        self.ui.actionEvents.setShortcut("Ctrl+Space")
        self.ui.actionWeb.triggered.connect(self.mnu_actionWeb_click)
        self.ui.actionWeb_view.triggered.connect(self.mnu_actionWeb_view_click)
        self.ui.actionWallets.triggered.connect(self.mnu_actionWallets_click)
        self.ui.actionUser_info.triggered.connect(self.mnu_user_info_click)

        self.ui.tbl_trosak.installEventFilter(self)
        
        self.ui.btn_show_all.setEnabled(False)
        self.setup_tbl_trosak_menu()

    def mnu_user_info_click(self):
        us = setting_cls.UserInfo(self.active_user_id, self.active_user, self.active_lang)
        us.setup_gui()
    
    def mnu_actionWallets_click(self):
        wall = wallet_cls.Wallet(self.active_user_id, self.active_user, self.active_lang)
        wall.setup_gui()
        self.table_populate()
        self.ui.lcd_balance.display(float(self.user_db.get_balance_rsd()))
        self.update_total()
    
    def mnu_actionWeb_click(self):
        web_add = web_cls.WebAdd(self.active_user_id, self.active_user, self.active_lang)
        web_add.setup_ui()
        
    def mnu_actionWeb_view_click(self):
        web_view = web_cls.Web(self.active_lang, self.active_user_id, self.active_user)
        web_view.setup_ui()

    def mnu_actionEvents_click(self):
        # Create list of event_ids to work with
        ev_ids = []
        counter = 0
        for i in range(self.ui.tbl_trosak.rowCount()):
            if not self.ui.tbl_trosak.isRowHidden(i):
                ev_ids.append(int(self.ui.tbl_trosak.item(i, 10).text()))
                counter += 1
        # Check if there is any data to show
        if counter < 1:
            msg_title = self.conn.lang("main_msg_events_show_title", self.active_lang)
            msg_text = self.conn.lang("main_msg_events_show_text", self.active_lang)
            result = QtWidgets.QMessageBox.information(None, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
            return
        # Show report dialog
        report = report_cls.EventReport(self.active_user_id, self.active_user, self.active_lang, ev_ids)
        report.setup_ui()

    def eventFilter(self, a0: 'QObject', a1: 'QEvent') -> bool:
        if a0 == self.ui.tbl_trosak and a1.type() == QtCore.QEvent.KeyPress:
            if a1.key() == QtCore.Qt.Key_Enter or a1.key() == QtCore.Qt.Key_Return:
                self.tbl_trosak_mnu_view_triggered()
                return True
        return super().eventFilter(a0, a1)

    def mnu_actionPlace_click(self):
        plc = add_cls.AddPlace(self.active_user_id, self.active_lang)
        plc.setup_ui()

    def mnu_actionEvent_type_click(self):
        ev_type = add_cls.AddEventType(self.active_user_id, self.active_lang)
        ev_type.setup_ui()

    def setup_tbl_trosak_menu(self):
        # Create Menu
        self.tbl_trosak_menu = QtWidgets.QMenu(self.ui.tbl_trosak)
        # Creat menu items
        self.tbl_trosak_mnu_view = QtWidgets.QAction(self.conn.lang("mnu_context_view", self.active_lang), self.ui.tbl_trosak)
        self.tbl_trosak_mnu_view.setShortcut("Ctrl+Return")
        self.tbl_trosak_mnu_edit = QtWidgets.QAction(self.conn.lang("mnu_context_edit", self.active_lang), self.ui.tbl_trosak)
        self.tbl_trosak_mnu_delete = QtWidgets.QAction(self.conn.lang("mnu_context_delete", self.active_lang), self.ui.tbl_trosak)
        # Add items to menu
        self.tbl_trosak_menu.addAction(self.tbl_trosak_mnu_view)
        self.tbl_trosak_menu.addAction(self.tbl_trosak_mnu_edit)
        self.tbl_trosak_menu.addAction(self.tbl_trosak_mnu_delete)
        # Connect menu items to function
        self.tbl_trosak_mnu_view.triggered.connect(self.tbl_trosak_mnu_view_triggered)
        self.tbl_trosak_mnu_edit.triggered.connect(self.tbl_trosak_mnu_edit_triggered)
        self.tbl_trosak_mnu_delete.triggered.connect(self.tbl_trosak_mnu_delete_triggered)
        # Setup tbl_trosak for custom menus
        self.ui.tbl_trosak.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.tbl_trosak.customContextMenuRequested.connect(self.tbl_trosak_menu_show)
        self.ui.tbl_trosak.cellDoubleClicked.connect(self.tbl_trosak_mnu_view_triggered)

    def tbl_trosak_menu_show(self, position):
        row = self.ui.tbl_trosak.currentRow()
        
        if row >= 0:
            if self.ui.tbl_trosak.item(row, 7).text() == "TRANSFER":
                self.tbl_trosak_mnu_delete.setEnabled(False)
                self.tbl_trosak_mnu_edit.setEnabled(False)
            else:
                self.tbl_trosak_mnu_delete.setEnabled(True)
                self.tbl_trosak_mnu_edit.setEnabled(True)

        self.tbl_trosak_menu.exec_(self.ui.tbl_trosak.viewport().mapToGlobal(position))

    def tbl_trosak_mnu_view_triggered(self):
        if self.ui.tbl_trosak.rowCount() > 0:
            # Create list od event ID-s to show and select one to be first shown
            ev_lst = []
            for i in range(self.ui.tbl_trosak.rowCount()):
                if not self.ui.tbl_trosak.isRowHidden(i):
                    ev_lst.append(int(self.ui.tbl_trosak.item(i,10).text()))
            row = self.ui.tbl_trosak.currentRow()
            ev_id = int(self.ui.tbl_trosak.item(row, 10).text())
            # Display event
            view_event = event_edit_cls.ViewEditEvent(self.active_user_id, self.active_user, self.active_lang, ev_id, open_for_view=True)
            result = view_event.setup_gui(list_of_IDs_to_show=ev_lst)
            # Set table current item to last shown item in view
            row = -1
            for i in range(self.ui.tbl_trosak.rowCount()):
                if not self.ui.tbl_trosak.isRowHidden(i):
                    row += 1
                    if int(self.ui.tbl_trosak.item(i,10).text()) == result:
                        self.ui.tbl_trosak.setCurrentCell(i, self.ui.tbl_trosak.currentColumn())

    def tbl_trosak_mnu_edit_triggered(self):
        if self.ui.tbl_trosak.rowCount() > 0:
            # Increase +1 opened edit windows
            self.opened_edit_win += 1
            # Create event ID to show
            row = self.ui.tbl_trosak.currentRow()
            ev_id = int(self.ui.tbl_trosak.item(row, 10).text())
            # Display event
            view_event = event_edit_cls.ViewEditEvent(self.active_user_id, self.active_user, self.active_lang, ev_id, open_for_view=False)
            result = view_event.setup_gui()
            # Decrease -1 opened edit windows
            self.opened_edit_win -= 1
            # Update current row data if needed
            if result == "":
                return
            else:
                row = self.ui.tbl_trosak.currentRow()
                itm = self.ui.tbl_trosak
                itm.item(row, 0).setText(result[5])
                itm.item(row, 1).setText(str(result[1]))
                itm.item(row, 2).setText(str(result[2]))
                itm.item(row, 3).setText(str(result[3]))
                itm.item(row, 4).setText(str(result[4]))
                itm.item(row, 5).setText(str(self.user_db.get_event_type_all(event_type_id=result[12])[0][1]))
                itm.item(row, 6).setText(result[9])
                itm.item(row, 7).setText(result[10])
                itm.item(row, 8).setText(str(self.user_db.get_place_all(place_id=result[13])[0][1]))
                itm.item(row, 9).setText(str(result[6]))
                itm.item(row, 10).setText(str(result[0]))
                self.ui.lcd_balance.display(float(self.user_db.get_balance_rsd()))
            self.ui.lcd_balance.display(float(self.user_db.get_balance_rsd()))
            self.update_total()
        
    def tbl_trosak_mnu_delete_triggered(self):
        if self.ui.tbl_trosak.currentRow() >= 0:
            if self.opened_edit_win > 0:
                msg_title = self.conn.lang("main_msg_opened_edit_window_title", self.active_lang)
                msg_text = self.conn.lang("main_msg_opened_edit_window_text", self.active_lang)
                msg_text = msg_text.replace("#", str(self.opened_edit_win))
                result = QtWidgets.QMessageBox.information(None, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
                return
            row_is_hidden = self.ui.tbl_trosak.isRowHidden(self.ui.tbl_trosak.currentRow())
            if row_is_hidden:
                return
            msg_title = self.conn.lang("main_tbl_trosak_menu_delete_title", self.active_lang)
            msg_text = self.conn.lang("main_tbl_trosak_menu_delete_text", self.active_lang)
            result = QtWidgets.QMessageBox.question(None, msg_title, msg_text, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.No:
                return
            row = self.ui.tbl_trosak.currentRow()
            id_to_del = int(self.ui.tbl_trosak.item(row, 10).text())
            self.user_db.delete_event(event_id=id_to_del)
            pos = [row-1, self.ui.tbl_trosak.currentColumn()]
            self.table_populate(position_to_show=pos)
            self.ui.lcd_balance.display(float(self.user_db.get_balance_rsd()))
            self.update_total()
    
    def mnu_actionEvent_click(self):
        new_event = add_cls.EventAdd(self.active_user, self.active_user_id, self.active_lang)
        new_event.setup_ui()
        new_event.show()
        new_event.exec_()
        self.ui.tbl_trosak.clear()
        self.table_populate()
        self.btn_show_all_click()
        self.ui.lcd_balance.display(float(self.user_db.get_balance_rsd()))

    def txt_filter_value_focused(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.ui.txt_filter_value.selectAll()

    def btn_show_all_click(self):
        for i in range(self.ui.tbl_trosak.rowCount()):
            self.ui.tbl_trosak.setRowHidden(i, False)
        self.ui.label.setText(self.conn.lang("main_event_browser", self.active_lang) + str(self.ui.tbl_trosak.rowCount()))
        self.update_total()
        for i in range(0, self.ui.lst_filter.count()):
            if self.ui.lst_filter.item(i).checkState() == QtCore.Qt.Checked:
                self.ui.btn_filter_apply_or.setEnabled(True)
                self.ui.btn_filter_apply_and.setEnabled(True)
        self.ui.btn_show_all.setEnabled(False)

    def calculate_filter(self, return_list_and_number_of_filters=False):
        # First load to dictionary all visible rows with value 1
        mp = {}
        for i in range(self.ui.tbl_trosak.rowCount()):
            if self.ui.tbl_trosak.isRowHidden(i):
                mp[i] = -1
            else:
                mp[i] = 0
        # Then we apply filters
        number_of_checked_filters = 0
        for i in range(0, self.ui.lst_filter.count()):
            item = self.ui.lst_filter.item(i)
            if item.checkState() != QtCore.Qt.Checked:
                continue
            number_of_checked_filters += 1
            op_exec = self.filter_list[item.text()]
            for i in range(0, self.ui.tbl_trosak.rowCount()):
                if mp[i] >= 0:
                    if op_exec[0] == 9:
                        cell = ""
                        for j in range(0, 9):
                            cell = cell + " " + self.ui.tbl_trosak.item(i, j).text().lower()
                    else:
                        cell = self.ui.tbl_trosak.item(i, op_exec[0]).text().lower()
                    if op_exec[1] == "=":
                        if op_exec[0] in range(1,5):
                            if float(cell) == float(op_exec[2]):
                                mp[i] += 1
                        elif op_exec[0] == 0:
                            if self.date_integer(cell) == op_exec[3]:
                                mp[i] += 1
                        else:
                            if cell == op_exec[2]:
                                mp[i] += 1
                    if op_exec[1] == "<>":
                        if op_exec[0] in range(1,5):
                            if float(cell) != float(op_exec[2]):
                                mp[i] += 1
                        elif op_exec[0] == 0:
                            if self.date_integer(cell) != op_exec[3]:
                                mp[i] += 1
                        else:
                            if cell != op_exec[2]:
                                mp[i] += 1
                    if op_exec[1] == "~":
                        if cell.find(op_exec[2]) >= 0:
                            mp[i] += 1
                    if op_exec[1] == ">":
                        if op_exec[0] in range(1,5):
                            if float(cell) > float(op_exec[2]):
                                mp[i] += 1
                        elif op_exec[0] == 0:
                            if self.date_integer(cell) > op_exec[3]:
                                mp[i] += 1
                        else:
                            if self.conn.is_decimal(cell) and self.conn.is_decimal(op_exec[2]):
                                if float(cell) > float(op_exec[2]):
                                    mp[i] += 1
                    if op_exec[1] == "<":
                        if op_exec[0] in range(1,5):
                            if float(cell) < float(op_exec[2]):
                                mp[i] += 1
                        elif op_exec[0] == 0:
                            if self.date_integer(cell) < op_exec[3]:
                                mp[i] += 1
                        else:
                            if self.conn.is_decimal(cell) and self.conn.is_decimal(op_exec[2]):
                                if float(cell) < float(op_exec[2]):
                                    mp[i] += 1
        if return_list_and_number_of_filters:
            return mp, number_of_checked_filters
        else:
            return mp
                                    
    def btn_apply_or_click(self):
        if self.ui.tbl_trosak.rowCount() < 1:
            return
        mp = self.calculate_filter()
        visible_rows = 0
        for i in range(self.ui.tbl_trosak.rowCount()):
            if mp[i] > 0:
                self.ui.tbl_trosak.setRowHidden(i, False)
                visible_rows += 1
            else:
                self.ui.tbl_trosak.setRowHidden(i, True)

        self.ui.label.setText(self.conn.lang("main_event_browser", self.active_lang) + str(visible_rows))
        self.update_total()
        self.ui.btn_filter_apply_and.setDisabled(False)
        self.ui.btn_filter_apply_or.setDisabled(True)
        self.ui.btn_show_all.setEnabled(True)

    def btn_apply_and_click(self):
        if self.ui.tbl_trosak.rowCount() < 1:
            return
        mp, set_visible = self.calculate_filter(return_list_and_number_of_filters=True)

        visible_rows = 0
        # set_visible = max(mp.values())
        # if set_visible <= 0:
        #     set_visible = 1
        for i in range(self.ui.tbl_trosak.rowCount()):
            if mp[i] == set_visible:
                self.ui.tbl_trosak.setRowHidden(i, False)
                visible_rows += 1
            else:
                self.ui.tbl_trosak.setRowHidden(i, True)

        self.ui.label.setText(self.conn.lang("main_event_browser", self.active_lang) + str(visible_rows))
        self.update_total()
        self.ui.btn_filter_apply_and.setDisabled(True)
        self.ui.btn_filter_apply_or.setDisabled(False)
        self.ui.btn_show_all.setEnabled(True)

    def keyPressEvent(self, a0: QtGui.QKeyEvent) -> None:
        if a0.key() == QtCore.Qt.Key_Delete and self.ui.lst_filter.hasFocus() and self.ui.lst_filter.count() > 0:
            item = self.ui.lst_filter.currentItem()
            self.filter_list.pop(item.text(), None)
            self.ui.lst_filter.takeItem(self.ui.lst_filter.row(item))
            self.lst_change_event()
        elif a0.key() == QtCore.Qt.Key_Return or a0.key() == QtCore.Qt.Key_Enter:
            self.btn_filter_add_click()
        return super().keyPressEvent(a0)
    
    def lst_change_event(self):
        self.ui.btn_filter_apply_or.setEnabled(False)
        self.ui.btn_filter_apply_and.setEnabled(False)
        for i in range(0, self.ui.lst_filter.count()):
            if self.ui.lst_filter.item(i).checkState() == QtCore.Qt.Checked:
                self.ui.btn_filter_apply_or.setEnabled(True)
                self.ui.btn_filter_apply_and.setEnabled(True)

    def cmb_operator_changed(self):
        if self.ui.cmb_operator.currentData() == "<>":
            self.ui.btn_filter_add.setEnabled(True)
        else:
            if self.ui.txt_filter_value.text() == "":
                self.ui.btn_filter_add.setEnabled(False)
            else:
                self.ui.btn_filter_add.setEnabled(True)

    def txt_filter_text_changed(self):
        if self.ui.cmb_operator.currentData() == "<>":
            self.ui.btn_filter_add.setEnabled(True)
        else:
            if self.ui.txt_filter_value.text() == "":
                self.ui.btn_filter_add.setEnabled(False)
            else:
                self.ui.btn_filter_add.setEnabled(True)
        
        self.ui.statusbar.showMessage(self.conn.lang("main_stb_ready", self.active_lang))
    
    def btn_filter_add_click(self):
        lst_text = self.conn.lang("main_filter_list_text", self.active_lang)
        txt_value = self.ui.txt_filter_value.text()
        col = self.ui.cmb_column.currentText()
        col_idx = self.ui.cmb_column.currentData()
        opr = self.ui.cmb_operator.currentText()
        opr_val = self.ui.cmb_operator.currentData()

        item_to_add = f"{lst_text} {col} {opr} '{txt_value}'"
        item = QtWidgets.QListWidgetItem()
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        item.setCheckState(QtCore.Qt.Checked)
        item.setText(item_to_add)
        # Check if there is same condition already in list
        for i in range(0, self.ui.lst_filter.count()):
            if self.ui.lst_filter.item(i).text() == item_to_add:
                return
        # Check if txt value is decimal if column is in [1,2,3,4]
        if col_idx in ([1,2,3,4]):
            if self.conn.is_decimal(txt_value) is False:
                return
            if opr_val == "~":
                return
        # Check is txt_value valid date
        result = self.date_integer(txt_value)
        if result == 0 and col_idx == 0 and opr_val != "~":
            return
        # Only valid operator for 'All colums' is '~'
        if col_idx == 9 and opr_val != "~":
            return
        # Add new filter to list and self.filter_list
        self.ui.lst_filter.addItem(item)
        self.filter_list[item_to_add] = [col_idx, opr_val, txt_value.lower(), result]
        self.lst_change_event()

    def date_integer(self, txtValue):
        a = txtValue.split(".")
        result = ""
        if len(a) < 3:
            return 0
        for i in a:
            result = i + result
        if self.conn.is_decimal(result):
            return result
        else:
            return 0

    def populate_filter_frame(self):
        # Populate column ComboBox
        for i in range(0,9):
            self.ui.cmb_column.addItem(self.ui.tbl_trosak.horizontalHeaderItem(i).text(),i)
        # Add 'all columns' item
        self.ui.cmb_column.addItem(self.conn.lang("main_cmb_column_all_columns", self.active_lang), 9)
        # Populate operand ComboBox
        oprerand = [
            (self.conn.lang("main_filter_operand_equal",self.active_lang), "="),
            (self.conn.lang("main_filter_operand_not_equal",self.active_lang), "<>"),
            (self.conn.lang("main_filter_operand_contains",self.active_lang), "~"),
            (self.conn.lang("main_filter_operand_greater",self.active_lang), ">"),
            (self.conn.lang("main_filter_operand_less",self.active_lang), "<")
            ]
        for i in oprerand:
            self.ui.cmb_operator.addItem(i[0], i[1])
        # Set current item for user
        self.ui.cmb_column.setCurrentIndex(self.conn.get_setting_data("main_filter_cmb_column", getParametar=True, user_id=self.active_user_id))
        self.ui.cmb_operator.setCurrentIndex(self.conn.get_setting_data("main_filter_cmb_operand", getParametar=True, user_id=self.active_user_id))

    def sort_table(self, column):
        if column == 0:
            col = 9
        else:
            col = column
        if col == self.table_sort_order[0]:
            if self.table_sort_order[1] == QtCore.Qt.AscendingOrder:
                self.table_sort_order[1] = QtCore.Qt.DescendingOrder
                self.ui.tbl_trosak.sortItems(col, Qt.DescendingOrder)
            else:
                sort_order = sort_order = QtCore.Qt.AscendingOrder
                self.table_sort_order[1] = QtCore.Qt.AscendingOrder
                self.ui.tbl_trosak.sortItems(col, Qt.AscendingOrder)
        else:
            self.table_sort_order = [col, QtCore.Qt.AscendingOrder]
            self.ui.tbl_trosak.sortItems(col, Qt.AscendingOrder)
        self.ui.tbl_trosak.horizontalHeader().setSortIndicator(column, self.table_sort_order[1])
        self.ui.tbl_trosak.horizontalHeader().setSortIndicatorShown(True)

    def table_populate(self, position_to_show=[-2,0]):
        if position_to_show[0] == -1:
            position_to_show[0] = 0
        # Get data from database
        data = self.user_db.get_data_trosak_for_main_win()
        # Update record count label
        number_of_records = self.conn.lang("main_event_browser", self.active_lang) + str(len(data))
        self.ui.label.setText(number_of_records)
        # Set headers captions
        row_n = len(data)  # Number of rows
        if len(data) == 0:
            col_n = 10
        else:
            col_n = len(data[0])  # Number od columns
        self.ui.tbl_trosak.setRowCount(row_n)
        self.ui.tbl_trosak.setColumnCount(col_n)
        header = []
        header.append(self.conn.lang("main_tbl_header_datum", self.active_lang))
        header.append(self.conn.lang("main_tbl_header_prihod_rsd", self.active_lang))
        header.append(self.conn.lang("main_tbl_header_rashod_rsd", self.active_lang))
        header.append(self.conn.lang("main_tbl_header_prihod_eur", self.active_lang))
        header.append(self.conn.lang("main_tbl_header_rashod_eur", self.active_lang))
        header.append(self.conn.lang("main_tbl_header_vrsta_naziv", self.active_lang))
        header.append(self.conn.lang("main_tbl_header_opis", self.active_lang))
        header.append(self.conn.lang("main_tbl_header_partner", self.active_lang))
        header.append(self.conn.lang("main_tbl_header_mesto_naziv", self.active_lang))
        header.append("datum_int")
        self.ui.tbl_trosak.setHorizontalHeaderLabels(header)
        
        if len(data) == 0:
            return
        # Populate table with data
        cur_row = 0
        cur_col = 0
        for x in data:
            for y in x:
                self.ui.tbl_trosak.setItem(cur_row, cur_col, QtWidgets.QTableWidgetItem(str(y)))
                cur_col += 1
            cur_row += 1
            cur_col = 0
        # Hide column datum_int (index=9) and trosak_id (index=10)
        self.ui.tbl_trosak.setColumnHidden(9, True)
        self.ui.tbl_trosak.setColumnHidden(10, True)
        # Set alignment for numeric columns
        for row in range(self.ui.tbl_trosak.rowCount()):
            for col in range(1,5):
                self.ui.tbl_trosak.item(row,col).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # Show last row if position is not set
        if position_to_show[0] < 0:
            self.ui.tbl_trosak.scrollToBottom()
            if row_n > 0:
                self.ui.tbl_trosak.setCurrentCell(row_n-1, 0)
        else:
            if position_to_show[0] < 0:
                position_to_show[0] = 0
            if row_n > 0:
                self.ui.tbl_trosak.scroll(position_to_show[0], position_to_show[1])
                self.ui.tbl_trosak.setCurrentCell(position_to_show[0], position_to_show[1])
        # Load headers widths
        for i in range (0,9):
            podesavanje_funkcija = "main_tbl_header_width" + str(i)
            result = self.conn.get_setting_data(podesavanje_funkcija, getParametar=True, user_id=self.active_user_id)
            self.ui.tbl_trosak.setColumnWidth(i, result)
        # Set table to Read Only
        self.ui.tbl_trosak.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

    def update_total(self):
        i_rsd = 0.0
        o_rsd = 0.0
        i_eur = 0.0
        o_eur = 0.0
        for i in range(self.ui.tbl_trosak.rowCount()):
            if self.ui.tbl_trosak.isRowHidden(i) is not True:
                item = self.ui.tbl_trosak.item(i,1).text()
                i_rsd += float(item)
                item = self.ui.tbl_trosak.item(i,2).text()
                o_rsd += float(item)
                item = self.ui.tbl_trosak.item(i,3).text()
                i_eur += float(item)
                item = self.ui.tbl_trosak.item(i,4).text()
                o_eur += float(item)
        t_rsd = i_rsd - o_rsd
        t_eur = i_eur - o_eur
        self.ui.lbl_rsd_income.setText(self.conn.lang("main_lbl_income", self.active_lang) + f"{i_rsd:.2f}")
        self.ui.lbl_rsd_outcome.setText(self.conn.lang("main_lbl_outcome", self.active_lang) + f"{o_rsd:.2f}")
        self.ui.lbl_eur_income.setText(self.conn.lang("main_lbl_income", self.active_lang) + f"{i_eur:.2f}")
        self.ui.lbl_eur_outcome.setText(self.conn.lang("main_lbl_outcome", self.active_lang) + f"{o_eur:.2f}")
        self.ui.lbl_rsd_total.setText(self.conn.lang("main_lbl_total", self.active_lang) + f"{t_rsd:.2f}")
        self.ui.lbl_eur_total.setText(self.conn.lang("main_lbl_total", self.active_lang) + f"{t_eur:.2f}")

    def _close_app_on_X(self, event):
        self.mnu_user_exit_click()

    def _set_main_window_geometry(self):
        x = self.conn.get_setting_data("main_x", getParametar=True, user_id=self.active_user_id)
        y = self.conn.get_setting_data("main_y", getParametar=True, user_id=self.active_user_id)
        w = self.conn.get_setting_data("main_w", getParametar=True, user_id=self.active_user_id)
        h = self.conn.get_setting_data("main_h", getParametar=True, user_id=self.active_user_id)
        f = self.conn.get_setting_data("main_full_screen", getParametar=True, user_id=self.active_user_id)
        self.setGeometry(x,y,w,h)
        self.move(x,y)
        if f == 1:
            self.showMaximized()

    def resizeEvent(self, event):
        tbl_x = self.ui.tbl_trosak.geometry().x()
        tbl_y = self.ui.tbl_trosak.geometry().y()
        tbl_h = self.ui.tbl_trosak.geometry().height()
        tbl_w = self.ui.tbl_trosak.geometry().width()
        lcd_x = self.ui.lcd_balance.geometry().x()
        lcd_y = self.ui.lcd_balance.geometry().y()
        lcd_h = self.ui.lcd_balance.geometry().height()
        lcd_w = self.ui.lcd_balance.geometry().width()
        lcd_x = self.width() - 280
        tbl_h = self.height() - 380
        tbl_w = self.width() - 20    
        self.ui.lcd_balance.setGeometry(QtCore.QRect(lcd_x, lcd_y, lcd_w, lcd_h))
        self.ui.tbl_trosak.setGeometry(QtCore.QRect(tbl_x, tbl_y, tbl_w, tbl_h))
        self.ui.lbl_balance.move(self.width() - 570, 60)
        self.ui.lbl_top_background.resize(QtCore.QSize(self.width(), 90))
        self.ui.frame.resize(self.width()-20, 155)
        # self.ui.lst_filter.resize(self.width()-320, 110)
        # self.ui.btn_filter_apply.move(self.width()-120, 120)
        x = str(self.pos().x())
        y = str(self.pos().y())
        w = str(self.width())
        h = str(self.height())
        self.ui.statusbar.showMessage(f"Window geometry changed. Pos = ({x} x {y})  Size = ({w} x {h})")
        QtCore.QTimer.singleShot(5000, lambda: self.ui.statusbar.showMessage(self.conn.lang("main_stb_ready",self.active_lang)))

    def mnu_user_exit_click(self):
        # Save main window position and size
        a = self.isMaximized()
        if self.isMaximized():
            self.conn.set_setting_data("main_full_screen","Full Screen", 1, self.active_user_id)
        else:   
            self.conn.set_setting_data("main_x","Main Window X pos", self.pos().x(), self.active_user_id)
            self.conn.set_setting_data("main_y","Main Window Y pos", self.pos().y(), self.active_user_id)
            self.conn.set_setting_data("main_w","Main Window WIDTH", self.width(), self.active_user_id)
            self.conn.set_setting_data("main_h","Main Window HEIGHT", self.height(), self.active_user_id)
            self.conn.set_setting_data("main_full_screen","Full Screen", 0, self.active_user_id)
        # Save column width in table
        for i in range (0,9):
            data = self.ui.tbl_trosak.columnWidth(i)
            podesavanje_funkcija = "main_tbl_header_width" + str(i)
            self.conn.set_setting_data(podesavanje_funkcija, "Sirina kolona u tabeli", data, self.active_user_id)
        # Save position for combo boxes
        self.conn.set_setting_data("main_filter_cmb_column", "Current index", self.ui.cmb_column.currentIndex(), self.active_user_id)
        self.conn.set_setting_data("main_filter_cmb_operand", "Current index", self.ui.cmb_operator.currentIndex(), self.active_user_id)
        self.close()
        app.closeAllWindows()

    def retranslateUi(self):
        a = self.conn.get_users_all()
        for i in a:
            if i[0] == self.active_user_id:
                ime = f"{self.active_user}, {i[5]} {i[4]}"
        self.ui.lbl_user.setText(ime)
        self.ui.lcd_balance.setToolTip(self.conn.lang("main_lcd_balance_tt",self.active_lang))
        self.ui.label.setText(self.conn.lang("main_event_browser",self.active_lang))
        self.ui.menuUser.setTitle(self.conn.lang("main_menu_user",self.active_lang))
        self.ui.menuAdd.setTitle(self.conn.lang("main_menu_add",self.active_lang))
        self.ui.menuHelp.setTitle(self.conn.lang("main_menu_help",self.active_lang))
        self.ui.toolBar.setWindowTitle("toolBar")
        self.ui.actionUser_info.setText(self.conn.lang("main_action_user_info",self.active_lang))
        self.ui.actionUser_language.setText(self.conn.lang("main_action_user_language",self.active_lang))
        self.ui.actionUser_config.setText(self.conn.lang("main_action_user_config",self.active_lang))
        self.ui.actionExit.setText(self.conn.lang("main_action_exit",self.active_lang))
        self.ui.actionImport_Database.setText(self.conn.lang("main_action_import_database",self.active_lang))
        self.ui.actionExport_Database.setText(self.conn.lang("main_action_export_database",self.active_lang))
        self.ui.actionEvent.setText(self.conn.lang("main_action_event",self.active_lang))
        self.ui.actionEvent.setToolTip(self.conn.lang("main_action_event_tt",self.active_lang))
        self.ui.actionEvent_type.setText(self.conn.lang("main_action_event_type",self.active_lang))
        self.ui.actionEvent_type.setToolTip(self.conn.lang("main_action_event_type_tt",self.active_lang))
        self.ui.actionLocation.setText(self.conn.lang("main_action_location",self.active_lang))
        self.ui.actionLocation.setToolTip(self.conn.lang("main_action_location_tt",self.active_lang))
        self.ui.actionWallet.setText(self.conn.lang("main_action_bank",self.active_lang))
        self.ui.actionWallet.setToolTip(self.conn.lang("main_action_bank_tt",self.active_lang))
        self.ui.actionWeb.setText(self.conn.lang("main_action_web",self.active_lang))
        self.ui.actionWeb.setToolTip(self.conn.lang("main_action_web_tt",self.active_lang))
        self.ui.actionAdress_book.setText(self.conn.lang("main_action_adress_book",self.active_lang))
        self.ui.actionAdress_book.setToolTip(self.conn.lang("main_action_adress_book_tt",self.active_lang))
        self.ui.actionHelp.setText(self.conn.lang("main_action_help",self.active_lang))
        self.ui.actionAbout.setText(self.conn.lang("main_action_about",self.active_lang))
        self.ui.lbl_balance.setText(self.conn.lang("main_lbl_balance",self.active_lang))
        self.ui.lbl_filter_caption.setText(self.conn.lang("main_lbl_filter_caption",self.active_lang))
        self.ui.lbl_filter_column.setText(self.conn.lang("main_lbl_filter_column",self.active_lang))
        self.ui.lbl_filter_operand.setText(self.conn.lang("main_lbl_filter_operand",self.active_lang))
        self.ui.lbl_filter_value.setText(self.conn.lang("main_lbl_filter_value",self.active_lang))
        self.ui.btn_filter_add.setText(self.conn.lang("main_btn_filter_add",self.active_lang))
        self.ui.btn_filter_apply_or.setText(self.conn.lang("main_btn_filter_apply_or",self.active_lang))
        self.ui.btn_show_all.setText(self.conn.lang("main_btn_show_all",self.active_lang))
        self.ui.grp_rsd.setTitle(self.conn.lang("main_grp_rsd",self.active_lang))
        self.ui.grp_eur.setTitle(self.conn.lang("main_grp_eur",self.active_lang))
        self.ui.lbl_rsd_income.setText(self.conn.lang("main_lbl_income",self.active_lang))
        self.ui.lbl_eur_income.setText(self.conn.lang("main_lbl_income",self.active_lang))
        self.ui.lbl_rsd_outcome.setText(self.conn.lang("main_lbl_outcome",self.active_lang))
        self.ui.lbl_eur_outcome.setText(self.conn.lang("main_lbl_outcome",self.active_lang))
        self.ui.lbl_rsd_total.setText(self.conn.lang("main_lbl_total",self.active_lang))
        self.ui.lbl_eur_total.setText(self.conn.lang("main_lbl_total",self.active_lang))
        self.ui.btn_filter_apply_and.setText(self.conn.lang("main_btn_filter_apply_and",self.active_lang))
        self.ui.btn_filter_apply_or.setToolTip(self.conn.lang("main_btn_filter_apply_or_tt",self.active_lang))
        self.ui.btn_filter_apply_and.setToolTip(self.conn.lang("main_btn_filter_apply_and_tt",self.active_lang))
        self.ui.menuView.setTitle(self.conn.lang("main_menuView",self.active_lang))
        self.ui.actionEvents.setText(self.conn.lang("main_action_events",self.active_lang))
        self.ui.actionWallets.setText(self.conn.lang("main_action_wallets",self.active_lang))
        self.ui.actionAdress_Book_view.setText(self.conn.lang("main_action_adress_book_view",self.active_lang))
        self.ui.actionWeb_view.setText(self.conn.lang("main_action_web_view",self.active_lang))
        self.ui.lbl_wait_title.setText(self.conn.lang("wait_msg_win_title",self.active_lang))
        self.ui.lbl_wait_text.setText(self.conn.lang("wait_msg_lbl_message",self.active_lang))







app = QtWidgets.QApplication(sys.argv)
log = log_cls.LogData()
log.reset_log()

active_user_name = start_login_screen()
if active_user_name == "":
    app.quit()
    sys.exit()

main_win = StartMainWindow(active_user_name)
main_win.setup_main_win()

main_win.show()
app.exec_()





log.end_program()

print (f"Korisnik: {active_user_name}")
