import math
import sqlite3
import sys

from PyQt5 import uic, QtGui
from PyQt5.QtCore import QTimer, Qt, QEvent, QSize, QPoint, QLine
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel
from PyQt5.QtWidgets import QWidget, QApplication, QAbstractButton, QMainWindow, QToolButton, QHBoxLayout, QGridLayout, \
    QScrollArea, QVBoxLayout, QTableWidgetItem, QTableWidget, QHeaderView, QInputDialog
from PyQt5.QtWidgets import QLineEdit, QCheckBox, QLabel, QPushButton, QPlainTextEdit
import requests
from PyQt5.uic.properties import QtCore, QtWidgets
from bs4 import BeautifulSoup
import datetime as dt


class Clock:
    def __init__(self, other, type, timezone, num, original_timezone, detail_coefficient=0, numbers=None, ):
        self.other, self.clock_type, self.timezone = other, type, timezone
        self.original_timezone = original_timezone
        self.detail_coefficient, self.num, self.numbers = detail_coefficient, num, numbers
        self.paint_is_allowed = False if type == 'digit' else True
        self.seconds_pos_1, self.seconds_pos_2 = 200, 200
        self.minutes_pos_1, self.minutes_pos_2 = 200, 200
        self.hours_pos_1, self.hours_pos_2 = 200, 200
        if self.clock_type == 'analog':
            if self.detail_coefficient == 0:
                self.pixmap = QPixmap('images/ClockFace_1.png')
            elif self.detail_coefficient == 1:
                self.pixmap = QPixmap('images/ClockFace_2.png')
            else:
                self.pixmap = QPixmap('images/ClockFace_3.png')
            self.other.clock_faces[self.num].setPixmap(self.pixmap)

    def add_changes(self, new_type, new_timezone):
        self.clock_type = new_type
        self.paint_is_allowed = False if new_type == 'digit' else True
        self.original_timezone = new_timezone
        sign = new_timezone[3]
        timezone = new_timezone[3:].split(':')
        self.timezone = [int(timezone[0]), 0 if len(timezone) == 1 else int(sign + timezone[1])]

    def update_clock(self):
        time = self.other.current_time
        self.time = [time[0], time[1], time[2]]
        self.time[0] = (time[0] + self.timezone[0] + (time[1] + self.timezone[1]) // 60) % 24
        self.time[1] = (time[1] + self.timezone[1]) % 60
        if self.clock_type == 'analog':
            self.update_analog()
        else:
            self.update_digit()

    def update_analog(self):
        clock_face_coordinates = self.other.clock_faces[self.num].mapToGlobal(QPoint(0, 0))
        self.clock_face_cord_x, self.clock_face_coord_y = clock_face_coordinates.x(), clock_face_coordinates.y()
        hours, minutes, seconds = self.time

        if self.detail_coefficient < 1:
            self.seconds_pos_1 = int(200 * self.other.coefficient_for_drawing - 130  * self.other.coefficient_for_drawing * math.cos((90 + 6 * seconds) * math.pi / 180))
            self.seconds_pos_2 = int(200 * self.other.coefficient_for_drawing - 130  * self.other.coefficient_for_drawing * math.sin((90 + 6 * seconds) * math.pi / 180))
        if self.detail_coefficient < 2:
            self.minutes_pos_1 = int(200  * self.other.coefficient_for_drawing - 110  * self.other.coefficient_for_drawing * math.cos((90 + 6 * minutes) * math.pi / 180))
            self.minutes_pos_2 = int(200 * self.other.coefficient_for_drawing - 110 * self.other.coefficient_for_drawing * math.sin((90 + 6 * minutes) * math.pi / 180))
        self.hours_pos_1 = int(200 * self.other.coefficient_for_drawing - 85 * self.other.coefficient_for_drawing * math.cos((90 + 30 * hours + minutes / 2) * math.pi / 180))
        self.hours_pos_2 = int(200 * self.other.coefficient_for_drawing - 85 * self.other.coefficient_for_drawing * math.sin((90 + 30 * hours + minutes / 2) * math.pi / 180))

    def update_digit(self):

        self.other.clock_faces[self.num].setText('digit ' + ':'.join(map(str, self.time)))


class AddClockNotEverythingIsSelected(Exception):
    def __init__(self, other):
        super().__init__()

        other.Label_1.setHidden(False)
        other.Label_2.setHidden(False)


class FirstWindow(QMainWindow):
    def __init__(self, desktop_size):
        super().__init__()
        uic.loadUi('Ui/MainWindowUi.ui', self)

        self.screen_size = desktop_size.width(), desktop_size.height()
        self.coefficient_for_drawing = (self.screen_size[0] // 4) / 400

#        response = requests.get('https://www.timeanddate.com/worldclock/timezone/utc')
#        soup = BeautifulSoup(response.text, 'html.parser')
#        time = map(int, str(soup.find("span", class_="h1", id="ct")).split('>')[1].split('<')[0].split(':'))
#        self.current_time = list(time)
        self.current_time = [0, 0, 0]

        self.analog_clock_face_1 = QPixmap('images/ClockFace_1.png')
        self.analog_clock_face_2 = QPixmap('images/ClockFace_2.png')
        self.analog_clock_face_3 = QPixmap('images/ClockFace_3.png')

        self.analog_clock_faces = [self.analog_clock_face_1,
                                   self.analog_clock_face_2,
                                   self.analog_clock_face_3]

        self.alarm_clock_button.clicked.connect(self.alarm_clocks)

        self.clocks = [None, None, None, None]
        self.clock_faces = {}

        self.clock_face_1 = QLabel(self)
        self.clock_face_1.resize(500, 500)
        self.clock_face_1.setHidden(True)

        self.clock_face_2 = QLabel(self)
        self.clock_face_2.resize(500, 500)
        self.clock_face_2.setHidden(True)

        self.clock_face_3 = QLabel(self)
        self.clock_face_3.resize(500, 500)
        self.clock_face_3.setHidden(True)

        self.clock_face_4 = QLabel(self)
        self.clock_face_4.resize(500, 500)
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

    def paintEvent(self, event):
        clock_hands_painter = QPainter()
        for clock in self.clocks:
            if clock is None:
                continue
            if clock.clock_type == 'analog':
                if clock.detail_coefficient == 0:
                    name = 'images/ClockFace_1'
                if clock.detail_coefficient == 1:
                    name = 'images/ClockFace_2'
                if clock.detail_coefficient == 2:
                    name = 'images/ClockFace_3'
                pixmap = QPixmap(name)
                pixmap = pixmap.scaled(QSize(int(400 * self.coefficient_for_drawing), int(400 * self.coefficient_for_drawing)))
                clock_hands_painter.begin(pixmap)
                self.draw_analog_clock(clock_hands_painter, clock)
                clock_hands_painter.end()
                self.clock_faces[clock.num].setPixmap(pixmap)

    def draw_analog_clock(self, clock_hands_painter, clock):
        clock_hands_painter.setPen(QPen(QColor(0, 0, 100), 4))
        clock_hands_painter.drawLine(int(200 * self.coefficient_for_drawing), int(200 * self.coefficient_for_drawing), clock.seconds_pos_1, clock.seconds_pos_2)
        clock_hands_painter.setPen(QPen(QColor(0, 0, 100), 6))
        clock_hands_painter.drawLine(int(200 * self.coefficient_for_drawing), int(200 * self.coefficient_for_drawing), clock.minutes_pos_1, clock.minutes_pos_2)
        clock_hands_painter.setPen(QPen(QColor(0, 0, 100), 8))
        clock_hands_painter.drawLine(int(200 * self.coefficient_for_drawing), int(200 * self.coefficient_for_drawing), clock.hours_pos_1, clock.hours_pos_2)


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
        end = False
        for clock in self.clocks:
            if clock is None:
                continue
            end = True
            clock.update_clock()
        if end:
            self.repaint()

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

        self.setWindowModality(Qt.ApplicationModal)

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
                original_timezone = self.TimeZoneComboBox.currentText()
                timezone = self.TimeZoneComboBox.currentText()[3:].split(':')
                timezone = [int(timezone[0]), 0 if len(timezone) == 1 else int(sign + timezone[1])]
                self.other.clock_layouts[num].replaceWidget(
                                                          self.other.clock_layouts[num].itemAt(0).widget(),
                                                          self.other.clock_faces[self.other.name[-1]])
                self.other.button.setHidden(True)
                self.other.clock_faces[self.other.name[-1]].setHidden(False)
                self.other.settings_clock_buttons[self.other.name[-1]].setHidden(False)
                self.other.delete_clock_buttons[self.other.name[-1]].setHidden(False)
                self.other.clocks[int(num) - 1] = Clock(self.other, clock_type, timezone, num, original_timezone)
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
        button.clicked.connect(self.add_alarm_clock)
        self.TableWidget.setCellWidget(0, 5, button)

        for num, elem in enumerate(self.data):
            btn_1, btn_2 = MyButton('Изменить'), MyButton('Удалить')
            btn_1.setFlat(True)
            btn_2.setFlat(True)
            btn_1.setObjectName(f'ChangeButton{elem[5]};{elem[3]}')
            btn_2.setObjectName(f'DeleteButton{elem[5]};{elem[3]}')
            btn_1.clicked.connect(self.change_alarm_clocks)
            btn_2.clicked.connect(self.delete_alarm_clocks)
            self.TableWidget.setCellWidget(num + 1, 5, btn_1)
            self.TableWidget.setCellWidget(num + 1, 6, btn_2)
            for num_, elem_ in enumerate(elem[:5]):
                item = QTableWidgetItem(elem_)
                item.setFlags(Qt.ItemIsEnabled)
                self.TableWidget.setItem(num + 1, num_, item)

    def add_alarm_clock(self):
        pass
        self.add_new_alarm_clock = AddNewAlarmClock(self)
        self.add_new_alarm_clock.show()

    def change_alarm_clocks(self):
        self.change_alarm_clock_window = ChangeAlarmClock()
        self.change_alarm_clock_window.show()

    def delete_alarm_clocks(self):
        self.answer = None
        name = self.sender().objectName()[12:].split(';')
        data = self.cursor.execute("""SELECT * FROM alarm_clocks
                                      WHERE universal_time = ? AND timezone = ?""", (name[0], name[1])).fetchone()
        self.dialog = DeleteDialog(self, data, name)
        self.dialog.show()


class ClockSettings(QWidget):
    def __init__(self, other, num):
        super().__init__()
        uic.loadUi('Ui/ClockSettingsUi.ui', self)

        self.setWindowModality(Qt.ApplicationModal)

        if other.clocks[num - 1].clock_type == 'analog':
            self.AnalogRadioButton.setChecked(True)
        else:
            self.DigitRadioButton.setChecked(True)

        index = self.TimeZoneComboBox.findText(other.clocks[num - 1].original_timezone, Qt.MatchFixedString)
        self.TimeZoneComboBox.setCurrentIndex(index)

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
        uic.loadUi('Ui/ChangeAlarmClockUi.ui', self)


class DeleteDialog(QWidget):
    def __init__(self, other, data, name):
        super().__init__()
        uic.loadUi('Ui/DeleteDialogUi.ui', self)
        self.setWindowModality(Qt.ApplicationModal)

        self.other, self.data, self.name = other, data, name

        self.NameLabel.setText(f'Вы действительно хотите удалить будильник {data[0]},')
        self.TimeLabel.setText(f'установленный на {data[1]}?')

        self.DeleteButton.clicked.connect(self.confirm)
        self.CancelButton.clicked.connect(self.cancel)

    def confirm(self):
        num = self.other.data.index(self.data)
        del self.other.data[num]
        self.other.TableWidget.removeRow(num + 1)
        self.other.cursor.execute("DELETE from alarm_clocks "
                                  "WHERE universal_time = ? AND timezone = ?", (self.name[0], self.name[1]))
        self.other.connection.commit()
        self.close()

    def cancel(self):
        self.close()


class AddNewAlarmClock(QWidget):
    def __init__(self, other):
        super().__init__()
        uic.loadUi('Ui/AddNewAlarmClockUi.ui', self)
        self.setWindowModality(Qt.ApplicationModal)
        self.other = other
        self.week_days = {'MondayCheckBox': 'пн',
                          'TuesdayCheckBox': 'вт',
                          'WednesdayCheckBox': 'ср',
                          'ThursdayCheckBox': 'чт',
                          'FridayCheckBox': 'пт',
                          'SaturdayCheckBox': 'сб',
                          'SundayCheckBox': 'вс'}

        self.AttentionLabel_1.setHidden(True)
        self.AttentionLabel_2.setHidden(True)

        self.SaveButton.clicked.connect(self.add_alarm_clock)
        self.CancelButton.clicked.connect(self.cancel)

    def cancel(self):
        self.close()

    def add_alarm_clock(self):
        try:
            if self.is_ok():
                pass
                self.check_boxes_help = [self.MondayCheckBox,
                                          self.TuesdayCheckBox,
                                          self.WednesdayCheckBox,
                                          self.ThursdayCheckBox,
                                          self.FridayCheckBox,
                                          self.SaturdayCheckBox,
                                          self.SundayCheckBox]
                self.check_boxes = []

                for check_box in self.check_boxes_help:
                    if check_box.isChecked():
                        self.check_boxes.append(check_box)

                if len(self.check_boxes) != 0:
                    self.check_boxes = map(lambda x: self.week_days[x.objectName()], self.check_boxes)
                    self.check_boxes = ', '.join(self.check_boxes)
                else:
                    self.check_boxes = 'Нет'

                values = (self.NameTextEdit.toPlainText(),
                          self.time,
                          self.check_boxes,
                          self.TimezoneComboBox.currentText(),
                          'Активен', self.universal_time)
                self.other.data.append(values)

                self.other.cursor.execute("""INSERT INTO alarm_clocks
                                             VALUES (?, ?, ?, ?, ?, ?)""", values)
                self.other.connection.commit()

                row_count = self.other.TableWidget.rowCount()
                self.other.TableWidget.insertRow(row_count)
                for num, value in enumerate(values[:5]):
                    item = QTableWidgetItem(value)
                    item.setFlags(Qt.ItemIsEnabled)
                    self.other.TableWidget.setItem(row_count, num, item)
                btn_1, btn_2 = MyButton('Изменить'), MyButton('Удалить')
                btn_1.setFlat(True)
                btn_2.setFlat(True)
                self.other.TableWidget.setCellWidget(row_count, 5, btn_1)
                self.other.TableWidget.setCellWidget(row_count, 6, btn_2)
                btn_1.setObjectName(f'ChangeButton{values[5]};{values[3]}')
                btn_2.setObjectName(f'DeleteButton{values[5]};{values[3]}')
                btn_1.clicked.connect(self.other.change_alarm_clocks)
                btn_2.clicked.connect(self.other.delete_alarm_clocks)
                self.close()

        except AddAlarmClockNotEverythingIsSelected:
            pass
        except AlarmClockAlreadyExistsException:
            self.setWindowModality(Qt.NonModal)
            self.alarm_clock_exists = AlarmClockAlreadyExists(self)
            self.alarm_clock_exists.show()


    def is_ok(self):
        if self.NameTextEdit.toPlainText() == '':
            raise AddAlarmClockNotEverythingIsSelected(self)
        elif self.TimezoneComboBox.currentText() == '...':
            raise AddAlarmClockNotEverythingIsSelected(self)
        timezone, universal_time = self.TimezoneComboBox.currentText()[3:], []
        sign = '-' if timezone[0] == '+' else '+'
        time = [int(self.HoursSpinBox.value()), int(self.MinutesSpinBox.value())]
        self.time = ':'.join(map(str, time))
        timezone = [int(sign + timezone.split(':')[0][1:]),
                    0 if len(timezone.split(':')) == 1 else int(sign + timezone.split(':')[1])]
        universal_time.append((time[0] + timezone[0] + (time[1] + timezone[1]) // 60) % 24)
        universal_time.append((time[1] + timezone[1]) % 60)
        self.universal_time = ':'.join(map(str, universal_time))
        if len(self.other.cursor.execute("""SELECT * from alarm_clocks
                                            WHERE timezone = ? AND universal_time = ?""", (self.TimezoneComboBox.currentText(), self.universal_time)).fetchall()):
            raise AlarmClockAlreadyExistsException(self)
        return True


class AddAlarmClockNotEverythingIsSelected(Exception):
    def __init__(self, other):
        super().__init__()
        other.AttentionLabel_1.setHidden(False)
        other.AttentionLabel_2.setHidden(False)


class AlarmClockAlreadyExistsException(Exception):
    def __init__(self, other):
        super().__init__()
        other.AttentionLabel_1.setHidden(True)
        other.AttentionLabel_2.setHidden(True)


class AlarmClockAlreadyExists(QWidget):
    def __init__(self, other):
        super().__init__()
        uic.loadUi('Ui/AlarmClockExistsUi.ui', self)
        self.other = other
        self.setWindowModality(Qt.ApplicationModal)
        self.OkButton.clicked.connect(self.confirm)

    def confirm(self):
        self.other.setWindowModality(Qt.ApplicationModal)
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    primary_screen = app.desktop().primaryScreen()
    desktop_size = app.desktop().screenGeometry(primary_screen).size()
    ex = FirstWindow(desktop_size)
    ex.showMaximized()
    sys.exit(app.exec())