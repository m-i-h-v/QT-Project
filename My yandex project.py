import sqlite3
import sys

from PyQt5 import uic, QtGui
from PyQt5.QtCore import QTimer, Qt, QEvent, QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel
from PyQt5.QtWidgets import QWidget, QApplication, QAbstractButton, QMainWindow, QToolButton, QHBoxLayout, QGridLayout, \
    QScrollArea, QVBoxLayout, QTableWidgetItem, QTableWidget, QHeaderView
from PyQt5.QtWidgets import QLineEdit, QCheckBox, QLabel, QPushButton, QPlainTextEdit
import requests
from PyQt5.uic.properties import QtCore, QtWidgets
from bs4 import BeautifulSoup
import datetime as dt


class Clock:
    def __init__(self, other, type, timezone, num, seconds=None, minutes=True, coefficient=2):
        self.other, self.clock_type, self.timezone = other, type, timezone
        self.seconds, self.minutes, self.coefficient = seconds, minutes, coefficient
        self.num = num

    def add_changes(self, new_type, new_timezone):
        self.clock_type = new_type
        sign = new_timezone[3]
        timezone = new_timezone[3:].split(':')
        self.timezone = [int(timezone[0]), 0 if len(timezone) == 1 else int(sign + timezone[1])]

    def update_clock(self):
        time = self.other.current_time
        time = [time[0], time[1], time[2]]
        time[0] = (time[0] + self.timezone[0] + (time[1] + self.timezone[1]) // 60) % 24
        time[1] = (time[1] + self.timezone[1]) % 60
        if self.clock_type == 'analog':
            self.draw_analog(time)
        else:
            self.draw_digit(time)

    def draw_analog(self, time):
        self.other.clock_faces[self.num].setText('analog ' + ':'.join(map(str, time)))

    def draw_digit(self, time):
        self.other.clock_faces[self.num].setText('digit ' + ':'.join(map(str, time)))


class AddClockNotEverythingIsSelected(Exception):
    def __init__(self, other):
        super().__init__()

        other.Label_1.setHidden(False)
        other.Label_2.setHidden(False)


class FirstWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('Ui/MainWindowUi.ui', self)

#        response = requests.get('https://www.timeanddate.com/worldclock/timezone/utc')
#        soup = BeautifulSoup(response.text, 'html.parser')
#        time = map(int, str(soup.find("span", class_="h1", id="ct")).split('>')[1].split('<')[0].split(':'))
#        self.current_time = list(time)
        self.current_time = [0, 0, 0]

        self.alarm_clock_button.clicked.connect(self.alarm_clocks)

        self.clocks = [None, None, None, None]
        self.clock_faces = {}

        self.clock_face_1 = QLabel(self)
        self.clock_face_1.setHidden(True)

        self.clock_face_2 = QLabel(self)
        self.clock_face_2.setHidden(True)

        self.clock_face_3 = QLabel(self)
        self.clock_face_3.setHidden(True)

        self.clock_face_4 = QLabel(self)
        self.clock_face_4.setHidden(True)

        self.clock_faces['1'] = self.clock_face_1
        self.clock_faces['2'] = self.clock_face_2
        self.clock_faces['3'] = self.clock_face_3
        self.clock_faces['4'] = self.clock_face_4

        self.Settings_clock_1 = MyButton()
        self.Settings_clock_2 = MyButton()
        self.Settings_clock_3 = MyButton()
        self.Settings_clock_4 = MyButton()

        self.Settings_clock_1.setObjectName('ClockSettings_1')
        self.Settings_clock_2.setObjectName('ClockSettings_2')
        self.Settings_clock_3.setObjectName('ClockSettings_3')
        self.Settings_clock_4.setObjectName('ClockSettings_4')

        self.Settings_clock_1.setFlat(True)
        self.Settings_clock_2.setFlat(True)
        self.Settings_clock_3.setFlat(True)
        self.Settings_clock_4.setFlat(True)

        self.Delete_clock_1 = MyButton()
        self.Delete_clock_2 = MyButton()
        self.Delete_clock_3 = MyButton()
        self.Delete_clock_4 = MyButton()

        self.Delete_clock_1.setFlat(True)
        self.Delete_clock_2.setFlat(True)
        self.Delete_clock_3.setFlat(True)
        self.Delete_clock_4.setFlat(True)

        self.add_clock_layout_1_2.insertWidget(0, self.Settings_clock_1)
        self.add_clock_layout_2_2.insertWidget(0, self.Settings_clock_2)
        self.add_clock_layout_3_2.insertWidget(0, self.Settings_clock_3)
        self.add_clock_layout_4_2.insertWidget(0, self.Settings_clock_4)
        self.add_clock_layout_1_2.insertWidget(1, self.Delete_clock_1)
        self.add_clock_layout_2_2.insertWidget(1, self.Delete_clock_2)
        self.add_clock_layout_3_2.insertWidget(1, self.Delete_clock_3)
        self.add_clock_layout_4_2.insertWidget(1, self.Delete_clock_4)

        self.Settings_clock_1.setIcon(QtGui.QIcon('images/SettingsButton.png'))
        self.Settings_clock_2.setIcon(QtGui.QIcon('images/SettingsButton.png'))
        self.Settings_clock_3.setIcon(QtGui.QIcon('images/SettingsButton.png'))
        self.Settings_clock_4.setIcon(QtGui.QIcon('images/SettingsButton.png'))

        self.Settings_clock_1.setHidden(True)
        self.Settings_clock_2.setHidden(True)
        self.Settings_clock_3.setHidden(True)
        self.Settings_clock_4.setHidden(True)

        self.Settings_clock_1.clicked.connect(self.clock_settings)
        self.Settings_clock_2.clicked.connect(self.clock_settings)
        self.Settings_clock_3.clicked.connect(self.clock_settings)
        self.Settings_clock_4.clicked.connect(self.clock_settings)

        self.Delete_clock_1.setHidden(True)
        self.Delete_clock_2.setHidden(True)
        self.Delete_clock_3.setHidden(True)
        self.Delete_clock_4.setHidden(True)

        self.Delete_clock_1.setIconSize(QSize(25, 25))
        self.Delete_clock_2.setIconSize(QSize(25, 25))
        self.Delete_clock_3.setIconSize(QSize(25, 25))
        self.Delete_clock_4.setIconSize(QSize(25, 25))

        self.Settings_clock_1.setIconSize(QSize(25, 25))
        self.Settings_clock_2.setIconSize(QSize(25, 25))
        self.Settings_clock_3.setIconSize(QSize(25, 25))
        self.Settings_clock_4.setIconSize(QSize(25, 25))

        self.Delete_clock_1.setObjectName('DeleteClock_1')
        self.Delete_clock_2.setObjectName('DeleteClock_2')
        self.Delete_clock_3.setObjectName('DeleteClock_3')
        self.Delete_clock_4.setObjectName('DeleteClock_4')

        self.Delete_clock_1.clicked.connect(self.delete_clock)
        self.Delete_clock_2.clicked.connect(self.delete_clock)
        self.Delete_clock_3.clicked.connect(self.delete_clock)
        self.Delete_clock_4.clicked.connect(self.delete_clock)

        self.delete_clock_buttons = {'1': self.Delete_clock_1,
                                     '2': self.Delete_clock_2,
                                     '3': self.Delete_clock_3,
                                     '4': self.Delete_clock_4}

        self.settings_clock_buttons = {'1': self.Settings_clock_1,
                                       '2': self.Settings_clock_2,
                                       '3': self.Settings_clock_3,
                                       '4': self.Settings_clock_4}

        self.clock_layouts = {'1': self.add_clock_layout_1,
                              '2': self.add_clock_layout_2,
                              '3': self.add_clock_layout_3,
                              '4': self.add_clock_layout_4}

        self.clock_1 = MyButton()
        self.clock_2 = MyButton()
        self.clock_3 = MyButton()
        self.clock_4 = MyButton()

        self.clock_1.setObjectName('clock_1')
        self.clock_2.setObjectName('clock_2')
        self.clock_3.setObjectName('clock_3')
        self.clock_4.setObjectName('clock_4')

        self.add_clock_layout_1.insertWidget(0, self.clock_1)
        self.add_clock_layout_2.insertWidget(0, self.clock_2)
        self.add_clock_layout_3.insertWidget(0, self.clock_3)
        self.add_clock_layout_4.insertWidget(0, self.clock_4)

        self.clock_1.setIcon(QtGui.QIcon('images/PlusButton.png'))
        self.clock_2.setIcon(QtGui.QIcon('images/PlusButton.png'))
        self.clock_3.setIcon(QtGui.QIcon('images/PlusButton.png'))
        self.clock_4.setIcon(QtGui.QIcon('images/PlusButton.png'))

        self.clock_1.setIconSize(QSize(250, 250))
        self.clock_2.setIconSize(QSize(250, 250))
        self.clock_3.setIconSize(QSize(250, 250))
        self.clock_4.setIconSize(QSize(250, 250))

        self.clock_1.setFlat(True)
        self.clock_2.setFlat(True)
        self.clock_3.setFlat(True)
        self.clock_4.setFlat(True)

        self.clock_1.clicked.connect(self.add_clock)
        self.clock_2.clicked.connect(self.add_clock)
        self.clock_3.clicked.connect(self.add_clock)
        self.clock_4.clicked.connect(self.add_clock)

        self.clock_buttons = [self.clock_1,
                              self.clock_2,
                              self.clock_3,
                              self.clock_4]

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(993)

    def add_clock(self):
        self.name = self.sender().objectName()
        self.button = self.sender()
        self.add_clock_window = AddClock(self)
        self.add_clock_window.show()

    def update_time(self):
        hour, minute, second = self.current_time
        new_sec = (second + 1) % 60
        new_min = (minute + (second + 1) // 60) % 60
        new_hour = (hour + (minute + (second + 1) // 60) // 60) % 24
        self.current_time = [new_hour, new_min, new_sec]
        for clock in self.clocks:
            if clock is None:
                continue
            clock.update_clock()

    def delete_clock(self):
        num = self.sender().objectName()[-1]
        self.clocks[int(num) - 1] = None
        self.clock_layouts[num].replaceWidget(
                                            self.clock_layouts[num].itemAt(0).widget(),
                                            self.clock_buttons[int(num) - 1])
        self.clock_faces[num].setHidden(True)
        self.clock_buttons[int(num) - 1].setHidden(False)
        self.settings_clock_buttons[num].setHidden(True)
        self.delete_clock_buttons[num].setHidden(True)

    def clock_settings(self):
        self.clock_settings_window = ClockSettings(self, int(self.sender().objectName()[-1]))
        self.clock_settings_window.show()


    def alarm_clocks(self):
        self.alarm_clocks_window = AlarmClocks(self)
        self.alarm_clocks_window.showMaximized()


class AddClock(QWidget):
    def __init__(self, other):
        super().__init__()
        uic.loadUi('Ui/AddClock.ui', self)
        self.other = other

        self.Label_1.setHidden(True)
        self.Label_2.setHidden(True)

        self.cancel_button.clicked.connect(self.cancel)
        self.ok_button.clicked.connect(self.add_clock)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.close()
        elif key == 16777220:
            self.add_clock()

    def is_ok(self):
        if not self.AnalogRadioButton.isChecked() and not self.DigitRadioButton.isChecked():
            raise AddClockNotEverythingIsSelected(self)
        elif self.TimeZoneComboBox.currentText() == '...':
            raise AddClockNotEverythingIsSelected(self)
        return True

    def add_clock(self):
        num = self.other.name[-1]
        try:
            if self.is_ok():
                clock_type = 'analog' if self.AnalogRadioButton.isChecked() else 'digit'
                sign = self.TimeZoneComboBox.currentText()[3]
                timezone = self.TimeZoneComboBox.currentText()[3:].split(':')
                timezone = [int(timezone[0]), 0 if len(timezone) == 1 else int(sign + timezone[1])]
                self.other.clock_layouts[num].replaceWidget(
                                                          self.other.clock_layouts[num].itemAt(0).widget(),
                                                          self.other.clock_faces[self.other.name[-1]])
                self.other.button.setHidden(True)
                self.other.clock_faces[self.other.name[-1]].setHidden(False)
                self.other.settings_clock_buttons[self.other.name[-1]].setHidden(False)
                self.other.delete_clock_buttons[self.other.name[-1]].setHidden(False)
                self.other.clocks[int(num) - 1] = Clock(self.other, clock_type, timezone, num=num)
                self.close()
        except AddClockNotEverythingIsSelected:
            pass

    def cancel(self):
        self.close()


class MyButton(QPushButton):
    def __init__(self, text=''):
        super().__init__()
        self.setMouseTracking(True)
        self.setText(text)

    def enterEvent(self, event):
        QApplication.setOverrideCursor(Qt.PointingHandCursor)

    def leaveEvent(self, event):
        QApplication.restoreOverrideCursor()


class AlarmClocks(QWidget):
    def __init__(self, other):
        super().__init__()
        self.other = other
        uic.loadUi('Ui/AlarmClocksUi.ui', self)

        self.connection = sqlite3.connect('database/alarm_clocks.sqlite')
        self.cursor = self.connection.cursor()

        self.data = self.cursor.execute("""SELECT * from alarm_clocks""").fetchall()

        self.TableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.TableWidget.setColumnCount(7)
        self.TableWidget.setRowCount(len(self.data) + 1)

        self.TableWidget.setSpan(0, 5, 1, 2)

        self.TableWidget.horizontalHeader().setVisible(False)
        self.TableWidget.verticalHeader().setVisible(False)

        item = QTableWidgetItem('Название')
        item.setFlags(Qt.ItemIsEnabled)
        self.TableWidget.setItem(0, 0, item)
        item = QTableWidgetItem('Время')
        item.setFlags(Qt.ItemIsEnabled)
        self.TableWidget.setItem(0, 1, item)
        item = QTableWidgetItem('Повторять')
        item.setFlags(Qt.ItemIsEnabled)
        self.TableWidget.setItem(0, 2, item)
        item = QTableWidgetItem('Часовой пояс')
        item.setFlags(Qt.ItemIsEnabled)
        self.TableWidget.setItem(0, 3, item)
        item = QTableWidgetItem('Режим')
        item.setFlags(Qt.ItemIsEnabled)
        self.TableWidget.setItem(0, 4, item)

        button = MyButton('Добавить')
        button.setFlat(True)
        self.TableWidget.setCellWidget(0, 5, button)

        for num, elem in enumerate(self.data):
            btn_1, btn_2 = MyButton('Изменить'), MyButton('Удалить')
            btn_1.setFlat(True)
            btn_2.setFlat(True)
#            time = [int(elem[1].split(':')[0], int(elem[1].split(':')[1]))]
#            tz, sign = elem[3][3:].split(':'), '-' if elem[3][4] == '+' else '+'
#            timezone = [int(tz[0]), 0 if len(tz) == 1 else int(sign + tz[1])]
#            time[0] = (time[0] + timezone[0] + (time[1] + timezone[1]) // 60) % 24
#            time[1] = (time[1] + timezone[1]) % 60
            btn_1.setObjectName(f'ChangeButton{elem[5]}')
            btn_2.setObjectName(f'DeleteButton{elem[5]}')
            btn_1.clicked.connect(self.change_alarm_clocks)
            btn_2.clicked.connect(self.delete_alarm_clocks)
            self.TableWidget.setCellWidget(num + 1, 5, btn_1)
            self.TableWidget.setCellWidget(num + 1, 6, btn_2)
            for num_, elem_ in enumerate(elem[:5]):
                item = QTableWidgetItem(elem_)
                item.setFlags(Qt.ItemIsEnabled)
                self.TableWidget.setItem(num + 1, num_, item)

    def change_alarm_clocks(self):
        change_alarm_clock_window = ChangeAlarmClock()
        change_alarm_clock_window.show()

    def delete_alarm_clocks(self):
        name = self.sender().objectName()[12:]
        data = self.cursor.execute("""SELECT * FROM alarm_clocks
                                      WHERE 'UTC+0' = ?""", (name,)).fetchone()
        num = self.data.index(data)
        del self.data[num]
        self.TableWidget.removeRow(num)
        self.cursor.execute("DELETE from alarm_clocks WHERE 'UTC+0' = ?", (name,))
        self.connection.commit()


class ClockSettings(QWidget):
    def __init__(self, other, num):
        super().__init__()
        uic.loadUi('Ui/ClockSettingsUi.ui', self)

        self.CancelButton.clicked.connect(self.cancel)
        self.OkButton.clicked.connect(self.apply_changes)
        self.other, self.num = other, num - 1

    def apply_changes(self):
        type = 'analog' if self.AnalogRadioButton.isChecked() else 'digit'
        tz = self.TimeZoneComboBox.currentText()
        self.other.clocks[self.num].add_changes(type, tz)
        self.close()

    def cancel(self):
        self.close()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.close()
        elif key == 16777220:
            self.apply_changes()


class ChangeAlarmClock(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('Ui/ChangeAlarmClockUi.ui')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FirstWindow()
    ex.showMaximized()
    sys.exit(app.exec())