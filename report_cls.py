from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from matplotlib import pyplot as plt
from matplotlib.ticker import ScalarFormatter
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


import connection
import log_cls
import report_ui
import event_edit_cls
import chart_show_ui
import chart_edit_ui


class EventReport(QtWidgets.QDialog):
    """
    Shows event report window, enables grouping data and various report formats.
    """
    def __init__(self, user_id, user_name, language, events_ids, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create variables
        self.active_user_id = user_id
        self.active_user_name = user_name
        self.active_lang = language
        self.events_id_list = events_ids  # List of event IDs to work with
        self.active_group = ""  # Active grouping data
        self.active_events = []  # List of events to populate widgets
        self.active_events_details = []  # List of events for selected group
        # Create connection with databases
        self.conn = connection.ConnStart()
        self.user = connection.User(self.active_user_id)
        self.log = log_cls.LogData()

    def setup_ui(self):
        self.log.write_log("Events report started ... ")
        # Setup widgets
        self.ui = report_ui.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowFlag(QtCore.Qt.Dialog)
        self.setWindowModality(Qt.ApplicationModal)
        self.ui.tab_info.setVisible(False)
        self.ui.tbl_tree.setAlternatingRowColors(True)
        self.ui.tbl_data.setAlternatingRowColors(True)
        self.ui.tbl_details.setAlternatingRowColors(True)
        self.ui.tab_data.setCurrentWidget(self.ui.tab_table)
        # Setup widgets language
        self.retranslateUi()
        self._setup_dialog_and_widgets()
        # Connect events with slots
        self.ui.btn_reset.clicked.connect(self.btn_reset_click)
        self.ui.btn_group_event_type.clicked.connect(self.btn_group_event_type_click)
        self.ui.btn_group_partner.clicked.connect(self.btn_group_partner_click)
        self.ui.btn_group_place.clicked.connect(self.btn_group_place_click)
        self.ui.btn_group_description.clicked.connect(self.btn_group_description_click)
        self.ui.btn_group_date.clicked.connect(self.btn_group_date_click)
        self.ui.rdb_days.toggled.connect(self.group_by_date)
        self.ui.rdb_weeks.toggled.connect(self.group_by_date)
        self.ui.rdb_months.toggled.connect(self.group_by_date)
        self.ui.rdb_years.toggled.connect(self.group_by_date)
        self.ui.sld_tree_indent.valueChanged.connect(self.sld_tree_indent_changed)
        self.ui.lbl_tree_indent_max.returnPressed.connect(self.indent_max_return_press)
        self.ui.lbl_tree_indent_char.textChanged.connect(self.indent_char_changed)
        self.ui.cmb_tree_show.currentIndexChanged.connect(self.cmb_tree_show_index_changed)
        self.ui.tbl_data.selectionChanged = self.tbl_data_selection_changed
        self.ui.tbl_tree.selectionChanged = self.tbl_tree_selection_changed
        self.ui.tbl_tree.doubleClicked.connect(self.tbl_tree_double_click)
        self.ui.tbl_data.doubleClicked.connect(self.tbl_data_double_click)
        self.ui.tbl_details.doubleClicked.connect(self.tbl_details_double_click)
        self.ui.btn_event_details.clicked.connect(self.btn_event_details_click)
        self.ui.btn_charts.clicked.connect(self.btn_charts_click)
        self.closeEvent = self.save_win_size
        # Custom menus
        self.ui.tbl_data.customContextMenuRequested.connect(self.tbl_data_custom_context_menu)
        self.mnu_tbl_data_details.triggered.connect(self.tbl_data_double_click)
        self.mnu_tbl_data_graph.triggered.connect(self.tbl_data_custom_menu_graph)
        self.mnu_tbl_data_display_by_days.triggered.connect(self.mnu_tbl_data_display_by_days_trigger)
        self.mnu_tbl_data_display_by_weeks.triggered.connect(self.mnu_tbl_data_display_by_weeks_trigger)
        self.mnu_tbl_data_display_by_months.triggered.connect(self.mnu_tbl_data_display_by_months_trigger)
        self.mnu_tbl_data_display_by_years.triggered.connect(self.mnu_tbl_data_display_by_years_trigger)
        self.mnu_tbl_data_display_by_event_type.triggered.connect(self.btn_group_event_type_click)
        self.mnu_tbl_data_display_by_place.triggered.connect(self.btn_group_place_click)
        self.mnu_tbl_data_display_by_counterpart.triggered.connect(self.btn_group_partner_click)
        self.mnu_tbl_data_display_by_description.triggered.connect(self.btn_group_description_click)
        # Prepare data in table filter_data
        self.user.create_filter_table(self.events_id_list)
        # Populate widgets
        # populate_data and widgets_setup must be changed for every group value
        self.populate_data()
        
        self.show()
        self.exec_()
        self.log.write_log("Events report finished ... ")


    def btn_charts_click(self):
        chrt = ChartShow(self.active_user_id, self.active_user_name, self.active_lang)
        chrt.setup_gui()

    def tbl_data_custom_menu_graph(self):
        x = []
        y = []
        cur_col = self.ui.tbl_data.currentColumn()
        lbl_y = [
            "main_tbl_header_rashod_rsd",
            "main_tbl_header_rashod_rsd",
            "main_tbl_header_prihod_rsd",
            "main_tbl_header_rashod_rsd",
            "report_header_event_type_view_total_rsd",
            "main_tbl_header_prihod_eur",
            "main_tbl_header_rashod_eur",
            "report_header_event_type_view_total_eur",
            "report_header_event_type_view_total"]
        col_trans = [3,3,2,3,4,5,6,7,8]
        
        if self.active_group == "days":
            for i in self.active_events:
                x.append(i[1][:11])
                y.append(i[col_trans[cur_col]])
            l = [self.conn.lang("main_tbl_header_datum", self.active_lang), self.conn.lang(lbl_y[cur_col], self.active_lang)]
            graph_title = self.conn.lang("report_simple_graph_title", self.active_lang) + self.conn.lang(lbl_y[cur_col], self.active_lang)
            self._show_simple_graph(x, y, graph_title, l)
        elif self.active_group == "weeks":
            for i in self.active_events:
                x.append(i[1])
                y.append(i[col_trans[cur_col]])
            l = [self.conn.lang("report_filter_data_by_weeks", self.active_lang), self.conn.lang(lbl_y[cur_col], self.active_lang)]
            graph_title = self.conn.lang("report_simple_graph_title", self.active_lang) + self.conn.lang(lbl_y[cur_col], self.active_lang)
            self._show_simple_graph(x, y, graph_title, l)
        elif self.active_group == "months":
            for i in self.active_events:
                x.append(i[1])
                y.append(i[col_trans[cur_col]])
            l = [self.conn.lang("report_header_months_view", self.active_lang), self.conn.lang(lbl_y[cur_col], self.active_lang)]
            graph_title = self.conn.lang("report_simple_graph_title", self.active_lang) + self.conn.lang(lbl_y[cur_col], self.active_lang)
            self._show_simple_graph(x, y, graph_title, l)
        elif self.active_group == "years":
            for i in self.active_events:
                x.append(i[1])
                y.append(i[col_trans[cur_col]])
            l = [self.conn.lang("report_filter_data_by_years", self.active_lang), self.conn.lang(lbl_y[cur_col], self.active_lang)]
            graph_title = self.conn.lang("report_simple_graph_title", self.active_lang) + self.conn.lang(lbl_y[cur_col], self.active_lang)
            self._show_simple_graph(x, y, graph_title, l)
        elif self.active_group == "event_type":
            for i in self.active_events:
                x.append(i[1])
                y.append(i[col_trans[cur_col]])
            l = [self.conn.lang("report_header_event_type_view_event_type", self.active_lang), self.conn.lang(lbl_y[cur_col], self.active_lang)]
            graph_title = self.conn.lang("report_simple_graph_title", self.active_lang) + self.conn.lang(lbl_y[cur_col], self.active_lang)
            self._show_simple_graph(x, y, graph_title, l)
        elif self.active_group == "partner":
            for i in self.active_events:
                x.append(i[1])
                y.append(i[col_trans[cur_col]])
            l = [self.conn.lang("report_header_partner_view_partner", self.active_lang), self.conn.lang(lbl_y[cur_col], self.active_lang)]
            graph_title = self.conn.lang("report_simple_graph_title", self.active_lang) + self.conn.lang(lbl_y[cur_col], self.active_lang)
            self._show_simple_graph(x, y, graph_title, l)
        elif self.active_group == "place":
            for i in self.active_events:
                x.append(i[1])
                y.append(i[col_trans[cur_col]])
            l = [self.conn.lang("report_header_place_view_place", self.active_lang), self.conn.lang(lbl_y[cur_col], self.active_lang)]
            graph_title = self.conn.lang("report_simple_graph_title", self.active_lang) + self.conn.lang(lbl_y[cur_col], self.active_lang)
            self._show_simple_graph(x, y, graph_title, l)
        elif self.active_group == "description":
            for i in self.active_events:
                x.append(i[1])
                y.append(i[col_trans[cur_col]])
            l = [self.conn.lang("report_header_description_view_description", self.active_lang), self.conn.lang(lbl_y[cur_col], self.active_lang)]
            graph_title = self.conn.lang("report_simple_graph_title", self.active_lang) + self.conn.lang(lbl_y[cur_col], self.active_lang)
            self._show_simple_graph(x, y, graph_title, l)


            
    def _show_simple_graph(self, x, y, title, lbls):
        chart_dic = {}
        chart_dic["x_value"] = x
        chart_dic["y_value"] = y
        chart_dic["headline"] = title
        chart_dic["X"] = lbls[0]
        chart_dic["Y"] = lbls[1]
        chrt = ChartContainer(self.active_user_id, self.active_user_name, self.active_lang, chart_dic)
        chrt.setup_gui()

    def mnu_tbl_data_display_by_days_trigger(self):
        self.ui.rdb_days.setChecked(True)
        self.btn_group_date_click()

    def mnu_tbl_data_display_by_weeks_trigger(self):
        self.ui.rdb_weeks.setChecked(True)
        self.btn_group_date_click()

    def mnu_tbl_data_display_by_months_trigger(self):
        self.ui.rdb_months.setChecked(True)
        self.btn_group_date_click()

    def mnu_tbl_data_display_by_years_trigger(self):
        self.ui.rdb_years.setChecked(True)
        self.btn_group_date_click()

    def tbl_data_custom_context_menu(self, pos):
        self.mnu_tbl_data.exec_(self.ui.tbl_data.mapToGlobal(pos))

    def btn_event_details_click(self):
        if self.ui.tab_data.currentWidget() == self.ui.tab_table:
            if self.ui.tbl_data.currentRow() < 0:
                return
            self.tbl_data_double_click(0)
        elif self.ui.tab_data.currentWidget() == self.ui.tab_tree:
            if self.ui.tbl_tree.currentRow() < 0:
                return
            self.tbl_tree_double_click(0)
        elif self.ui.tab_data.currentWidget() == self.ui.tab_details:
            if self.ui.tbl_details.currentRow() < 0:
                return
            self.tbl_details_double_click()

    def tbl_details_double_click(self):
        if self.ui.tbl_details.currentRow() < 0:
            return
        ev = int(self.ui.tbl_details.item(self.ui.tbl_details.currentRow(), 0).text())
        ev_show = event_edit_cls.ViewEditEvent(self.active_user_id, self.active_user_name, self.active_lang, ev, open_for_view=True)
        ev_ids = []
        for i in self.active_events_details:
            ev_ids.append(i[0])
        ev_show.setup_gui(ev_ids)


    def view_event_details(self, ev_id=0, ev_ids=[]):
        res = event_edit_cls.ViewEditEvent(self.active_user_id, self.active_user_name, self.active_lang, ev_id, open_for_view=True)
        res.setup_gui(list_of_IDs_to_show=ev_ids)
    
    def tbl_data_selection_changed(self,x,y):
        row = self.ui.tbl_data.currentRow()
        txt = self.ui.tbl_data.item(row, 1).text()
        self.populate_details_table(txt)

    def tbl_tree_selection_changed(self,x,y):
        row = self.ui.tbl_tree.currentRow()
        txt = self.ui.tbl_tree.item(row, 0).text()
        self.populate_details_table(txt)

    def tbl_tree_double_click(self,x):
        if self.active_group != "":
            self.ui.tab_data.setCurrentWidget(self.ui.tab_details)

    def tbl_data_double_click(self,x):
        if self.active_group == "":
            ev_id = int(self.ui.tbl_data.item(self.ui.tbl_data.currentRow(), 0).text())
            self.view_event_details(ev_id, self.events_id_list)
        else:
            self.ui.tab_data.setCurrentWidget(self.ui.tab_details)

    def populate_details_table(self, item_in_col_1_text):
        # Clear data
        self.ui.tbl_details.clear()
        self.ui.tbl_details.setRowCount(0)
        self.ui.tbl_details.setColumnCount(0)
        # Get data for selected group
        if self.active_group == "":
            return
        idx = 0
        suc = False
        for i in self.active_events:
            if i[1] == item_in_col_1_text:
                suc = True
                break
            idx += 1
        if not suc:
            return
        self.active_events_details = self.user.get_filter_details_data(self.active_group, self.active_events, idx)
        # Populate table
        self.ui.tbl_details.setColumnCount(11)
        self.ui.tbl_details.setRowCount(len(self.active_events_details))
        for x in range(len(self.active_events_details)):
            for y in range(11):
                self.ui.tbl_details.setItem(x, y, QtWidgets.QTableWidgetItem(str(self.active_events_details[x][y])))
        # Set Headers
        h = []
        h.append("Hidden")
        h.append(self.conn.lang("main_tbl_header_datum", self.active_lang))
        h.append(self.conn.lang("main_tbl_header_prihod_rsd", self.active_lang))
        h.append(self.conn.lang("main_tbl_header_rashod_rsd", self.active_lang))
        h.append(self.conn.lang("main_tbl_header_prihod_eur", self.active_lang))
        h.append(self.conn.lang("main_tbl_header_rashod_eur", self.active_lang))
        h.append(self.conn.lang("main_tbl_header_vrsta_naziv", self.active_lang))
        h.append(self.conn.lang("main_tbl_header_partner", self.active_lang))
        h.append(self.conn.lang("main_tbl_header_mesto_naziv", self.active_lang))
        h.append(self.conn.lang("main_tbl_header_opis", self.active_lang))
        h.append(self.conn.lang("add_event_lbl_exchange", self.active_lang))
        self.ui.tbl_details.setHorizontalHeaderLabels(h)
        self.ui.tbl_details.setColumnHidden(0, True)
        self.ui.tbl_details.setSortingEnabled(True)
        # Set label as caption
        lbl_text = str(len(self.active_events_details)) + self.conn.lang("report_details_lbl_details_caption", self.active_lang)
        lbl_text = lbl_text + self.active_events[idx][1]
        self.ui.lbl_details_caption.setText(lbl_text)

    def cmb_tree_show_index_changed(self):
        self.populate_data_tree()

    def indent_char_changed(self):
        self.populate_data_tree()

    def indent_max_return_press(self):
        self.ui.sld_tree_indent.setMaximum(int(self.ui.lbl_tree_indent_max.text()))
        self.populate_data_tree()

    def sld_tree_indent_changed(self):
        self.ui.lbl_tree_indent_max.setText(str(self.ui.sld_tree_indent.value()))
        self.populate_data_tree()

    def load_win_size(self):
        x = self.conn.get_setting_data("report_x", getParametar=True, user_id=self.active_user_id)
        y = self.conn.get_setting_data("report_y", getParametar=True, user_id=self.active_user_id)
        w = self.conn.get_setting_data("report_w", getParametar=True, user_id=self.active_user_id)
        h = self.conn.get_setting_data("report_h", getParametar=True, user_id=self.active_user_id)
        self.resize(w,h)
        self.move(x,y)

    def save_win_size(self, event):
        # Save window geometry
        self.conn.set_setting_data("report_x","Report Window X pos", self.pos().x(), self.active_user_id)
        self.conn.set_setting_data("report_y","Report Window Y pos", self.pos().y(), self.active_user_id)
        self.conn.set_setting_data("report_w","Report Window WIDTH", self.width(), self.active_user_id)
        self.conn.set_setting_data("report_h","Report Window HEIGHT", self.height(), self.active_user_id)
        # Save columns width
        if self.active_group != "":
            for i in range(10):
                w = self.ui.tbl_data.columnWidth(i)
                a = "report_tbl_header_width" + str(i)
                self.conn.set_setting_data(a, "Sirina kolona u tabeli", w, self.active_user_id)
        # Save tree view indent data, combobox
        self.conn.set_setting_data("report_tree_indent_val", "Value for tree view indent", parametar=self.ui.sld_tree_indent.value(), user_id=self.active_user_id)
        self.conn.set_setting_data("report_tree_indent_max", "Max value for tree view indent", parametar=self.ui.sld_tree_indent.maximum(), user_id=self.active_user_id)
        self.conn.set_setting_data("report_tree_cmb_tree_show", "ComboBox", self.ui.cmb_tree_show.currentIndex(), self.active_user_id)
        self.conn.set_setting_data("report_tree_tbl_tree_col_width0", "Table column width", self.ui.tbl_tree.columnWidth(0), self.active_user_id)
        self.conn.set_setting_data("report_tree_tbl_tree_col_width1", "Table column width", self.ui.tbl_tree.columnWidth(1), self.active_user_id)
        self.conn.set_setting_data("report_tree_indent_char", self.ui.lbl_tree_indent_char.text(), 0, self.active_user_id)
        

    def btn_group_date_click(self):
        self.group_by_date()

    def group_by_date(self):
        if self.ui.rdb_days.isChecked():
            self.active_group = "days"
        elif self.ui.rdb_months.isChecked():
            self.active_group = "months"
        elif self.ui.rdb_weeks.isChecked():
            self.active_group = "weeks"
        elif self.ui.rdb_years.isChecked():
            self.active_group = "years"
        self.populate_data()

    def btn_group_event_type_click(self):
        self.active_group = "event_type"
        self.populate_data()

    def btn_group_partner_click(self):
        self.active_group = "partner"
        self.populate_data()

    def btn_group_place_click(self):
        self.active_group = "place"
        self.populate_data()

    def btn_group_description_click(self):
        self.active_group = "description"
        self.populate_data()

    def btn_reset_click(self):
        self.active_group = ""
        self.populate_data()
    
    def populate_data(self):
        if self.active_group == "":
            self.mnu_tbl_data_graph.setEnabled(False)
        else:
            self.mnu_tbl_data_graph.setEnabled(True)
        self.populate_data_table()
        self.populate_data_tree()
        self.ui.tbl_details.clear()
        self.ui.tbl_details.setRowCount(0)

    def populate_data_tree(self):
        # Clear table and set number of rows and columns
        self.ui.tbl_tree.clear()
        self.ui.tbl_tree.setRowCount(self.ui.tbl_data.rowCount())
        # Get value for min and max
        if self.active_group == "":
            rsd_i = [x[14] for x in self.active_events]
            rsd_o = [x[15] for x in self.active_events]
            rsd_t = [x[14]-x[15] for x in self.active_events]
            eur_i = [x[16] for x in self.active_events]
            eur_o = [x[17] for x in self.active_events]
            eur_t = [x[16]-x[17] for x in self.active_events]
            tot_t = [(x[16]-x[17])*x[22]+x[14]-x[15] for x in self.active_events]
        else:
            rsd_i = [x[2] for x in self.active_events]
            rsd_o = [x[3] for x in self.active_events]
            rsd_t = [x[4] for x in self.active_events]
            eur_i = [x[5] for x in self.active_events]
            eur_o = [x[6] for x in self.active_events]
            eur_t = [x[7] for x in self.active_events]
            tot_t = [x[8] for x in self.active_events]
        # Set increment step for each combobox value
        stp = {}
        stp[0] = (max(rsd_i) - min(rsd_i)) / self.ui.sld_tree_indent.value()
        if stp[0] == 0:
            stp[0] = max(rsd_i)
        stp[1] = (max(rsd_o) - min(rsd_o)) / self.ui.sld_tree_indent.value()
        if stp[1] == 0:
            stp[1] = max(rsd_o)
        stp[2] = (max(rsd_t) - min(rsd_t)) / self.ui.sld_tree_indent.value()
        if stp[2] == 0:
            stp[2] = max(rsd_t)
        stp[3] = (max(eur_i) - min(eur_i)) / self.ui.sld_tree_indent.value()
        if stp[3] == 0:
            stp[3] = max(eur_i)
        stp[4] = (max(eur_o) - min(eur_o)) / self.ui.sld_tree_indent.value()
        if stp[4] == 0:
            stp[4] = max(eur_o)
        stp[5] = (max(eur_t) - min(eur_t)) / self.ui.sld_tree_indent.value()
        if stp[5] == 0:
            stp[5] = max(eur_t)
        stp[6] = (max(tot_t) - min(tot_t)) / self.ui.sld_tree_indent.value()
        if stp[6] == 0:
            stp[6] = max(tot_t)
        cr_idx = self.ui.cmb_tree_show.currentIndex()
        step = int(stp[cr_idx])
        if step == 0:
            step = 1
        indent = self.ui.lbl_tree_indent_char.text()

        # Write data to table
        for i in range(self.ui.tbl_data.rowCount()):
            if self.active_group == "":
                txt0 = self.ui.tbl_data.item(i, 0).text()
                if cr_idx in [0,1]:
                    form_txt = indent * int(self.active_events[i][cr_idx + 14] / step)
                    form_txt = form_txt + str(self.active_events[i][cr_idx + 14])
                elif cr_idx in [3,4]:
                    form_txt = indent * int(self.active_events[i][cr_idx + 13] / step)
                    form_txt = form_txt + str(self.active_events[i][cr_idx + 13])
                elif cr_idx == 2:
                    form_txt = indent * int((self.active_events[i][14] - self.active_events[i][15]) / step)
                    form_txt = form_txt + str(self.active_events[i][14] - self.active_events[i][15])
                elif cr_idx == 5:
                    form_txt = indent * int((self.active_events[i][16] - self.active_events[i][17]) / step)
                    form_txt = form_txt + str(self.active_events[i][16] - self.active_events[i][17])
                elif cr_idx == 6:
                    aa = (self.active_events[i][14] - self.active_events[i][15]) + (self.active_events[i][16] - self.active_events[i][17]) * self.active_events[i][22]
                    form_txt = indent * int(aa / step)
                    form_txt = form_txt + str(aa)
            else:
                txt0 = self.ui.tbl_data.item(i, 1).text()
                form_txt = indent * int(self.active_events[i][cr_idx + 2] / step)
                form_txt = form_txt + str(self.active_events[i][cr_idx + 2])
            self.ui.tbl_tree.setItem(i, 0, QtWidgets.QTableWidgetItem(txt0))
            self.ui.tbl_tree.setItem(i, 1, QtWidgets.QTableWidgetItem(form_txt))
        header_label = []
        self.ui.tbl_tree.setHorizontalHeaderLabels([])
        header_label.append(self.conn.lang("report_tree_tbl_tree_header0", self.active_lang))
        hh = self.conn.lang("report_tree_tbl_tree_header1", self.active_lang)
        hh = hh + self.ui.lbl_tree_indent_char.text()
        header_label.append(hh)
        self.ui.tbl_tree.setHorizontalHeaderLabels(header_label)
        self.ui.tbl_tree.setSortingEnabled(True)
        
            
        


    def _setup_dialog_and_widgets(self):
        # Fill combo 'show' with data
        self.ui.cmb_tree_show.clear()
        self.ui.cmb_tree_show.addItem(self.conn.lang("report_header_income_rsd_sum", self.active_lang),2)
        self.ui.cmb_tree_show.addItem(self.conn.lang("report_header_outcome_rsd_sum", self.active_lang),3)
        self.ui.cmb_tree_show.addItem(self.conn.lang("report_header_event_type_view_total_rsd", self.active_lang),4)
        self.ui.cmb_tree_show.addItem(self.conn.lang("report_header_income_eur_sum", self.active_lang),5)
        self.ui.cmb_tree_show.addItem(self.conn.lang("report_header_outcome_eur_sum", self.active_lang),6)
        self.ui.cmb_tree_show.addItem(self.conn.lang("report_header_event_type_view_total_eur", self.active_lang),7)
        self.ui.cmb_tree_show.addItem(self.conn.lang("report_header_event_type_view_total", self.active_lang),8)
        # Load indent value and indent max, combobox
        self.ui.sld_tree_indent.setRange(1, self.conn.get_setting_data("report_tree_indent_max", getParametar=True, user_id=self.active_user_id))
        self.ui.sld_tree_indent.setValue(self.conn.get_setting_data("report_tree_indent_val", getParametar=True, user_id=self.active_user_id))
        self.ui.lbl_tree_indent_max.setText(str(self.ui.sld_tree_indent.value()))
        self.ui.cmb_tree_show.setCurrentIndex(self.conn.get_setting_data("report_tree_cmb_tree_show", getParametar=True, user_id=self.active_user_id))
        self.ui.tbl_tree.setColumnCount(2)
        self.ui.tbl_tree.setColumnWidth(0, self.conn.get_setting_data("report_tree_tbl_tree_col_width0", getParametar=True, user_id=self.active_user_id))
        self.ui.tbl_tree.setColumnWidth(1, self.conn.get_setting_data("report_tree_tbl_tree_col_width1", getParametar=True, user_id=self.active_user_id))
        self.ui.lbl_tree_indent_char.setText(self.conn.get_setting_data("report_tree_indent_char", user_id=self.active_user_id))
        # Set minumum window size and load user win size
        self.setMinimumSize(820, 300)
        self.load_win_size()
        # Setup custom context menus
        self.ui.tbl_data.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.tbl_tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.mnu_tbl_data = QtWidgets.QMenu(self.ui.tbl_data)
        self.mnu_tbl_data_details = QtWidgets.QAction(QtGui.QIcon("data/assets/edit.png"), self.conn.lang("report_btn_event_details", self.active_lang))
        self.mnu_tbl_data_graph = QtWidgets.QAction(QtGui.QIcon("data/assets/graph.png"), self.conn.lang("cmnu_report_tbl_data_graph", self.active_lang))
        self.mnu_tbl_data_display_by_days = QtWidgets.QAction(QtGui.QIcon("data/assets/view_day.png"), self.conn.lang("cmnu_report_tbl_data_display_by_days", self.active_lang))
        self.mnu_tbl_data_display_by_weeks = QtWidgets.QAction(QtGui.QIcon("data/assets/view_week.png"), self.conn.lang("cmnu_report_tbl_data_display_by_weeks", self.active_lang))
        self.mnu_tbl_data_display_by_months = QtWidgets.QAction(QtGui.QIcon("data/assets/view_month.png"), self.conn.lang("cmnu_report_tbl_data_display_by_months", self.active_lang))
        self.mnu_tbl_data_display_by_years = QtWidgets.QAction(QtGui.QIcon("data/assets/view_year.png"), self.conn.lang("cmnu_report_tbl_data_display_by_years", self.active_lang))
        self.mnu_tbl_data_display_by_event_type = QtWidgets.QAction(QtGui.QIcon("data/assets/main_add_event_type"), self.conn.lang("cmnu_report_tbl_data_display_by_event_type", self.active_lang))
        self.mnu_tbl_data_display_by_place = QtWidgets.QAction(QtGui.QIcon("data/assets/main_location.png"), self.conn.lang("cmnu_report_tbl_data_display_by_place", self.active_lang))
        self.mnu_tbl_data_display_by_counterpart = QtWidgets.QAction(QtGui.QIcon("data/assets/partner.png"), self.conn.lang("cmnu_report_tbl_data_display_by_counterpart", self.active_lang))
        self.mnu_tbl_data_display_by_description = QtWidgets.QAction(QtGui.QIcon("data/assets/description.png"), self.conn.lang("cmnu_report_tbl_data_display_by_description", self.active_lang))
        # Add actions to menu        
        self.mnu_tbl_data.addAction(self.mnu_tbl_data_details)
        self.mnu_tbl_data.addAction(self.mnu_tbl_data_graph)
        self.mnu_tbl_data.addSeparator()
        self.mnu_tbl_data.addAction(self.mnu_tbl_data_display_by_days)
        self.mnu_tbl_data.addAction(self.mnu_tbl_data_display_by_weeks)
        self.mnu_tbl_data.addAction(self.mnu_tbl_data_display_by_months)
        self.mnu_tbl_data.addAction(self.mnu_tbl_data_display_by_years)
        self.mnu_tbl_data.addSeparator()
        self.mnu_tbl_data.addAction(self.mnu_tbl_data_display_by_event_type)
        self.mnu_tbl_data.addAction(self.mnu_tbl_data_display_by_place)
        self.mnu_tbl_data.addAction(self.mnu_tbl_data_display_by_counterpart)
        self.mnu_tbl_data.addAction(self.mnu_tbl_data_display_by_description)
        # Disable graph if group is None
        if self.active_group == "":
            self.mnu_tbl_data_graph.setDisabled(True)

    def populate_data_table(self):
        # Set variables (for each group value diferent)
        if self.active_group == "":
            self.ui.tab_info.setVisible(False)
            col_range = (13,23)  # Visible columns
            col_center_left = []  # Columns indexes to align left
            col_center_right = []  # Columns indexes to align right
        elif self.active_group == "event_type":
            self.ui.tab_info.setVisible(True)
            col_range = (0,9)
            col_center_left = [1]
            col_center_right = [2,3,4,5,6,7,8]
        elif self.active_group == "partner":
            self.ui.tab_info.setVisible(True)
            col_range = (0,9)
            col_center_left = [1]
            col_center_right = [2,3,4,5,6,7,8]
        elif self.active_group == "place":
            self.ui.tab_info.setVisible(True)
            col_range = (0,9)
            col_center_left = [1]
            col_center_right = [2,3,4,5,6,7,8]
        elif self.active_group == "description":
            self.ui.tab_info.setVisible(True)
            col_range = (0,9)
            col_center_left = [1]
            col_center_right = [2,3,4,5,6,7,8]
        elif self.active_group == "days":
            self.ui.tab_info.setVisible(True)
            col_range = (0,9)
            col_center_left = [1]
            col_center_right = [2,3,4,5,6,7,8]
        elif self.active_group == "weeks":
            self.ui.tab_info.setVisible(True)
            col_range = (0,9)
            col_center_left = [1]
            col_center_right = [2,3,4,5,6,7,8]
        elif self.active_group == "months":
            self.ui.tab_info.setVisible(True)
            col_range = (0,9)
            col_center_left = [1]
            col_center_right = [2,3,4,5,6,7,8]
        elif self.active_group == "years":
            self.ui.tab_info.setVisible(True)
            col_range = (0,9)
            col_center_left = []
            col_center_right = [2,3,4,5,6,7,8]
        # Clear list and get data
        self.active_events.clear()
        self.ui.tbl_data.clear()
        self.ui.tbl_data.show()
        self.ui.tbl_data.setRowCount(0)
        self.ui.tbl_data.setColumnCount(0)
        self.ui.tbl_data.setHorizontalHeaderLabels([])
        self.active_events = self.user.get_filter_data(self.active_group)
        # Setup widgets (number of rows, cols, etc...)
        self.widgets_setup_table()
        # Load column width if group is not ""
        if self.active_group != "":
            for i in range(10):
                prmt = "report_tbl_header_width" + str(i)
                w = self.conn.get_setting_data(prmt, getParametar=True, user_id=self.active_user_id)
                self.ui.tbl_data.setColumnWidth(i, w)
        # Populate widgets with data 
        for x in range(len(self.active_events)):
            for y in range(col_range[1]):
                itm = QtWidgets.QTableWidgetItem(str(self.active_events[x][y]))
                if y in col_center_left:
                    itm.setTextAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
                elif y in col_center_right:
                    itm.setTextAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
                else:
                    itm.setTextAlignment(QtCore.Qt.AlignCenter|QtCore.Qt.AlignVCenter)
                self.ui.tbl_data.setItem(x, y, itm)
        # Hide first 13 columns for group = ""
        for i in range(col_range[0]):
            self.ui.tbl_data.setColumnHidden(i, True)
        # Update label number of records
        lbl_text = self.conn.lang("main_event_browser", self.active_lang)
        lbl_text = lbl_text + " " + str(len(self.active_events))
        self.ui.lbl_table_rows.setText(lbl_text)
        self.update_info_tab()
        self.ui.tbl_data.setSortingEnabled(True)

    def update_info_tab(self):
        if not self.ui.tab_info.isVisible():
            return
        rsd_i = [x[2] for x in self.active_events]
        rsd_o = [x[3] for x in self.active_events]
        eur_i = [x[5] for x in self.active_events]
        eur_o = [x[6] for x in self.active_events]

        a = min(rsd_i)
        rsd_i_min = self.active_events[rsd_i.index(a)][1] + " = " + str(a)
        a = max(rsd_i)
        rsd_i_max = self.active_events[rsd_i.index(a)][1] + " = " + str(a)
        a = min(rsd_o)
        rsd_o_min = self.active_events[rsd_o.index(a)][1] + " = " + str(a)
        a = max(rsd_o)
        rsd_o_max = self.active_events[rsd_o.index(a)][1] + " = " + str(a)

        a = min(eur_i)
        eur_i_min = self.active_events[eur_i.index(a)][1] + " = " + str(a)
        a = max(eur_i)
        eur_i_max = self.active_events[eur_i.index(a)][1] + " = " + str(a)
        a = min(eur_o)
        eur_o_min = self.active_events[eur_o.index(a)][1] + " = " + str(a)
        a = max(eur_o)
        eur_o_max = self.active_events[eur_o.index(a)][1] + " = " + str(a)

        self.ui.lbl_info_min_income_rsd_data.setText(rsd_i_min)
        self.ui.lbl_info_max_income_rsd_data.setText(rsd_i_max)
        self.ui.lbl_info_min_outcome_rsd_data.setText(rsd_o_min)
        self.ui.lbl_info_max_outcome_rsd_data.setText(rsd_o_max)
        self.ui.lbl_info_min_income_eur_data.setText(eur_i_min)
        self.ui.lbl_info_max_income_eur_data.setText(eur_i_max)
        self.ui.lbl_info_min_outcome_eur_data.setText(eur_o_min)
        self.ui.lbl_info_max_outcome_eur_data.setText(eur_o_max)


    def widgets_setup_table(self):
        # Table (for each group value diferent)
        header_data = []
        row_c = len(self.active_events)
        if self.active_group == "":
            # Append 12 headers for hidden columns
            for i in range(13):
                header_data.append("Hidden")
            col_c = 23
            header_data.append(self.conn.lang("main_tbl_header_datum", self.active_lang))
            header_data.append(self.conn.lang("main_tbl_header_prihod_rsd", self.active_lang))
            header_data.append(self.conn.lang("main_tbl_header_rashod_rsd", self.active_lang))
            header_data.append(self.conn.lang("main_tbl_header_prihod_eur", self.active_lang))
            header_data.append(self.conn.lang("main_tbl_header_rashod_eur", self.active_lang))
            header_data.append(self.conn.lang("main_tbl_header_vrsta_naziv", self.active_lang))
            header_data.append(self.conn.lang("add_event_lbl_partner", self.active_lang))
            header_data.append(self.conn.lang("main_tbl_header_mesto_naziv", self.active_lang))
            header_data.append(self.conn.lang("main_tbl_header_opis", self.active_lang))
            header_data.append(self.conn.lang("add_event_lbl_exchange", self.active_lang))
        elif self.active_group == "event_type":
            col_c = 9
            header_data.append(self.conn.lang("report_header_event_type_view_items_no", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_event_type", self.active_lang))
            header_data.append(self.conn.lang("report_header_income_rsd_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_outcome_rsd_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total_rsd", self.active_lang))
            header_data.append(self.conn.lang("report_header_income_eur_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_outcome_eur_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total_eur", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total", self.active_lang))
        elif self.active_group == "partner":
            col_c = 9
            header_data.append(self.conn.lang("report_header_event_type_view_items_no", self.active_lang))
            header_data.append(self.conn.lang("report_header_partner_view_partner", self.active_lang))
            header_data.append(self.conn.lang("report_header_income_rsd_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_outcome_rsd_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total_rsd", self.active_lang))
            header_data.append(self.conn.lang("report_header_income_eur_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_outcome_eur_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total_eur", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total", self.active_lang))
        elif self.active_group == "place":
            col_c = 9
            header_data.append(self.conn.lang("report_header_event_type_view_items_no", self.active_lang))
            header_data.append(self.conn.lang("report_header_place_view_place", self.active_lang))
            header_data.append(self.conn.lang("report_header_income_rsd_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_outcome_rsd_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total_rsd", self.active_lang))
            header_data.append(self.conn.lang("report_header_income_eur_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_outcome_eur_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total_eur", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total", self.active_lang))
        elif self.active_group == "description":
            col_c = 9
            header_data.append(self.conn.lang("report_header_event_type_view_items_no", self.active_lang))
            header_data.append(self.conn.lang("report_header_description_view_description", self.active_lang))
            header_data.append(self.conn.lang("report_header_income_rsd_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_outcome_rsd_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total_rsd", self.active_lang))
            header_data.append(self.conn.lang("report_header_income_eur_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_outcome_eur_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total_eur", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total", self.active_lang))
        elif self.active_group == "days":
            col_c = 9
            header_data.append(self.conn.lang("report_header_event_type_view_items_no", self.active_lang))
            header_data.append(self.conn.lang("main_tbl_header_datum", self.active_lang))
            header_data.append(self.conn.lang("report_header_income_rsd_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_outcome_rsd_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total_rsd", self.active_lang))
            header_data.append(self.conn.lang("report_header_income_eur_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_outcome_eur_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total_eur", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total", self.active_lang))
        elif self.active_group == "weeks":
            col_c = 9
            header_data.append(self.conn.lang("report_header_event_type_view_items_no", self.active_lang))
            header_data.append(self.conn.lang("report_header_weeks_view", self.active_lang))
            header_data.append(self.conn.lang("report_header_income_rsd_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_outcome_rsd_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total_rsd", self.active_lang))
            header_data.append(self.conn.lang("report_header_income_eur_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_outcome_eur_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total_eur", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total", self.active_lang))
        elif self.active_group == "months":
            col_c = 9
            header_data.append(self.conn.lang("report_header_event_type_view_items_no", self.active_lang))
            header_data.append(self.conn.lang("report_header_months_view", self.active_lang))
            header_data.append(self.conn.lang("report_header_income_rsd_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_outcome_rsd_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total_rsd", self.active_lang))
            header_data.append(self.conn.lang("report_header_income_eur_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_outcome_eur_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total_eur", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total", self.active_lang))
        elif self.active_group == "years":
            col_c = 9
            header_data.append(self.conn.lang("report_header_event_type_view_items_no", self.active_lang))
            header_data.append(self.conn.lang("report_header_years_view", self.active_lang))
            header_data.append(self.conn.lang("report_header_income_rsd_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_outcome_rsd_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total_rsd", self.active_lang))
            header_data.append(self.conn.lang("report_header_income_eur_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_outcome_eur_sum", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total_eur", self.active_lang))
            header_data.append(self.conn.lang("report_header_event_type_view_total", self.active_lang))
                            
        self.ui.tbl_data.setRowCount(row_c)
        self.ui.tbl_data.setColumnCount(col_c)
        self.ui.tbl_data.setHorizontalHeaderLabels(header_data)


    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        # Resize widgets with window
        w = self.width()
        h = self.height()
        self.ui.frm_options.resize(w, 150)
        self.ui.tab_data.resize(w, h - 150)
        self.ui.tbl_data.resize(w-8, h - 220)
        self.ui.tbl_tree.resize(w-8, h - 230)
        self.ui.tbl_details.resize(w-8, h - 225)
        self.ui.lbl_details_caption.resize(w, 27)

        return super().resizeEvent(a0)

    def retranslateUi(self):
        self.setWindowTitle(self.conn.lang("report_win_title", self.active_lang))
        self.ui.btn_group_date.setText(self.conn.lang("report_btn_group_date", self.active_lang))
        self.ui.rdb_days.setText(self.conn.lang("report_rdb_days", self.active_lang))
        self.ui.rdb_weeks.setText(self.conn.lang("report_rdb_weeks", self.active_lang))
        self.ui.rdb_months.setText(self.conn.lang("report_rdb_months", self.active_lang))
        self.ui.rdb_years.setText(self.conn.lang("report_rdb_years", self.active_lang))
        self.ui.btn_group_event_type.setText(self.conn.lang("report_btn_event_type", self.active_lang))
        self.ui.btn_group_place.setText(self.conn.lang("report_btn_place", self.active_lang))
        self.ui.btn_group_partner.setText(self.conn.lang("report_btn_partner", self.active_lang))
        self.ui.btn_group_description.setText(self.conn.lang("report_btn_description", self.active_lang))
        self.ui.lbl_group_by.setText(self.conn.lang("report_lbl_group_by", self.active_lang))
        self.ui.btn_event_details.setText(self.conn.lang("report_btn_event_details", self.active_lang))
        self.ui.lbl_table_rows.setText(self.conn.lang("report_lbl_table_rows", self.active_lang))
        self.ui.btn_reset.setText(self.conn.lang("report_btn_reset", self.active_lang))
        self.ui.tab_data.setTabText(self.ui.tab_data.indexOf(self.ui.tab_table), self.conn.lang("report_tab_table_title", self.active_lang))
        self.ui.tab_data.setTabText(self.ui.tab_data.indexOf(self.ui.tab_tree), self.conn.lang("report_tab_tree_title", self.active_lang))
        self.ui.tab_data.setTabText(self.ui.tab_data.indexOf(self.ui.tab_details), self.conn.lang("report_tab_detail_title", self.active_lang))
        self.ui.tab_data.setTabToolTip(self.ui.tab_data.indexOf(self.ui.tab_table), self.conn.lang("report_tab_table_title_tt", self.active_lang))
        self.ui.tab_data.setTabToolTip(self.ui.tab_data.indexOf(self.ui.tab_tree), self.conn.lang("report_tab_tree_title_tt", self.active_lang))
        self.ui.tab_data.setTabToolTip(self.ui.tab_data.indexOf(self.ui.tab_details), self.conn.lang("report_tab_detail_title_tt", self.active_lang))
        self.ui.lbl_info_min_max_income_rsd.setText(self.conn.lang("report_info_tab_min_max_income", self.active_lang))
        self.ui.lbl_info_min_max_income_eur.setText(self.conn.lang("report_info_tab_min_max_income", self.active_lang))
        self.ui.lbl_info_min_max_outcome_rsd.setText(self.conn.lang("report_info_tab_min_max_outcome", self.active_lang))
        self.ui.lbl_info_min_max_outcome_eur.setText(self.conn.lang("report_info_tab_min_max_outcome", self.active_lang))
        self.ui.tab_info.setTabText(self.ui.tab_info.indexOf(self.ui.info_tab_rsd), "RSD")
        self.ui.tab_info.setTabText(self.ui.tab_info.indexOf(self.ui.info_tab_eur), "EUR")
        self.ui.lbl_tree_show.setText(self.conn.lang("report_tree_lbl_show", self.active_lang))
        self.ui.lbl_tree_indent.setText(self.conn.lang("report_tree_lbl_indent", self.active_lang))
        self.ui.lbl_details_caption.setText(self.conn.lang("report_details_lbl_details_caption", self.active_lang))
        self.ui.lbl_tree_indent_char_caption.setText(self.conn.lang("report_tree_lbl_tree_indent_char_caption", self.active_lang))
        self.ui.btn_charts.setText(self.conn.lang("report_btn_chart_setting", self.active_lang))


class ChartShow(QtWidgets.QDialog):
    def __init__(self, user_id, user_name, language, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create enviroment variables
        self.active_user_id = user_id
        self.active_user_name = user_name
        self.active_lang = language
        self.chart_list = []
        self.conn = connection.ConnStart()
        self.log = log_cls.LogData()
        self.ui = chart_show_ui.Ui_Dialog()
        self.chart = connection.Chart(self.active_user_id)

    def setup_gui(self):
        # Setup GUI
        self.ui.setupUi(self)
        self.retranslateUi()
        self.setFixedSize(590, 345)
        self.setWindowFlag(QtCore.Qt.Dialog)
        self.setWindowModality(Qt.ApplicationModal)
        # Setup context menu for lst_charts
        self.setup_context_mnu()
        # Connect events with slots
        self.ui.btn_add.clicked.connect(self.btn_add_click)
        self.ui.lst_charts.currentChanged = self.lst_charts_current_changed
        self.ui.lst_charts.customContextMenuRequested.connect(self.lst_charts_show_menu)
        self.action_rename.triggered.connect(self.action_rename_triggered)
        self.ui.btn_rename.clicked.connect(self.action_rename_triggered)
        self.action_delete.triggered.connect(self.action_delete_triggered)
        self.ui.btn_delete.clicked.connect(self.action_delete_triggered)
        self.action_edit.triggered.connect(self.action_edit_triggered)
        self.ui.btn_edit.clicked.connect(self.action_edit_triggered)
        self.ui.btn_show.clicked.connect(self.btn_show_click)
        self.ui.lst_charts.doubleClicked.connect(self.btn_show_click)

        # Populate widgets
        self.populate_widgets()

        self.show()
        self.exec_()

    def btn_show_click(self):
        c_id = self.ui.lst_charts.currentItem().data(QtCore.Qt.UserRole)
        chart_dict = self.chart.get_chart_data(c_id)
        chrt = ChartContainer(self.active_user_id, self.active_user_name, self.active_lang, chart_dict)
        chrt.setup_gui()

    def action_edit_triggered(self):
        ad = ChartEdit(self.active_user_id, self.active_user_name, self.active_lang)
        ad.setup_gui(edit_mode=self.ui.lst_charts.currentItem().text())
        self.populate_widgets(self.ui.lst_charts.currentRow())

    def action_rename_triggered(self):
        txt = self.ui.lst_charts.currentItem().text()
        msg_title = self.conn.lang("chart_show_rename_msg_title", self.active_lang)
        msg_text = self.conn.lang("chart_show_rename_msg_text", self.active_lang)
        result, ok_pressed = QtWidgets.QInputDialog.getText(self, msg_title, msg_text)
        if ok_pressed and result !="":
            if len(self.chart.get_charts_all(chart_name=result)) == 0:
                self.chart.set_chart_name(self.ui.lst_charts.currentItem().data(QtCore.Qt.UserRole), result)
                c_lst = self.ui.lst_charts.currentRow()
                self.populate_widgets(c_lst)
            else:
                msg_title = self.conn.lang("chart_show_win_title", self.active_lang)
                msg_text = self.conn.lang("chart_edit_btn_save_exists_msg_text", self.active_lang)
                msg_text = msg_text.replace("*", result)
                a = QtWidgets.QMessageBox.information(self, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
                return

    def action_delete_triggered(self):
        msg_title = self.conn.lang("btn_delete", self.active_lang)
        msg_text = self.conn.lang("chart_show_delete_question_msg_text", self.active_lang)
        msg_text = msg_text.replace("*", self.ui.lst_charts.currentItem().text())
        result = QtWidgets.QMessageBox.question(self, msg_title, msg_text, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if result == QtWidgets.QMessageBox.Yes:
            c_id = self.ui.lst_charts.currentItem().data(QtCore.Qt.UserRole)
            self.chart.delete_chart_and_data(c_id)
        self.populate_widgets()

    def lst_charts_show_menu(self, pos):
        self.mnu_charts.exec_(self.ui.lst_charts.mapToGlobal(pos))

    def setup_context_mnu(self):
        self.mnu_charts = QtWidgets.QMenu(self.ui.lst_charts)
        self.action_edit = QtWidgets.QAction(self.conn.lang("btn_edit", self.active_lang))
        self.action_rename = QtWidgets.QAction(self.conn.lang("btn_rename", self.active_lang))
        self.action_delete = QtWidgets.QAction(self.conn.lang("btn_delete", self.active_lang))
        self.mnu_charts.addAction(self.action_edit)
        self.mnu_charts.addAction(self.action_rename)
        self.mnu_charts.addAction(self.action_delete)
        self.ui.lst_charts.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

    def lst_charts_current_changed(self, x, y):
        if self.ui.lst_charts.currentItem() != None:
            self.ui.btn_edit.setEnabled(True)
            self.ui.btn_rename.setEnabled(True)
            self.ui.btn_delete.setEnabled(True)
            self.ui.btn_show.setEnabled(True)
            for i in self.chart_list:
                if i[0] == self.ui.lst_charts.currentItem().data(QtCore.Qt.UserRole):
                    self.ui.lbl_description.setText(i[2])

    def populate_widgets(self, current_row=0):
        self.chart_list = self.chart.get_charts_all()
        self.ui.lst_charts.clear()
        for i in self.chart_list:
            item = QtWidgets.QListWidgetItem(i[1])
            item.setData(QtCore.Qt.UserRole, i[0])
            self.ui.lst_charts.addItem(item)
        if current_row < len(self.chart_list):
            self.ui.lst_charts.setCurrentRow(current_row)
        if len(self.chart_list) > 0:
            self.ui.btn_edit.setEnabled(True)
            self.ui.btn_rename.setEnabled(True)
            self.ui.btn_delete.setEnabled(True)
            self.ui.btn_show.setEnabled(True)
        else:
            self.ui.btn_edit.setEnabled(False)
            self.ui.btn_rename.setEnabled(False)
            self.ui.btn_delete.setEnabled(False)
            self.ui.btn_show.setEnabled(False)

    def btn_add_click(self):
        ad = ChartEdit(self.active_user_id, self.active_user_name, self.active_lang)
        ad.setup_gui()
        self.populate_widgets()

    def retranslateUi(self):
        self.setWindowTitle(self.conn.lang("chart_show_win_title", self.active_lang))
        self.ui.lbl_saved_charts.setText(self.conn.lang("chart_show_lbl_saved_charts", self.active_lang))
        self.ui.btn_show.setText(self.conn.lang("chart_show_btn_show", self.active_lang))
        self.ui.btn_delete.setText(self.conn.lang("btn_delete", self.active_lang))
        self.ui.btn_rename.setText(self.conn.lang("btn_rename", self.active_lang))
        self.ui.btn_add.setText(self.conn.lang("chart_show_btn_add", self.active_lang))
        self.ui.btn_edit.setText(self.conn.lang("btn_edit", self.active_lang))
        self.ui.lbl_description.setText(self.conn.lang("chart_show_lbl_description", self.active_lang))
        self.ui.lbl_description.setText("")


class ChartEdit(QtWidgets.QDialog):
    def __init__(self, user_id, user_name, language, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create enviroment variables
        self.active_user_id = user_id
        self.active_user_name = user_name
        self.active_lang = language

        self.filter_event_type_btn_state = False
        self.filter_partner_btn_state = False
        self.filter_location_btn_state = False

        self.conn = connection.ConnStart()
        self.user = connection.User(self.active_user_id)
        self.chart = connection.Chart(self.active_user_id)
        self.log = log_cls.LogData()
        self.ui = chart_edit_ui.Ui_Dialog()
        # Create lists of event_types, partners and location
        # col0 = visible, col1 = checked state, col2 = Name, col3 = ID
        self.event_type_list = []
        self.partners_list = []
        self.locations_list = []
        # Fill lists with data
        self._fill_lists_for_list_widgets()


    def setup_gui(self, edit_mode=""):
        self.edit_mode = edit_mode  # Name of chart to edit
        # Setup GUI
        self.ui.setupUi(self)
        self.retranslateUi()
        self.setFixedSize(1200, 640)
        self.setWindowFlag(QtCore.Qt.Dialog)
        self.setWindowModality(Qt.ApplicationModal)
        self.ui.txt_y_axis.setAlignment(QtCore.Qt.AlignCenter)
        self.ui.txt_headline.setAlignment(QtCore.Qt.AlignCenter)
        self.ui.txt_x_axis.setAlignment(QtCore.Qt.AlignCenter)
        # Fill widgets with general data
        self.fill_widgets_with_general_data()
        # Setup enabled/disabled widgets
        self.setup_widgets_status()
        self.rdb_charts_toggled()
        # Connect events with slots
        # Event type widgets
        self.ui.chk_event_type.stateChanged.connect(self._setup_event_type_status)
        self.ui.btn_event_type_select_all.clicked.connect(self.btn_event_type_select_all_click)
        self.ui.btn_event_type_clear_all.clicked.connect(self.btn_event_type_clear_all_click)
        self.ui.lst_event_type.itemChanged.connect(self.lst_event_type_changed)
        self.ui.txt_event_type_filter.textChanged.connect(self.txt_event_type_filter_text_changed)
        self.ui.txt_event_type_filter.returnPressed.connect(self.btn_event_type_filter_apply_click)
        self.ui.btn_event_type_filter_apply.clicked.connect(self.btn_event_type_filter_apply_click)
        # Partner widgets
        self.ui.chk_partner.stateChanged.connect(self._setup_partner_status)
        self.ui.btn_partner_select_all.clicked.connect(self.btn_partner_select_all_click)
        self.ui.btn_partner_clear_all.clicked.connect(self.btn_partner_clear_all_click)
        self.ui.lst_partner.itemChanged.connect(self.lst_partner_changed)
        self.ui.txt_partner_filter.textChanged.connect(self.txt_partner_filter_text_changed)
        self.ui.txt_partner_filter.returnPressed.connect(self.btn_partner_filter_apply_click)
        self.ui.btn_partner_filter_apply.clicked.connect(self.btn_partner_filter_apply_click)
        # Location widgets
        self.ui.chk_location.stateChanged.connect(self._setup_location_status)
        self.ui.btn_location_select_all.clicked.connect(self.btn_location_select_all_click)
        self.ui.btn_location_clear_all.clicked.connect(self.btn_location_clear_all_click)
        self.ui.lst_location.itemChanged.connect(self.lst_location_changed)
        self.ui.txt_location_filter.textChanged.connect(self.txt_location_filter_text_changed)
        self.ui.txt_location_filter.returnPressed.connect(self.btn_location_filter_apply_click)
        self.ui.btn_location_filter_apply.clicked.connect(self.btn_location_filter_apply_click)
        # Radio button (Group by) events
        self.ui.rdb_dates.toggled.connect(self.rdb_group_by_toggled)
        self.ui.rdb_weeks.toggled.connect(self.rdb_group_by_toggled)
        self.ui.rdb_months.toggled.connect(self.rdb_group_by_toggled)
        self.ui.rdb_years.toggled.connect(self.rdb_group_by_toggled)
        # Other events
        self.ui.btn_headline_font.clicked.connect(self.btn_headline_font_click)
        self.ui.btn_headline_color.clicked.connect(self.btn_headline_color_click)
        self.ui.btn_x_axis_font.clicked.connect(self.btn__x_axis_font_click)
        self.ui.btn_x_axis_color.clicked.connect(self.btn__x_axis_color_click)
        self.ui.btn_y_axis_font.clicked.connect(self.btn__y_axis_font_click)
        self.ui.btn_y_axis_color.clicked.connect(self.btn__y_axis_color_click)
        self.ui.rdb_bars.toggled.connect(self.rdb_charts_toggled)
        self.ui.rdb_lines.toggled.connect(self.rdb_charts_toggled)
        self.ui.rdb_pies.toggled.connect(self.rdb_charts_toggled)
        self.ui.btn_chart_color.clicked.connect(self.btn_chart_color_click)
        self.ui.cmb_y_axis.currentTextChanged.connect(self.cmb_y_axis_text_changed)
        self.ui.btn_cancel.clicked.connect(self.btn_cancel_click)
        self.ui.btn_save.clicked.connect(self.btn_save_click)
        self.ui.btn_preview.clicked.connect(self.btn_preview_click)
        # Load data if edit_mode is <> ""
        if self.edit_mode != "":
            self.load_chart()
        self.show()
        self.exec_()

    def btn_preview_click(self):
        chart_dict = self.create_chart_dictionary()
        chrt = ChartContainer(self.active_user_id, self.active_user_name, self.active_lang, chart_dict)
        chrt.setup_gui()

    def load_chart(self):
        # Get data
        result = self.chart.get_charts_all(chart_name=self.edit_mode)
        ch_id = result[0][0]
        c = self.chart.get_chart_data(ch_id)
        # Load data to widgets
        self.ui.txt_name.setText(c["name"])
        self.ui.txt_description.setText(c["description"])
        if c["event_type"] == "all":
            self.ui.chk_event_type.setChecked(False)
        else:
            self.ui.chk_event_type.setChecked(True)
            for i in range(len(self.event_type_list)):
                if self.event_type_list[i][3] in c["event_type"]:
                    self.event_type_list[i][1] = 1
                    self.ui.lst_event_type.item(i).setCheckState(QtCore.Qt.Checked)
                else:
                    self.event_type_list[i][1] = 0
                    self.ui.lst_event_type.item(i).setCheckState(QtCore.Qt.Unchecked)
        if c["partner"] == "all":
            self.ui.chk_partner.setChecked(False)
        else:
            self.ui.chk_partner.setChecked(True)
            for i in range(len(self.partners_list)):
                if self.partners_list[i][2] in c["partner"]:
                    self.partners_list[i][1] = 1
                    self.ui.lst_partner.item(i).setCheckState(QtCore.Qt.Checked)
                else:
                    self.partners_list[i][1] = 0
                    self.ui.lst_partner.item(i).setCheckState(QtCore.Qt.Unchecked)
        if c["location"] == "all":
            self.ui.chk_location.setChecked(False)
        else:
            self.ui.chk_location.setChecked(True)
            for i in range(len(self.locations_list)):
                if self.locations_list[i][3] in c["location"]:
                    self.locations_list[i][1] = 1
                    self.ui.lst_location.item(i).setCheckState(QtCore.Qt.Checked)
                else:
                    self.locations_list[i][1] = 0
                    self.ui.lst_location.item(i).setCheckState(QtCore.Qt.Unchecked)
        if c["group"] == "datum":
            self.ui.rdb_dates.setChecked(True)
        elif c["group"] == "nedelja":
            self.ui.rdb_weeks.setChecked(True)
        elif c["group"] == "mesec_broj":
            self.ui.rdb_months.setChecked(True)
        elif c["group"] == "godina":
            self.ui.rdb_years.setChecked(True)
        self.ui.txt_headline.setText(c["headline"])
        font = self.ui.txt_headline.font()
        font.setFamily(c["headline_font"][0])
        font.setPointSize(c["headline_font"][1])
        font.setBold(c["headline_font"][2])
        font.setItalic(c["headline_font"][3])
        font.setUnderline(c["headline_font"][4])
        font.setStrikeOut(c["headline_font"][5])
        self.ui.txt_headline.setFont(font)
        color = c["headline_color"]
        self.ui.txt_headline.setStyleSheet(f"color: {color} ;")
        self.ui.txt_x_axis.setText(c["X"])
        font = self.ui.txt_x_axis.font()
        font.setFamily(c["X_font"][0])
        font.setPointSize(c["X_font"][1])
        font.setBold(c["X_font"][2])
        font.setItalic(c["X_font"][3])
        font.setUnderline(c["X_font"][4])
        font.setStrikeOut(c["X_font"][5])
        self.ui.txt_x_axis.setFont(font)
        color = c["X_color"]
        self.ui.txt_x_axis.setStyleSheet(f"color: {color} ;")
        self.ui.txt_y_axis.setText(c["Y"])
        font = self.ui.txt_y_axis.font()
        font.setFamily(c["Y_font"][0])
        font.setPointSize(c["Y_font"][1])
        font.setBold(c["Y_font"][2])
        font.setItalic(c["Y_font"][3])
        font.setUnderline(c["Y_font"][4])
        font.setStrikeOut(c["Y_font"][5])
        self.ui.txt_y_axis.setFont(font)
        color = c["Y_color"]
        self.ui.txt_y_axis.setStyleSheet(f"color: {color} ;")
        self.ui.cmb_y_axis.setCurrentIndex(c["Y_type"][1])
        if c["g_type"] == "bar":
            self.ui.rdb_bars.setChecked(True)
        elif c["g_type"] == "line":
            self.ui.rdb_lines.setChecked(True)
        elif c["g_type"] == "pie":
            self.ui.rdb_pies.setChecked(True)
        color = c["g_color"]
        self.ui.lbl_graph_color.setStyleSheet(f"background-color: {color} ;")
        for i in range(self.ui.cmb_chart_marker.count()):
            txt = self.ui.cmb_chart_marker.itemText(i)
            txt = txt[1:(len(c["g_marker"])+1)]
            if txt == c["g_marker"]:
                self.ui.cmb_chart_marker.setCurrentIndex(i)
                break
        for i in range(self.ui.cmb_chart_pattern.count()):
            txt = self.ui.cmb_chart_pattern.itemText(i)
            txt = txt[1:(len(c["g_pattern"])+1)]
            if txt == c["g_pattern"]:
                self.ui.cmb_chart_pattern.setCurrentIndex(i)
                break
        self.setup_widgets_status()

    def create_chart_dictionary(self):
        """All data is stored in dictionary.
        Event type is stored as "all" or as list of ID-s
        Partners (Counterpart) are stored as "all" or as list of names
        Locations are stored as "all" or as list of ID-s
        Headline, X and Y axes has their name, font and color
        Fonts are stored as list (name, size, bold, italic, underline, strikeout
        Colors are stored with HEX values
        """
        # Count selected data
        items_event_type = 0
        items_partner = 0
        items_location = 0
        for i in self.event_type_list:
            if i[1] == 1:
                items_event_type += 1
        for i in self.partners_list:
            if i[1] == 1:
                items_partner += 1
        for i in self.locations_list:
            if i[1] == 1:
                items_location += 1
        # Create chart dictionary
        # Add general info
        c = {}
        c["name"] = self.ui.txt_name.text()
        c["description"] = self.ui.txt_description.toPlainText()
        # Add data to show
        if items_event_type == len(self.event_type_list) or not self.ui.chk_event_type.isChecked():
            c["event_type"] = "all"
        else:
            a = []
            for i in self.event_type_list:
                if i[1] == 1:
                    a.append(i[3])
            c["event_type"] = a
        if items_partner == len(self.partners_list) or not self.ui.chk_partner.isChecked():
            c["partner"] = "all"
        else:
            a = []
            for i in self.partners_list:
                if i[1] == 1:
                    a.append(i[2])
            c["partner"] = a
        if items_location == len(self.locations_list) or not self.ui.chk_location.isChecked():
            c["location"] = "all"
        else:
            a = []
            for i in self.locations_list:
                if i[1] == 1:
                    a.append(i[3])
            c["location"] = a
        # Add group by
        if self.ui.rdb_dates.isChecked():
            c["group"] = "datum"
        elif self.ui.rdb_weeks.isChecked():
            c["group"] = "nedelja"
        elif self.ui.rdb_months.isChecked():
            c["group"] = "mesec_broj"
        elif self.ui.rdb_years.isChecked():
            c["group"] = "godina"
        # Add headline
        c["headline"] = self.ui.txt_headline.toPlainText()
        a = []
        font = self.ui.txt_headline.font()
        a.append(font.family())
        a.append(font.pointSize())
        a.append(font.bold())
        a.append(font.italic())
        a.append(font.underline())
        a.append(font.strikeOut())
        c["headline_font"] = a
        pallete = self.ui.txt_headline.palette()
        c["headline_color"] = pallete.color(self.ui.txt_headline.foregroundRole()).name()
        # Add X axis
        c["X"] = self.ui.txt_x_axis.text()
        a = []
        font = self.ui.txt_x_axis.font()
        a.append(font.family())
        a.append(font.pointSize())
        a.append(font.bold())
        a.append(font.italic())
        a.append(font.underline())
        a.append(font.strikeOut())
        c["X_font"] = a
        pallete = self.ui.txt_x_axis.palette()
        c["X_color"] = pallete.color(self.ui.txt_x_axis.foregroundRole()).name()
        # Add Y axis
        c["Y"] = self.ui.txt_y_axis.text()
        a = []
        font = self.ui.txt_y_axis.font()
        a.append(font.family())
        a.append(font.pointSize())
        a.append(font.bold())
        a.append(font.italic())
        a.append(font.underline())
        a.append(font.strikeOut())
        c["Y_font"] = a
        pallete = self.ui.txt_y_axis.palette()
        c["Y_color"] = pallete.color(self.ui.txt_y_axis.foregroundRole()).name()
        a = ["i_rsd", "o_rsd", "t_rsd", "i_eur", "o_eur", "t_eur"]
        c["Y_type"] = [a[self.ui.cmb_y_axis.currentIndex()], self.ui.cmb_y_axis.currentIndex()]
        # Add Graph stuff
        if self.ui.rdb_bars.isChecked():
            c["g_type"] = "bar"
        elif self.ui.rdb_lines.isChecked():
            c["g_type"] = "line"
        elif self.ui.rdb_pies.isChecked():
            c["g_type"] = "pie"
        pallete = self.ui.lbl_graph_color.palette()
        c["g_color"] = pallete.color(self.ui.lbl_graph_color.backgroundRole()).name()
        if self.ui.cmb_chart_marker.currentIndex() == 0:
            c["g_marker"] = ""
        else:
            x = self.ui.cmb_chart_marker.currentText()
            y = x.find("'", 1)
            x = x[1:y]
            c["g_marker"] = x
        if self.ui.cmb_chart_pattern.currentIndex() == 0:
            c["g_pattern"] = ""
        else:
            x = self.ui.cmb_chart_pattern.currentText()
            y = x.find("'", 1)
            x = x[1:y]
            c["g_pattern"] = x
        return c

    def btn_save_click(self):
        # Check if name is entered
        msg_title = self.conn.lang("chart_edit_btn_save_exists_msg_title", self.active_lang)
        if self.ui.txt_name.text() == "":
            msg_text = self.conn.lang("chart_edit_btn_save_no_name_question_msg_text", self.active_lang)
            result, ok_pressed = QtWidgets.QInputDialog.getText(self, msg_title, msg_text)
            if ok_pressed:
                if result == "":
                    msg_text = self.conn.lang("chart_edit_btn_save_no_name_error_msg_text", self.active_lang)
                    result = QtWidgets.QMessageBox.information(self, msg_title, msg_text, QtWidgets.QMessageBox.Ok)        
                    return
                else:
                    self.ui.txt_name.setText(result)
            else:
                return
        # Check is there already chart with same name
        result = self.chart.get_charts_all(chart_name=self.ui.txt_name.text())
        if len(result) > 0:
            if self.edit_mode == "" or result[0][1] != self.edit_mode:
                msg_text = self.conn.lang("chart_edit_btn_save_exists_msg_text", self.active_lang)
                msg_text = msg_text.replace("*", self.ui.txt_name.text())
                result = QtWidgets.QMessageBox.information(self, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
                return
        # Check is there data to show
        items_event_type = 0
        items_partner = 0
        items_location = 0
        for i in self.event_type_list:
            if i[1] == 1:
                items_event_type += 1
        for i in self.partners_list:
            if i[1] == 1:
                items_partner += 1
        for i in self.locations_list:
            if i[1] == 1:
                items_location += 1
        msg_title = self.conn.lang("chart_edit_win_title", self.active_lang)
        msg_text = ""
        if items_event_type == 0 and self.ui.chk_event_type.isChecked():
            msg_text = self.conn.lang("chart_edit_btn_save_no_event_type_msg_text", self.active_lang)
        elif items_partner == 0 and self.ui.chk_partner.isChecked():
            msg_text = self.conn.lang("chart_edit_btn_save_no_partners_msg_text", self.active_lang)
        elif items_location == 0 and self.ui.chk_location.isChecked():
            msg_text = self.conn.lang("chart_edit_btn_save_no_location_msg_text", self.active_lang)
        if msg_text != "":
            result = QtWidgets.QMessageBox.information(self, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
            return
        # Create chart dictionary
        c = self.create_chart_dictionary()
        # Add chart to database
        self.chart.add_chart(c, self.ui.txt_name.text())
        msg_text = self.conn.lang("chart_edit_btn_save_ok_msg_text", self.active_lang)
        result = QtWidgets.QMessageBox.information(self, msg_title, msg_text, QtWidgets.QMessageBox.Ok)
        self.close()

    def btn_cancel_click(self):
        msg_title = self.conn.lang("chart_edit_btn_cancel_msg_title", self.active_lang)
        msg_text = self.conn.lang("chart_edit_btn_cancel_msg_text", self.active_lang)
        result = QtWidgets.QMessageBox.question(self, msg_title, msg_text, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if result == QtWidgets.QMessageBox.No:
            return
        self.close()

    def cmb_y_axis_text_changed(self):
        self.ui.txt_y_axis.setText(self.ui.cmb_y_axis.currentText())

    def rdb_charts_toggled(self):
        if self.ui.rdb_bars.isChecked():
            img = "data/assets/chart_bar.png"
            self.ui.cmb_chart_pattern.setEnabled(True)
        elif self.ui.rdb_lines.isChecked():
            img = "data/assets/chart_line.png"
            self.ui.cmb_chart_pattern.setEnabled(False)
        elif self.ui.rdb_pies.isChecked():
            img = "data/assets/chart_pie.png"
            self.ui.cmb_chart_pattern.setEnabled(True)
        self.ui.lbl_pic.setPixmap(QtGui.QPixmap(img))

    def btn_chart_color_click(self):
        color = QtWidgets.QColorDialog.getColor(self.ui.lbl_graph_color.palette().window().color())
        if color.isValid():
            self.ui.lbl_graph_color.setStyleSheet(f"background-color: {color.name()};")

    def btn_headline_font_click(self):
        font, ok = QtWidgets.QFontDialog.getFont(self.ui.txt_headline.font())
        if ok:
            self.ui.txt_headline.setFont(font)

    def btn_headline_color_click(self):
        color = QtWidgets.QColorDialog.getColor(self.ui.txt_headline.palette().text().color())
        if color.isValid():
            self.ui.txt_headline.setStyleSheet(f"color: {color.name()};")

    def btn__x_axis_font_click(self):
        font, ok = QtWidgets.QFontDialog.getFont(self.ui.txt_x_axis.font())
        if ok:
            self.ui.txt_x_axis.setFont(font)

    def btn__x_axis_color_click(self):
        color = QtWidgets.QColorDialog.getColor(self.ui.txt_x_axis.palette().text().color())
        if color.isValid():
            self.ui.txt_x_axis.setStyleSheet(f"color: {color.name()};")

    def btn__y_axis_font_click(self):
        font, ok = QtWidgets.QFontDialog.getFont(self.ui.txt_y_axis.font())
        if ok:
            self.ui.txt_y_axis.setFont(font)

    def btn__y_axis_color_click(self):
        color = QtWidgets.QColorDialog.getColor(self.ui.txt_y_axis.palette().text().color())
        if color.isValid():
            self.ui.txt_y_axis.setStyleSheet(f"color: {color.name()};")

    def rdb_group_by_toggled(self):
        if self.ui.rdb_dates.isChecked():
            txt = self.conn.lang("chart_edit_by_dates_x_axis_title", self.active_lang)
        elif self.ui.rdb_weeks.isChecked():
            txt = self.conn.lang("report_header_weeks_view", self.active_lang)
        elif self.ui.rdb_months.isChecked():
            txt = self.conn.lang("report_header_months_view", self.active_lang)
        elif self.ui.rdb_years.isChecked():
            txt = self.conn.lang("report_header_years_view", self.active_lang)
        self.update_info_line_text()
    
    def update_info_line_text(self):
        txt = self.conn.lang("graph_edit_info_line_text1", self.active_lang)
        txt1 = self.conn.lang("graph_edit_info_line_text2", self.active_lang)
        # Resolve event type
        all_checked = True
        none_checked = True
        for i in self.event_type_list:
            if i[1] == 1:
                none_checked = False
            elif i[1] == 0:
                all_checked = False
        if len(self.event_type_list) > 0:
            if self.ui.chk_event_type.isChecked():
                txt1 = self.ui.chk_event_type.text() + " ("
                if all_checked:
                    txt1 = txt1 + self.conn.lang("graph_edit_info_line_text3", self.active_lang) + ") "
                elif none_checked:
                    txt1 = txt1 + self.conn.lang("graph_edit_info_line_text4", self.active_lang) + ") "
                else:
                    for i in self.event_type_list:
                        if i[1] == 1:
                            txt1 = txt1 + i[2] + ", "
                    txt1 = txt1[:-2]
                    txt1 = txt1 + ") "
            else:
                txt1 = self.ui.chk_event_type.text() + " (" + self.conn.lang("graph_edit_info_line_text3", self.active_lang) + ") "
        else:
            txt1 = self.ui.chk_event_type.text() + " (" + self.conn.lang("graph_edit_info_line_text4", self.active_lang) + ") "
        txt = txt + txt1 + "& "
        # Resolve partner
        all_checked = True
        none_checked = True
        for i in self.partners_list:
            if i[1] == 1:
                none_checked = False
            elif i[1] == 0:
                all_checked = False
        if len(self.partners_list) > 0:
            if self.ui.chk_partner.isChecked():
                txt1 = self.ui.chk_partner.text() + " ("
                if all_checked:
                    txt1 = txt1 + self.conn.lang("graph_edit_info_line_text3", self.active_lang) + ") "
                elif none_checked:
                    txt1 = txt1 + self.conn.lang("graph_edit_info_line_text4", self.active_lang) + ") "
                else:
                    for i in self.partners_list:
                        if i[1] == 1:
                            txt1 = txt1 + i[2] + ", "
                    txt1 = txt1[:-2]
                    txt1 = txt1 + ") "
            else:
                txt1 = self.ui.chk_partner.text() + " (" + self.conn.lang("graph_edit_info_line_text3", self.active_lang) + ") "
        else:
            txt1 = self.ui.chk_partner.text() + " (" + self.conn.lang("graph_edit_info_line_text4", self.active_lang) + ") "
        txt = txt + txt1 + "& "
        # Resolve location
        all_checked = True
        none_checked = True
        for i in self.locations_list:
            if i[1] == 1:
                none_checked = False
            elif i[1] == 0:
                all_checked = False
        if len(self.locations_list) > 0:
            if self.ui.chk_location.isChecked():
                txt1 = self.ui.chk_location.text() + " ("
                if all_checked:
                    txt1 = txt1 + self.conn.lang("graph_edit_info_line_text3", self.active_lang) + ") "
                elif none_checked:
                    txt1 = txt1 + self.conn.lang("graph_edit_info_line_text4", self.active_lang) + ") "
                else:
                    for i in self.locations_list:
                        if i[1] == 1:
                            txt1 = txt1 + i[2] + ", "
                    txt1 = txt1[:-2]
                    txt1 = txt1 + ") "
            else:
                txt1 = self.ui.chk_location.text() + " (" + self.conn.lang("graph_edit_info_line_text3", self.active_lang) + ") "
        else:
            txt1 = self.ui.chk_location.text() + " (" + self.conn.lang("graph_edit_info_line_text4", self.active_lang) + ") "
        txt = txt + txt1
        # Resolve Group by
        txt = txt + " " + self.ui.lbl_group_by.text() + " "
        if self.ui.rdb_dates.isChecked():
            txt1 = self.ui.rdb_dates.text()
        elif self.ui.rdb_weeks.isChecked():
            txt1 = self.ui.rdb_weeks.text()
        elif self.ui.rdb_months.isChecked():
            txt1 = self.ui.rdb_months.text()
        elif self.ui.rdb_years.isChecked():
            txt1 = self.ui.rdb_years.text()
        txt = txt + txt1
        self.ui.lbl_info.setText(txt)

    def btn_event_type_filter_apply_click(self):
        self.ui.btn_event_type_filter_apply.setEnabled(False)
        self.filter_event_type_btn_state = 0
        self.update_event_type_list()
        self._setup_event_type_status()

    def btn_partner_filter_apply_click(self):
        self.ui.btn_partner_filter_apply.setEnabled(False)
        self.filter_partner_btn_state = 0
        self.update_partners_list()
        self._setup_partner_status()

    def btn_location_filter_apply_click(self):
        self.ui.btn_location_filter_apply.setEnabled(False)
        self.filter_location_btn_state = 0
        self.update_locations_list()
        self._setup_location_status()

    def txt_event_type_filter_text_changed(self):
        self.ui.btn_event_type_filter_apply.setEnabled(True)
        self.filter_event_type_btn_state = 1

    def txt_partner_filter_text_changed(self):
        self.ui.btn_partner_filter_apply.setEnabled(True)
        self.filter_partner_btn_state = 1

    def txt_location_filter_text_changed(self):
        self.ui.btn_location_filter_apply.setEnabled(True)
        self.filter_location_btn_state = 1

    def lst_event_type_changed(self, item):
        evt_id = item.data(QtCore.Qt.UserRole)
        if item.checkState() == QtCore.Qt.Checked:
            for i in range(len(self.event_type_list)):
                if self.event_type_list[i][3] == evt_id:
                    self.event_type_list[i][1] = 1
                    break
        else:
            for i in range(len(self.event_type_list)):
                if self.event_type_list[i][3] == evt_id:
                    self.event_type_list[i][1] = 0
                    break
        self._setup_event_type_status()

    def lst_partner_changed(self, item):
        evt_id = item.data(QtCore.Qt.UserRole)
        if item.checkState() == QtCore.Qt.Checked:
            for i in range(len(self.partners_list)):
                if self.partners_list[i][3] == evt_id:
                    self.partners_list[i][1] = 1
                    break
        else:
            for i in range(len(self.partners_list)):
                if self.partners_list[i][3] == evt_id:
                    self.partners_list[i][1] = 0
                    break
        self._setup_partner_status()

    def lst_location_changed(self, item):
        evt_id = item.data(QtCore.Qt.UserRole)
        if item.checkState() == QtCore.Qt.Checked:
            for i in range(len(self.locations_list)):
                if self.locations_list[i][3] == evt_id:
                    self.locations_list[i][1] = 1
                    break
        else:
            for i in range(len(self.locations_list)):
                if self.locations_list[i][3] == evt_id:
                    self.locations_list[i][1] = 0
                    break
        self._setup_location_status()

    def btn_event_type_select_all_click(self):
        for i in range(self.ui.lst_event_type.count()):
            self.ui.lst_event_type.item(i).setCheckState(QtCore.Qt.Checked)
            for j in range(len(self.event_type_list)):
                if self.event_type_list[j][3] == self.ui.lst_event_type.item(i).data(QtCore.Qt.UserRole):
                    self.event_type_list[j][1] = 1
                    break
        self._setup_event_type_status()

    def btn_partner_select_all_click(self):
        for i in range(self.ui.lst_partner.count()):
            self.ui.lst_partner.item(i).setCheckState(QtCore.Qt.Checked)
            for j in range(len(self.partners_list)):
                if self.partners_list[j][3] == self.ui.lst_partner.item(i).data(QtCore.Qt.UserRole):
                    self.partners_list[j][1] = 1
                    break
        self._setup_partner_status()

    def btn_location_select_all_click(self):
        for i in range(self.ui.lst_location.count()):
            self.ui.lst_location.item(i).setCheckState(QtCore.Qt.Checked)
            for j in range(len(self.locations_list)):
                if self.locations_list[j][3] == self.ui.lst_location.item(i).data(QtCore.Qt.UserRole):
                    self.locations_list[j][1] = 1
                    break
        self._setup_location_status()

    def btn_event_type_clear_all_click(self):
        for i in range(self.ui.lst_event_type.count()):
            self.ui.lst_event_type.item(i).setCheckState(QtCore.Qt.Unchecked)
            for j in range(len(self.event_type_list)):
                if self.event_type_list[j][3] == self.ui.lst_event_type.item(i).data(QtCore.Qt.UserRole):
                    self.event_type_list[j][1] = 0
                    break
        self._setup_event_type_status()

    def btn_partner_clear_all_click(self):
        for i in range(self.ui.lst_partner.count()):
            self.ui.lst_partner.item(i).setCheckState(QtCore.Qt.Unchecked)
            for j in range(len(self.partners_list)):
                if self.partners_list[j][3] == self.ui.lst_partner.item(i).data(QtCore.Qt.UserRole):
                    self.partners_list[j][1] = 0
                    break
        self._setup_partner_status()

    def btn_location_clear_all_click(self):
        for i in range(self.ui.lst_location.count()):
            self.ui.lst_location.item(i).setCheckState(QtCore.Qt.Unchecked)
            for j in range(len(self.locations_list)):
                if self.locations_list[j][3] == self.ui.lst_location.item(i).data(QtCore.Qt.UserRole):
                    self.locations_list[j][1] = 0
                    break
        self._setup_location_status()

    def setup_widgets_status(self):
        self._setup_event_type_status()
        self._setup_partner_status()
        self._setup_location_status()

    def _setup_event_type_status(self):
        if self.ui.chk_event_type.isChecked():
            self.ui.lst_event_type.setEnabled(True)
            self.ui.txt_event_type_filter.setEnabled(True)
            self.ui.btn_event_type_filter_apply.setEnabled(self.filter_event_type_btn_state)
            items_checked = 0
            items_cleared = 0
            items_total = 0
            for i in self.event_type_list:
                if i[0] == 1:
                    items_total += 1
                    if i[1] == 1:
                        items_checked += 1
                    else:
                        items_cleared += 1
            if items_checked == items_total:
                self.ui.btn_event_type_select_all.setEnabled(False)
            else:
                self.ui.btn_event_type_select_all.setEnabled(True)
            if items_cleared == items_total:
                self.ui.btn_event_type_clear_all.setEnabled(False)
            else:
                self.ui.btn_event_type_clear_all.setEnabled(True)
        else:
            self.ui.lst_event_type.setEnabled(False)
            self.ui.txt_event_type_filter.setEnabled(False)
            self.ui.btn_event_type_filter_apply.setEnabled(False)
            self.ui.btn_event_type_select_all.setEnabled(False)
            self.ui.btn_event_type_clear_all.setEnabled(False)
        self.update_info_line_text()

    def _setup_partner_status(self):
        if self.ui.chk_partner.isChecked():
            self.ui.lst_partner.setEnabled(True)
            self.ui.txt_partner_filter.setEnabled(True)
            self.ui.btn_partner_filter_apply.setEnabled(self.filter_partner_btn_state)
            items_checked = 0
            items_cleared = 0
            items_total = 0
            for i in self.partners_list:
                if i[0] == 1:
                    items_total += 1
                    if i[1] == 1:
                        items_checked += 1
                    else:
                        items_cleared += 1
            if items_checked == items_total:
                self.ui.btn_partner_select_all.setEnabled(False)
            else:
                self.ui.btn_partner_select_all.setEnabled(True)
            if items_cleared == items_total:
                self.ui.btn_partner_clear_all.setEnabled(False)
            else:
                self.ui.btn_partner_clear_all.setEnabled(True)
        else:
            self.ui.lst_partner.setEnabled(False)
            self.ui.txt_partner_filter.setEnabled(False)
            self.ui.btn_partner_filter_apply.setEnabled(False)
            self.ui.btn_partner_select_all.setEnabled(False)
            self.ui.btn_partner_clear_all.setEnabled(False)
        self.update_info_line_text()

    def _setup_location_status(self):
        if self.ui.chk_location.isChecked():
            self.ui.lst_location.setEnabled(True)
            self.ui.txt_location_filter.setEnabled(True)
            self.ui.btn_location_filter_apply.setEnabled(self.filter_location_btn_state)
            items_checked = 0
            items_cleared = 0
            items_total = 0
            for i in self.locations_list:
                if i[0] == 1:
                    items_total += 1
                    if i[1] == 1:
                        items_checked += 1
                    else:
                        items_cleared += 1
            if items_checked == items_total:
                self.ui.btn_location_select_all.setEnabled(False)
            else:
                self.ui.btn_location_select_all.setEnabled(True)
            if items_cleared == items_total:
                self.ui.btn_location_clear_all.setEnabled(False)
            else:
                self.ui.btn_location_clear_all.setEnabled(True)
        else:
            self.ui.lst_location.setEnabled(False)
            self.ui.txt_location_filter.setEnabled(False)
            self.ui.btn_location_filter_apply.setEnabled(False)
            self.ui.btn_location_select_all.setEnabled(False)
            self.ui.btn_location_clear_all.setEnabled(False)
        self.update_info_line_text()

    def fill_widgets_with_general_data(self):
        # Populate lists with data
        self.update_event_type_list()
        self.update_partners_list()
        self.update_locations_list()
        # Set default Radio Buttons
        self.ui.rdb_months.setChecked(True)
        self.ui.rdb_bars.setChecked(True)
        # Populate Y Axis ComboBox
        self.ui.cmb_y_axis.clear()
        self.ui.cmb_y_axis.addItem(self.conn.lang("main_tbl_header_prihod_rsd", self.active_lang), 1)
        self.ui.cmb_y_axis.addItem(self.conn.lang("main_tbl_header_rashod_rsd", self.active_lang), 2)
        self.ui.cmb_y_axis.addItem(self.conn.lang("report_header_event_type_view_total_rsd", self.active_lang), 3)
        self.ui.cmb_y_axis.addItem(self.conn.lang("main_tbl_header_prihod_eur", self.active_lang), 4)
        self.ui.cmb_y_axis.addItem(self.conn.lang("main_tbl_header_rashod_eur", self.active_lang), 5)
        self.ui.cmb_y_axis.addItem(self.conn.lang("report_header_event_type_view_total_eur", self.active_lang), 6)
        self.ui.cmb_y_axis.setCurrentIndex(1)
        self.ui.txt_y_axis.setText(self.ui.cmb_y_axis.currentText())
        # Populate markers ComboBox
        self.ui.cmb_chart_marker.clear()
        self.ui.cmb_chart_marker.addItem(self.conn.lang("graph_edit_marker0", self.active_lang))
        for i in range(1,21):
            txt_find = "graph_edit_marker" + str(i)
            txt = self.conn.lang(txt_find, self.active_lang) + self.conn.lang("graph_edit_marker_marker", self.active_lang)
            self.ui.cmb_chart_marker.addItem(txt)
        for i in range(self.ui.cmb_chart_marker.count()):
            item = self.ui.cmb_chart_marker.itemText(i)
            self.ui.cmb_chart_marker.setItemData(i, item, QtCore.Qt.ToolTipRole)
        # Populate paterns ComboBox
        self.ui.cmb_chart_pattern.clear()
        self.ui.cmb_chart_pattern.addItem(self.conn.lang("graph_edit_marker0", self.active_lang))
        for i in range(1,14):
            txt_find = "graph_edit_pattern" + str(i)
            txt = self.conn.lang(txt_find, self.active_lang) + self.conn.lang("graph_edit_pattern_pattern", self.active_lang)
            self.ui.cmb_chart_pattern.addItem(txt)
        for i in range(self.ui.cmb_chart_pattern.count()):
            item = self.ui.cmb_chart_pattern.itemText(i)
            self.ui.cmb_chart_pattern.setItemData(i, item, QtCore.Qt.ToolTipRole)
        self.rdb_group_by_toggled()

    def update_locations_list(self):
        # Get filter criteria
        flt = self.ui.txt_location_filter.text().lower()
        # Clear list
        self.ui.lst_location.clear()
        # Check if filter allows item to be visible
        for i in range(len(self.locations_list)):
            low_item = self.locations_list[i][2].lower()
            item_is_visible = 1
            if flt != "":
                if low_item.find(flt) < 0:
                    item_is_visible = 0
            self.locations_list[i][0] = item_is_visible
        # Fill list
        l = self.locations_list
        for i in range(len(l)):
            # Create item
            item = QtWidgets.QListWidgetItem()
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setText(l[i][2])
            item.setData(QtCore.Qt.UserRole, l[i][3])
            # If item is checked set state to checked
            if l[i][1] == 1:
                item.setCheckState(QtCore.Qt.Checked)
            else:
                item.setCheckState(QtCore.Qt.Unchecked)
            # Add item to list
            if l[i][0] == 1:
                self.ui.lst_location.addItem(item)

    def update_partners_list(self):
        # Get filter criteria
        flt = self.ui.txt_partner_filter.text().lower()
        # Clear list
        self.ui.lst_partner.clear()
        # Check if filter allows item to be visible
        for i in range(len(self.partners_list)):
            low_item = self.partners_list[i][2].lower()
            item_is_visible = 1
            if flt != "":
                if low_item.find(flt) < 0:
                    item_is_visible = 0
            self.partners_list[i][0] = item_is_visible
        # Fill list
        l = self.partners_list
        for i in range(len(l)):
            # Create item
            item = QtWidgets.QListWidgetItem()
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setText(l[i][2])
            item.setData(QtCore.Qt.UserRole, l[i][3])
            # If item is checked set state to checked
            if l[i][1] == 1:
                item.setCheckState(QtCore.Qt.Checked)
            else:
                item.setCheckState(QtCore.Qt.Unchecked)
            # Add item to list
            if l[i][0] == 1:
                self.ui.lst_partner.addItem(item)

    def update_event_type_list(self):
        # Get filter criteria
        flt = self.ui.txt_event_type_filter.text().lower()
        # Clear list
        self.ui.lst_event_type.clear()
        # Check if filter allows item to be visible
        for i in range(len(self.event_type_list)):
            low_item = self.event_type_list[i][2].lower()
            item_is_visible = 1
            if flt != "":
                if low_item.find(flt) < 0:
                    item_is_visible = 0
            self.event_type_list[i][0] = item_is_visible
        # Fill list
        l = self.event_type_list
        for i in range(len(l)):
            # Create item
            item = QtWidgets.QListWidgetItem()
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setText(l[i][2])
            item.setData(QtCore.Qt.UserRole, l[i][3])
            # If item is checked set state to checked
            if l[i][1] == 1:
                item.setCheckState(QtCore.Qt.Checked)
            else:
                item.setCheckState(QtCore.Qt.Unchecked)
            # Add item to list
            if l[i][0] == 1:
                self.ui.lst_event_type.addItem(item)

    def _fill_lists_for_list_widgets(self):
        # Event type
        result = self.user.get_event_type_all()
        for i in result:
            self.event_type_list.append([1, 1, i[1], i[0]])
        # Locations
        result = self.user.get_place_all()
        for i in result:
            self.locations_list.append([1, 1, i[1], i[0]])
        # Partner (partner ID = generic += 1)
        gen_id = 0
        result = self.user.get_partner_list_unique(sort_data=True)
        for i in result:
            gen_id += 1
            self.partners_list.append([1, 1, i[0], gen_id])

    def retranslateUi(self):
        self.setWindowTitle(self.conn.lang("chart_edit_win_title", self.active_lang))
        self.ui.grp_organization.setTitle(self.conn.lang("chart_edit_grp_organization_title", self.active_lang))
        self.ui.chk_event_type.setText(self.conn.lang("chart_edit_chk_event_type", self.active_lang))
        self.ui.btn_event_type_select_all.setText(self.conn.lang("btn_select_all", self.active_lang))
        self.ui.btn_event_type_clear_all.setText(self.conn.lang("btn_clear_all", self.active_lang))
        self.ui.btn_location_clear_all.setText(self.conn.lang("btn_clear_all", self.active_lang))
        self.ui.btn_location_select_all.setText(self.conn.lang("btn_select_all", self.active_lang))
        self.ui.chk_location.setText(self.conn.lang("chart_edit_chk_location", self.active_lang))
        self.ui.txt_event_type_filter.setPlaceholderText(self.conn.lang("chart_edit_txt_event_type_filter_placeholder", self.active_lang))
        self.ui.txt_location_filter.setPlaceholderText(self.conn.lang("chart_edit_txt_event_type_filter_placeholder", self.active_lang))
        self.ui.txt_partner_filter.setPlaceholderText(self.conn.lang("chart_edit_txt_event_type_filter_placeholder", self.active_lang))
        self.ui.btn_partner_clear_all.setText(self.conn.lang("btn_clear_all", self.active_lang))
        self.ui.btn_partner_select_all.setText(self.conn.lang("btn_select_all", self.active_lang))
        self.ui.chk_partner.setText(self.conn.lang("chart_edit_chk_partner", self.active_lang))
        self.ui.lbl_group_by.setText(self.conn.lang("chart_edit_lbl_group_by", self.active_lang))
        self.ui.rdb_dates.setText(self.conn.lang("chart_edit_rdb_dates", self.active_lang))
        self.ui.rdb_weeks.setText(self.conn.lang("chart_edit_rdb_weeks", self.active_lang))
        self.ui.rdb_months.setText(self.conn.lang("chart_edit_rdb_months", self.active_lang))
        self.ui.rdb_years.setText(self.conn.lang("chart_edit_rdb_years", self.active_lang))
        self.ui.lbl_chart_edit.setText(self.conn.lang("chart_edit_lbl_chart_edit", self.active_lang))
        self.ui.lbl_chart_name.setText(self.conn.lang("chart_edit_lbl_chart_name", self.active_lang))
        self.ui.btn_save.setText(self.conn.lang("btn_save", self.active_lang))
        self.ui.btn_preview.setText(self.conn.lang("btn_preview", self.active_lang))
        self.ui.grp_design.setTitle(self.conn.lang("chart_edit_grp_design_title", self.active_lang))
        self.ui.btn_headline_font.setText(self.conn.lang("btn_font", self.active_lang))
        self.ui.btn_headline_color.setText(self.conn.lang("btn_color", self.active_lang))
        self.ui.lbl_headline.setText(self.conn.lang("graph_edit_lbl_headline", self.active_lang))
        self.ui.btn_x_axis_color.setText(self.conn.lang("btn_color", self.active_lang))
        self.ui.lbl_x_axis.setText(self.conn.lang("graph_edit_lbl_x_axis", self.active_lang))
        self.ui.btn_x_axis_font.setText(self.conn.lang("btn_font", self.active_lang))
        self.ui.btn_y_axis_font.setText(self.conn.lang("btn_font", self.active_lang))
        self.ui.btn_y_axis_color.setText(self.conn.lang("btn_color", self.active_lang))
        self.ui.lbl_y_axis.setText(self.conn.lang("graph_edit_lbl_y_axis", self.active_lang))
        self.ui.rdb_bars.setText(self.conn.lang("graph_edit_rdb_bars", self.active_lang))
        self.ui.rdb_lines.setText(self.conn.lang("graph_edit_rdb_lines", self.active_lang))
        self.ui.btn_chart_color.setText(self.conn.lang("btn_color", self.active_lang))
        self.ui.btn_cancel.setText(self.conn.lang("btn_cancel", self.active_lang))
        self.ui.lbl_chart_description.setText(self.conn.lang("graph_edit_lbl_chart_description", self.active_lang))
        self.ui.txt_name.setText(self.conn.lang("chart_edit_txt_name_untitled", self.active_lang))
        self.ui.txt_headline.setText(self.conn.lang("chart_edit_txt_name_untitled", self.active_lang))
        self.ui.rdb_pies.setText(self.conn.lang("graph_edit_rdb_pies", self.active_lang))
        

class ChartContainer(QtWidgets.QDialog):
    def __init__(self, user_id, user_name, language, chart_dictionary, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create enviroment variables
        self.active_user_id = user_id
        self.active_user_name = user_name
        self.active_lang = language
        self.chart_dict = chart_dictionary

        self.conn = connection.ConnStart()
        self.log = log_cls.LogData()
        self.chart = connection.Chart(self.active_user_id)
        self.user = connection.User(self.active_user_id)

    def setup_gui(self):
        # Setup Widgets
        self.setup_ui()
        self.load_settings()

        # Connect events with slots
        self.closeEvent = self.save_settings

        # Show Chart
        if "x_value" in self.chart_dict:
            self._show_simple_graph()
        else:
            self.show_graph()

        self.show()
        self.exec_()

    def _show_simple_graph(self):
        x = self.chart_dict["x_value"]
        y = self.chart_dict["y_value"]
        title = self.chart_dict["headline"]
        lbls = [self.chart_dict["X"], self.chart_dict["Y"]]

        ax = self.fig.add_subplot()
        ax.bar(x, y)
        step = int(len(x)/60) + 1
        avg = (max(y) - min(y)) / 2
        ax.set_xticks(x[::step])
        ax.tick_params(axis="x", labelrotation=90)
        ax.set_xlabel(lbls[0])
        ax.set_ylabel(lbls[1])
        ax.yaxis.set_major_formatter('{x:,.0f}')
        ax.axhline(y=0, color="r")
        ax.axhline(y=avg, color="g", linestyle="--")
        ax.scatter(x, y, marker="o", color="b")
        self.fig.subplots_adjust(bottom=0.22)
        ax.set_title(title, fontdict={"fontsize":20})
        for i, val in enumerate(y):
            ax.text(x[i], y[i], str(val), ha="center", va="bottom", color="r", fontdict={"fontsize":8})
    
    def calculate_x_y_data(self):
        c = self.chart_dict
        data = self.chart.get_filter_data(c)
        q_sum = c["Y_type"][1] + 1
        x = []
        y = []
        s = 0
        for i in data:
            if c["event_type"] == "all" or (i[7] in c["event_type"]):
                if c["partner"] == "all" or (i[8] in c["partner"]):
                    if c["location"] == "all" or (i[9] in c["location"]):
                        if i[0] in x:
                            s = s + i[q_sum]
                        else:
                            x.append(i[0])
                            y.append(s)
                            s = i[q_sum]
        if len(x) > 0:
            y.append(s)
            y.pop(0)
        return x, y
    
    def show_graph(self):
        x, y = self.calculate_x_y_data()

        ax = self.fig.add_subplot()
        if self.chart_dict["g_type"] == "bar":
            ax.bar(x, y, hatch=self.chart_dict["g_pattern"], color=self.chart_dict["g_color"])
        elif self.chart_dict["g_type"] == "line":
            ax.plot(x, y, marker=self.chart_dict["g_marker"], color=self.chart_dict["g_color"])
        elif self.chart_dict["g_type"] == "pie":
            z = [0.2] * len(x)
            ax.pie(y, labels=x, explode=z)
            return
        
        step = int(len(x)/60) + 1
        avg = (max(y) - min(y)) / 2
        ax.set_xticks(x[::step])
        ax.tick_params(axis="x", labelrotation=90)
        ax.yaxis.set_major_formatter('{x:,.0f}')
        ax.axhline(y=0, color="r")
        ax.axhline(y=avg, color="g", linestyle="--")

        self.fig.subplots_adjust(bottom=0.22)

        font = self._setup_fontdic(self.chart_dict["X_font"], self.chart_dict["X_color"])
        ax.set_xlabel(self.chart_dict["X"],fontdict=font)
        font = self._setup_fontdic(self.chart_dict["Y_font"], self.chart_dict["Y_color"])
        ax.set_ylabel(self.chart_dict["Y"], fontdict=font)
        font = self._setup_fontdic(self.chart_dict["headline_font"], self.chart_dict["headline_color"])
        ax.set_title(self.chart_dict["headline"], fontdict=font)
        for i, val in enumerate(y):
            ax.text(x[i], y[i], str(val), ha="center", va="bottom", color="r", fontdict={"fontsize":8})
        # plt.show()

    def _setup_fontdic(self, chart_font, color):
        c = chart_font
        f = {}
        f["family"] = c[0]
        f["size"] = c[1]
        if c[2] == 1:
            f["weight"] = "bold"
        if c[3] == 1:
            f["style"] = "italic"
        if c[4] == 1:
            f["underline"] = True
        if c[5] == 1:
            f["strikeout"] = True
        f["color"] = color
        return f

    def setup_ui(self):
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowCloseButtonHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.v_layout = QtWidgets.QVBoxLayout(self)
        # Create matplotlib Figure
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        # dodajte Matplotlib canvas u QDialog koristeći QVBoxLayout
        self.v_layout.addWidget(self.canvas)

    def load_settings(self):
        x = self.conn.get_setting_data("chart_container_win_x", getParametar=True, user_id=self.active_user_id)
        y = self.conn.get_setting_data("chart_container_win_y", getParametar=True, user_id=self.active_user_id)
        w = self.conn.get_setting_data("chart_container_win_w", getParametar=True, user_id=self.active_user_id)
        h = self.conn.get_setting_data("chart_container_win_h", getParametar=True, user_id=self.active_user_id)
        self.move(x, y)
        self.resize(w, h)

    def save_settings(self, i):
        x = self.pos().x()
        y = self.pos().y()
        w = self.width()
        h = self.height()
        self.conn.set_setting_data("chart_container_win_x", "Win geometry", x, self.active_user_id)
        self.conn.set_setting_data("chart_container_win_y", "Win geometry", y, self.active_user_id)
        self.conn.set_setting_data("chart_container_win_w", "Win geometry", w, self.active_user_id)
        self.conn.set_setting_data("chart_container_win_h", "Win geometry", h, self.active_user_id)



