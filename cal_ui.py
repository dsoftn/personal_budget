from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.WindowModal)
        Dialog.resize(300, 260)
        Dialog.setMinimumSize(QtCore.QSize(300, 260))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("data/assets/calendar.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        Dialog.setModal(True)
        self.cld_datum = QtWidgets.QCalendarWidget(Dialog)
        self.cld_datum.setGeometry(QtCore.QRect(0, 0, 300, 221))
        self.cld_datum.setLocale(QtCore.QLocale(QtCore.QLocale.Serbian, QtCore.QLocale.Serbia))
        self.cld_datum.setGridVisible(True)
        self.cld_datum.setObjectName("cld_datum")
        self.btn_ok = QtWidgets.QPushButton(Dialog)
        self.btn_ok.setGeometry(QtCore.QRect(140, 230, 75, 23))
        self.btn_ok.setObjectName("btn_ok")
        self.btn_cancel = QtWidgets.QPushButton(Dialog)
        self.btn_cancel.setGeometry(QtCore.QRect(220, 230, 75, 23))
        self.btn_cancel.setObjectName("btn_cancel")

        QtCore.QMetaObject.connectSlotsByName(Dialog)

