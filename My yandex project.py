import math
import sqlite3
import sys

from pygame import mixer
from PyQt5 import uic, QtGui
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt5.QtWidgets import QWidget, QApplication, QAbstractButton, QMainWindow, QToolButton, QHBoxLayout, QGridLayout, \
    QScrollArea, QVBoxLayout, QTableWidgetItem, QTableWidget, QHeaderView, QInputDialog
from PyQt5.QtWidgets import QLineEdit, QCheckBox, QLabel, QPushButton, QPlainTextEdit
import requests
from PyQt5.uic.properties import QtCore, QtWidgets
from bs4 import BeautifulSoup


NAME = 'Циферблаты и будильники'
mixer.init()


class AlarmClockPlaying(QWidget):
    def __init__(self, name, time, other):
        super().__init__()
        uic.loadUi('Ui/AlarmClockPlayingUi.ui', self)
        self.time, self.other = time, other

        self.setWindowFlags(Qt.CustomizeWindowHint)

        self.setWindowModality(Qt.ApplicationModal)

        self.pixmap = QPixmap('images/Numbers/SimpleBackground.png')
        self.pixmap = self.pixmap.scaled(QSize(int(400 * other.coefficient_for_drawing * 6 / 7),
                                               int(400 * other.coefficient_for_drawing)))
        self.play = True

        self.NameLabel.setText(name)
        self.repaint()

        self.timer = QTimer()
        self.timer.singleShot(22000, self.stop_playing)

        self.play_timer = QTimer()
        self.play_timer.singleShot(11000, self.play_again)

        mixer.music.play()

        self.StopButton.clicked.connect(self.stop_playing)

    def paintEvent(self, event):
        clock_hands_painter = QPainter()
        clock_hands_painter.begin(self.pixmap)
        self.draw_current_time(clock_hands_painter)
        clock_hands_painter.end()
        self.CurrentTimeLabel.setPixmap(self.pixmap)

    def draw_current_time(self, clock_hands_painter):
        div = 0
        for num, number in enumerate(self.time):
            if num % 3 != 2:
                pixmap = self.other.pixmaps_for_drawing_digit[number]
                clock_hands_painter.drawPixmap(div,
                                               0,
                                               pixmap,
                                               0,
                                               0,
                                               self.other.number_for_drawing_3,
                                               self.other.number_for_drawing_2)
                div += int(400 * self.other.coefficient_for_drawing / 5)
            else:
                div -= self.other.number_for_drawing_5
                pixmap = self.other.pixmaps_for_drawing_digit[number]
                clock_hands_painter.drawPixmap(div,
                                               0,
                                               pixmap,
                                               0,
                                               0,
                                               self.other.number_for_drawing_3,
                                               self.other.number_for_drawing_2)
                div += self.other.number_for_drawing_5
                div += self.other.number_for_drawing_4

    def stop_playing(self):
        self.play = False
        mixer.music.stop()
        self.close()

    def play_again(self):
        if self.play:
            mixer.music.play()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.stop_playing()
        elif key == 16777220:
            self.stop_playing()


class Clock:
    def __init__(self, other, type, timezone, num, original_timezone, detail_coefficient=0, numbers=True, ):
        self.other, self.clock_type, self.timezone = other, type, timezone
        self.original_timezone, self.time = original_timezone, [0, 0, 0]
        self.detail_coefficient, self.num, self.numbers = detail_coefficient, num, numbers
        self.paint_is_allowed = False if type == 'digit' else True
        self.seconds_pos_1, self.seconds_pos_2 = 200, 200
        self.minutes_pos_1, self.minutes_pos_2 = 200, 200
        self.hours_pos_1, self.hours_pos_2 = 200, 200

        self.number_for_drawing_analog_1 = 200 * self.other.coefficient_for_drawing
        self.number_for_drawing_analog_2 = 130 * self.other.coefficient_for_drawing
        self.number_for_drawing_analog_3 = 110 * self.other.coefficient_for_drawing
        self.number_for_drawing_analog_4 = 85 * self.other.coefficient_for_drawing

        if self.clock_type == 'analog':
            name = ''
            if self.detail_coefficient == 0:
                name = 'images/ClockFace_1'
            elif self.detail_coefficient == 1:
                name = 'images/ClockFace_2'
            else:
                name = 'images/ClockFace_3'
            if numbers:
                name += '_nums'
            name += '.png'
            self.pixmap = QPixmap(name)
            self.pixmap.scaled(QSize(self.other.number_for_drawing_2,
                                     self.other.number_for_drawing_2))
            self.other.clock_faces[self.num].setPixmap(self.pixmap)
        else:
            self.pixmap = QPixmap('images/Numbers/SimpleBackground.png')
            self.pixmap.scaled(QSize(self.other.number_for_drawing_2,
                                     self.other.number_for_drawing_2))

    def add_changes(self, new_type, new_timezone, detail_coefficient, numbers):
        self.clock_type = new_type
        self.detail_coefficient, self.numbers = detail_coefficient, numbers
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

    def update_analog(self):
        hours, minutes, seconds = self.time

        self.seconds_pos_1 = int(self.number_for_drawing_analog_1 - self.number_for_drawing_analog_2
                                 * math.cos((90 + 6 * seconds) * math.pi / 180))

        self.seconds_pos_2 = int(self.number_for_drawing_analog_1 - self.number_for_drawing_analog_2
                                 * math.sin((90 + 6 * seconds) * math.pi / 180))

        self.minutes_pos_1 = int(self.number_for_drawing_analog_1 - self.number_for_drawing_analog_3
                                 * math.cos((90 + 6 * minutes) * math.pi / 180))

        self.minutes_pos_2 = int(self.number_for_drawing_analog_1 - self.number_for_drawing_analog_3
                                 * math.sin((90 + 6 * minutes) * math.pi / 180))

        self.hours_pos_1 = int(self.number_for_drawing_analog_1 - self.number_for_drawing_analog_4 *
                               math.cos((90 + 30 * hours + minutes / 2) * math.pi / 180))

        self.hours_pos_2 = int(self.number_for_drawing_analog_1 - self.number_for_drawing_analog_4 *
                               math.sin((90 + 30 * hours + minutes / 2) * math.pi / 180))


class AddClockNotEverythingIsSelected(Exception):
    def __init__(self, other):
        super().__init__()

        other.Label_1.setHidden(False)
        other.Label_2.setHidden(False)


class FirstWindow(QMainWindow):
    def __init__(self, desktop_size):
        super().__init__()
        uic.loadUi('Ui/MainWindowUi.ui', self)

        mixer.music.load('sounds/AlarmClockSound.mp3')

        self.setWindowTitle(NAME)

        self.screen_size = desktop_size.width(), desktop_size.height()
        self.coefficient_for_drawing = (self.screen_size[0] // 4) / 480

        self.number_for_drawing_1 = int(200 * self.coefficient_for_drawing)
        self.number_for_drawing_2 = int(400 * self.coefficient_for_drawing)
        self.number_for_drawing_3 = int(400 * self.coefficient_for_drawing / 7)
        self.number_for_drawing_4 = int(400 * self.coefficient_for_drawing / 14)
        self.number_for_drawing_5 = int(400 * self.coefficient_for_drawing / 28)

        try:
            response = requests.get('https://www.timeanddate.com/worldclock/timezone/utc')
            soup = BeautifulSoup(response.text, 'html.parser')
            time = map(int, str(soup.find("span", class_="h1", id="ct")).split('>')[1].split('<')[0].split(':'))
            self.current_time = list(time)
        except requests.ConnectionError:
            self.current_time = [0, 0, 0]

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

        self.Delete_clock_1.setIcon(QtGui.QIcon('images/TrashBin.png'))
        self.Delete_clock_2.setIcon(QtGui.QIcon('images/TrashBin.png'))
        self.Delete_clock_3.setIcon(QtGui.QIcon('images/TrashBin.png'))
        self.Delete_clock_4.setIcon(QtGui.QIcon('images/TrashBin.png'))

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

        self.Delete_clock_1.setIconSize(QSize(30, 30))
        self.Delete_clock_2.setIconSize(QSize(30, 30))
        self.Delete_clock_3.setIconSize(QSize(30, 30))
        self.Delete_clock_4.setIconSize(QSize(30, 30))

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

        self.pixmaps_for_drawing_digit = {'0': QPixmap('images/Numbers/Number_0.png'),
                                          '1': QPixmap('images/Numbers/Number_1.png'),
                                          '2': QPixmap('images/Numbers/Number_2.png'),
                                          '3': QPixmap('images/Numbers/Number_3.png'),
                                          '4': QPixmap('images/Numbers/Number_4.png'),
                                          '5': QPixmap('images/Numbers/Number_5.png'),
                                          '6': QPixmap('images/Numbers/Number_6.png'),
                                          '7': QPixmap('images/Numbers/Number_7.png'),
                                          '8': QPixmap('images/Numbers/Number_8.png'),
                                          '9': QPixmap('images/Numbers/Number_9.png'),
                                          ':': QPixmap('images/Numbers/NumberDoubleDot.png')}
        for pixmap in self.pixmaps_for_drawing_digit.keys():
            self.pixmaps_for_drawing_digit[pixmap] = self.pixmaps_for_drawing_digit[pixmap].scaled(QSize(
                self.number_for_drawing_3, self.number_for_drawing_2))

        self.connection = sqlite3.connect('database/alarm_clocks.sqlite')
        self.cursor = self.connection.cursor()

        self.alarm_clocks_check()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(990)

        self.timer_time_check = QTimer()
        self.timer_time_check.timeout.connect(self.time_check)
        self.timer_time_check.start(120000)

        self.timer_alarm_clock_check = QTimer()
        self.timer_alarm_clock_check.timeout.connect(self.alarm_clocks_check)
        self.timer_alarm_clock_check.start(600000)

    def time_check(self):
        try:
            response = requests.get('https://www.timeanddate.com/worldclock/timezone/utc')
            soup = BeautifulSoup(response.text, 'html.parser')
            time = map(int, str(soup.find("span", class_="h1", id="ct")).split('>')[1].split('<')[0].split(':'))
            self.current_time = list(time)
        except requests.ConnectionError:
            pass

    def alarm_clocks_check(self):
        time = self.current_time[0], self.current_time[1]
        for i in range(10):
            time_1 = str((time[0] + (time[1] + i) // 60) % 24).rjust(2, '0')
            time_2 = str((time[1] + i) % 60).rjust(2, '0')
            time_to_check = ':'.join([time_1, time_2])
            data = self.cursor.execute("""SELECT name, universal_time FROM alarm_clocks
                                          WHERE universal_time = ?""", (time_to_check,)).fetchall()
            if len(data) == 1:
                alarm_clock_time = list(map(int, data[0][1].split(':')))
                if alarm_clock_time[1] - time[1] >= 0:
                    check_time = alarm_clock_time[1] - time[1]
                else:
                    check_time = alarm_clock_time[1] - time[1] + 60
                timer = QTimer()
                if check_time != 0:
                    timer.singleShot(check_time * 60000 - (self.current_time[2] - 3) * 1000, self.play_alarm_clock)
                else:
                    timer.singleShot(check_time * 60000, self.play_alarm_clock)

    def play_alarm_clock(self):
        arguement = str(self.current_time[0]).rjust(2, '0') + ':' + str(self.current_time[1]).rjust(2, '0')
        data = self.cursor.execute("""SELECT name, time from alarm_clocks
                                      WHERE universal_time = ?""", (arguement,)).fetchall()
        if len(data) == 1:
            self.alarm_clock_playing_widget = AlarmClockPlaying(data[0][0], data[0][1], self)
            self.alarm_clock_playing_widget.show()

    def paintEvent(self, event):
        clock_hands_painter = QPainter()
        for clock in self.clocks:
            if clock is None:
                continue
            if clock.clock_type == 'analog':
                if clock.detail_coefficient == 0:
                    name = 'images/ClockFace_1'
                elif clock.detail_coefficient == 1:
                    name = 'images/ClockFace_2'
                else:
                    name = 'images/ClockFace_3'
                if clock.numbers:
                    name += '_nums'
                name += '.png'
                pixmap = QPixmap(name)
                pixmap = pixmap.scaled(QSize(self.number_for_drawing_2,
                                             self.number_for_drawing_2))
                clock_hands_painter.begin(pixmap)
                self.draw_analog_clock(clock_hands_painter, clock)
                clock_hands_painter.end()
                self.clock_faces[clock.num].setPixmap(pixmap)
            else:
                pixmap = QPixmap('images/Numbers/SimpleBackground.png')
                pixmap = pixmap.scaled(QSize(self.number_for_drawing_2,
                                             self.number_for_drawing_2))
                clock_hands_painter.begin(pixmap)
                self.draw_digit_clock(clock_hands_painter, clock)
                clock_hands_painter.end()
                self.clock_faces[clock.num].setPixmap(pixmap)

    def draw_analog_clock(self, clock_hands_painter, clock):
        clock_hands_painter.setPen(QPen(QColor(0, 0, 100), 4))
        clock_hands_painter.drawLine(self.number_for_drawing_1, self.number_for_drawing_1,
                                     clock.seconds_pos_1, clock.seconds_pos_2)
        clock_hands_painter.setPen(QPen(QColor(0, 0, 100), 6))
        clock_hands_painter.drawLine(self.number_for_drawing_1, self.number_for_drawing_1,
                                     clock.minutes_pos_1, clock.minutes_pos_2)
        clock_hands_painter.setPen(QPen(QColor(0, 0, 100), 8))
        clock_hands_painter.drawLine(self.number_for_drawing_1, self.number_for_drawing_1,
                                     clock.hours_pos_1, clock.hours_pos_2)

    def draw_digit_clock(self, clock_hands_painter, clock):
        time = clock.time
        numbers = []
        for part in time:
            numbers.append(str(part).rjust(2, '0'))
        numbers = ':'.join(numbers)
        div = 0
        for num, number in enumerate(numbers):
            if num % 3 != 2:
                pixmap = self.pixmaps_for_drawing_digit[number]
                clock_hands_painter.drawPixmap(div,
                                               0,
                                               pixmap,
                                               0,
                                               0,
                                               self.number_for_drawing_3,
                                               self.number_for_drawing_2)
                div += self.number_for_drawing_3
            else:
                div -= self.number_for_drawing_5
                pixmap = self.pixmaps_for_drawing_digit[number]
                clock_hands_painter.drawPixmap(div,
                                               0,
                                               pixmap,
                                               0,
                                               0,
                                               self.number_for_drawing_3,
                                               self.number_for_drawing_2)
                div += self.number_for_drawing_5
                div += self.number_for_drawing_4

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

    def alarm_clock_added(self, time):
        difference = [int(time.split(':')[0]) - self.current_time[0], int(time.split(':')[1]) - self.current_time[1]]
        if difference[0] == 1 and difference[1] + 60 <= 9:
            if difference[1] + 60 <= 9:
                timer = QTimer()
                timer.singleShot((difference[1] + 60) * 60000 - (self.current_time[2] - 3) * 1000,
                                 self.play_alarm_clock)
        elif difference[0] % 24 == 0 and difference[1] in range(10):
            timer = QTimer()
            if difference[1] != 0:
                timer.singleShot(difference[1] * 60000 - (self.current_time[2] - 3) * 1000, self.play_alarm_clock)
            else:
                timer.singleShot(difference[1] * 60000, self.play_alarm_clock)


class AddClock(QWidget):
    def __init__(self, other):
        super().__init__()
        uic.loadUi('Ui/AddClock.ui', self)
        self.other = other

        self.setWindowTitle(NAME)
        self.setWindowModality(Qt.ApplicationModal)

        self.NumbersAreNeededCheckBox.setChecked(True)
        self.NumbersAreNeededCheckBox.setHidden(True)

        self.pixmap_1 = QPixmap('images/ClockFace_1.png')
        self.pixmap_2 = QPixmap('images/ClockFace_2.png')
        self.pixmap_3 = QPixmap('images/ClockFace_3.png')
        self.pixmap_1.scaled(QSize(300, 300))
        self.pixmap_2.scaled(QSize(300, 300))
        self.pixmap_3.scaled(QSize(300, 300))
        self.ClockFaceLabel_1.setPixmap(self.pixmap_1)
        self.ClockFaceLabel_2.setPixmap(self.pixmap_2)
        self.ClockFaceLabel_3.setPixmap(self.pixmap_3)
        self.ClockFaceLabel_1.setHidden(True)
        self.ClockFaceLabel_2.setHidden(True)
        self.ClockFaceLabel_3.setHidden(True)
        self.CoefficientRadioButton_1.setHidden(True)
        self.CoefficientRadioButton_2.setHidden(True)
        self.CoefficientRadioButton_3.setHidden(True)

        self.AnalogRadioButton.clicked.connect(self.change_variants)
        self.DigitRadioButton.clicked.connect(self.change_variants)

        self.CoefficientRadioButton_1.setChecked(True)

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
                if self.CoefficientRadioButton_1.isChecked():
                    coefficient = 0
                elif self.CoefficientRadioButton_2.isChecked():
                    coefficient = 1
                else:
                    coefficient = 2
                self.other.clocks[int(num) - 1] = Clock(self.other, clock_type, timezone, num, original_timezone,
                                                        coefficient, self.NumbersAreNeededCheckBox.isChecked())
                self.close()
        except AddClockNotEverythingIsSelected:
            pass

    def change_variants(self):
        if self.sender().objectName()[0] == 'A':
            self.ClockFaceLabel_1.setHidden(False)
            self.ClockFaceLabel_2.setHidden(False)
            self.ClockFaceLabel_3.setHidden(False)
            self.CoefficientRadioButton_1.setHidden(False)
            self.CoefficientRadioButton_2.setHidden(False)
            self.CoefficientRadioButton_3.setHidden(False)
            self.NumbersAreNeededCheckBox.setHidden(False)
        else:
            self.ClockFaceLabel_1.setHidden(True)
            self.ClockFaceLabel_2.setHidden(True)
            self.ClockFaceLabel_3.setHidden(True)
            self.CoefficientRadioButton_1.setHidden(True)
            self.CoefficientRadioButton_2.setHidden(True)
            self.CoefficientRadioButton_3.setHidden(True)
            self.NumbersAreNeededCheckBox.setHidden(True)

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
        self.setWindowTitle(NAME)

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
        self.add_new_alarm_clock = AddNewAlarmClock(self)
        self.add_new_alarm_clock.show()

    def change_alarm_clocks(self):
        self.change_alarm_clock_window = AlarmClockSettings(self, self.sender())
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

        self.setWindowTitle(NAME)
        self.setWindowModality(Qt.ApplicationModal)

        self.pixmap_1 = QPixmap('images/ClockFace_1.png')
        self.pixmap_2 = QPixmap('images/ClockFace_2.png')
        self.pixmap_3 = QPixmap('images/ClockFace_3.png')
        self.pixmap_1.scaled(QSize(other.number_for_drawing_2, other.number_for_drawing_2))
        self.pixmap_2.scaled(QSize(other.number_for_drawing_2, other.number_for_drawing_2))
        self.pixmap_3.scaled(QSize(other.number_for_drawing_2, other.number_for_drawing_2))
        self.ClockFaceLabel_1.setPixmap(self.pixmap_1)
        self.ClockFaceLabel_2.setPixmap(self.pixmap_2)
        self.ClockFaceLabel_3.setPixmap(self.pixmap_3)

        if other.clocks[num - 1].detail_coefficient == 0:
            self.CoefficientRadioButton_1.setChecked(True)
        elif other.clocks[num - 1].detail_coefficient == 1:
            self.CoefficientRadioButton_2.setChecked(True)
        else:
            self.CoefficientRadioButton_3.setChecked(True)

        if other.clocks[num - 1].numbers:
            self.NumbersAreNeededCheckBox.setChecked(True)

        self.AnalogRadioButton.clicked.connect(self.change_variants)
        self.DigitRadioButton.clicked.connect(self.change_variants)

        if other.clocks[num - 1].clock_type == 'analog':
            self.AnalogRadioButton.setChecked(True)
        else:
            self.CoefficientRadioButton_1.setHidden(True)
            self.CoefficientRadioButton_2.setHidden(True)
            self.CoefficientRadioButton_3.setHidden(True)
            self.ClockFaceLabel_1.setHidden(True)
            self.ClockFaceLabel_2.setHidden(True)
            self.ClockFaceLabel_3.setHidden(True)
            self.DigitRadioButton.setChecked(True)
            self.NumbersAreNeededCheckBox.setHidden(True)

        index = self.TimeZoneComboBox.findText(other.clocks[num - 1].original_timezone, Qt.MatchFixedString)
        self.TimeZoneComboBox.setCurrentIndex(index)

        self.CancelButton.clicked.connect(self.cancel)
        self.OkButton.clicked.connect(self.apply_changes)
        self.other, self.num = other, num - 1

    def change_variants(self):
        if self.sender().objectName()[0] == 'A':
            self.ClockFaceLabel_1.setHidden(False)
            self.ClockFaceLabel_2.setHidden(False)
            self.ClockFaceLabel_3.setHidden(False)
            self.CoefficientRadioButton_1.setHidden(False)
            self.CoefficientRadioButton_2.setHidden(False)
            self.CoefficientRadioButton_3.setHidden(False)
            self.NumbersAreNeededCheckBox.setHidden(False)
        else:
            self.ClockFaceLabel_1.setHidden(True)
            self.ClockFaceLabel_2.setHidden(True)
            self.ClockFaceLabel_3.setHidden(True)
            self.CoefficientRadioButton_1.setHidden(True)
            self.CoefficientRadioButton_2.setHidden(True)
            self.CoefficientRadioButton_3.setHidden(True)
            self.NumbersAreNeededCheckBox.setHidden(True)

    def apply_changes(self):
        type = 'analog' if self.AnalogRadioButton.isChecked() else 'digit'
        tz = self.TimeZoneComboBox.currentText()
        if self.CoefficientRadioButton_1.isChecked():
            coefficient = 0
        elif self.CoefficientRadioButton_2.isChecked():
            coefficient = 1
        else:
            coefficient = 2
        self.other.clocks[self.num].add_changes(type, tz, coefficient, self.NumbersAreNeededCheckBox.isChecked())
        self.close()

    def cancel(self):
        self.close()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.close()
        elif key == 16777220:
            self.apply_changes()


class AlarmClockSettings(QWidget):
    def __init__(self, other, sender):
        super().__init__()
        uic.loadUi('Ui/AlarmClockSettingsUi.ui', self)
        self.setWindowTitle(NAME)
        self.other, self.sender = other, sender

        name = sender.objectName()[12:].split(';')
        self.name = name
        self.alarm_clock = other.cursor.execute("""SELECT * from alarm_clocks
                                                   WHERE universal_time = ? AND timezone = ?""", (name[0], name[1])).fetchone()

        repeat = self.alarm_clock[2].split(', ')
        self.check_boxes = {'пн': self.MondayCheckBox,
                            'вт': self.TuesdayCheckBox,
                            'ср': self.WednesdayCheckBox,
                            'чт': self.ThursdayCheckBox,
                            'пт': self.FridayCheckBox,
                            'сб': self.SaturdayCheckBox,
                            'вс': self.SundayCheckBox,
                            'Нет': None}

        for repeat_day in repeat:
            if self.check_boxes[repeat_day] is not None:
                self.check_boxes[repeat_day].setChecked(True)

        self.NameTextEdit.setPlainText(self.alarm_clock[0])
        index = self.TimezoneComboBox.findText(name[1], Qt.MatchFixedString)
        self.TimezoneComboBox.setCurrentIndex(index)
        self.HoursSpinBox.setValue(int(self.alarm_clock[1].split(':')[0]))
        self.MinutesSpinBox.setValue(int(self.alarm_clock[1].split(':')[1]))

        self.SaveButton.clicked.connect(self.apply_changes)
        self.CancelButton.clicked.connect(self.cancel)

    def cancel(self):
        self.close()

    def apply_changes(self):
        num = self.other.data.index(self.alarm_clock) + 1
        name = self.NameTextEdit.toPlainText()
        if name == '':
            name = 'Будильник'
        time = str(self.HoursSpinBox.value()).rjust(2, '0') + ':' + str(self.MinutesSpinBox.value()).rjust(2, '0')
        repeat_days = []
        for repeat_day in self.check_boxes.keys():
            if repeat_day != 'Нет':
                if self.check_boxes[repeat_day].isChecked():
                    repeat_days.append(repeat_day)
        if len(repeat_days) != 0:
             repeat_days = ', '.join(repeat_days)
        else:
            repeat_days = 'Нет'
        timezone = self.TimezoneComboBox.currentText()
        sign = '-' if timezone[3:][0] == '+' else '+'
        time_zone = timezone[4:].split(':')
        tz = [0, 0]
        tz[0] = int(sign + time_zone[0])
        tz[1] = 0 if len(time_zone) == 1 else int(sign + time_zone[1])
        mode = 'Активен'
        universal_time = list()
        universal_time.append(str((self.HoursSpinBox.value() + tz[0] + (self.MinutesSpinBox.value() +
                                                                        tz[1]) // 60) % 24).rjust(2, '0'))
        universal_time.append(str((self.MinutesSpinBox.value() + tz[1]) % 60).rjust(2, '0'))
        universal_time = ':'.join(map(str, universal_time))
        try:
            if self.is_ok(universal_time):
                values = (name, time, repeat_days, timezone, mode, universal_time, self.name[1], self.name[0])
                self.other.cursor.execute("""UPDATE alarm_clocks
                                             SET name = ?, time = ?, repeat = ?, timezone = ?, mode = ?, universal_time = ?
                                             WHERE timezone = ? AND universal_time = ?""", values)
                self.other.connection.commit()
                for i in range(5):
                    item = QTableWidgetItem(values[i])
                    item.setFlags(Qt.ItemIsEnabled)
                    self.other.TableWidget.setItem(num, i, item)
                self.other.TableWidget.cellWidget(num, 5).setObjectName(f'ChangeButton{universal_time};{timezone}')
                self.other.TableWidget.cellWidget(num, 6).setObjectName(f'DeleteButton{universal_time};{timezone}')
                self.other.data[num - 1] = (name, time, repeat_days, timezone, mode, universal_time)
                if time != self.alarm_clock[1]:
                    self.other.other.alarm_clock_added(universal_time)
                self.close()
        except AlarmClockAlreadyExistsException:
            self.setWindowModality(Qt.NonModal)
            self.announcement = AlarmClockAlreadyExists(self)
            self.announcement.show()

    def is_ok(self, time):
        data = self.other.cursor.execute("""SELECT * from alarm_clocks
                                            WHERE universal_time = ?""", (time,)).fetchall()
        if len(data) == 0 or time == self.alarm_clock[5]:
            return True
        raise AlarmClockAlreadyExistsException

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.close()
        elif key == 16777220:
            self.apply_changes()

class DeleteDialog(QWidget):
    def __init__(self, other, data, name):
        super().__init__()
        uic.loadUi('Ui/DeleteDialogUi.ui', self)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle(NAME)

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

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.close()
        elif key == 16777220:
            self.confirm()


class AddNewAlarmClock(QWidget):
    def __init__(self, other):
        super().__init__()
        uic.loadUi('Ui/AddNewAlarmClockUi.ui', self)
        self.setWindowTitle(NAME)
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
                self.other.other.alarm_clock_added(self.universal_time)
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
        self.time = ':'.join([str(time[0]).rjust(2, '0'), str(time[1]).rjust(2, '0')])
        timezone = [int(sign + timezone.split(':')[0][1:]),
                    0 if len(timezone.split(':')) == 1 else int(sign + timezone.split(':')[1])]
        universal_time.append((time[0] + timezone[0] + (time[1] + timezone[1]) // 60) % 24)
        universal_time.append((time[1] + timezone[1]) % 60)
        self.universal_time = str(universal_time[0]).rjust(2, '0') + ':' + str(universal_time[1]).rjust(2, '0')
        if len(self.other.cursor.execute("""SELECT * from alarm_clocks
                                            WHERE universal_time = ?""", (self.universal_time,)).fetchall()):
            raise AlarmClockAlreadyExistsException(self)
        return True

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.close()
        elif key == 16777220:
            self.add_alarm_clock()


class AddAlarmClockNotEverythingIsSelected(Exception):
    def __init__(self, other=None):
        super().__init__()
        if other is not None:
            other.AttentionLabel_1.setHidden(False)
            other.AttentionLabel_2.setHidden(False)


class AlarmClockAlreadyExistsException(Exception):
    def __init__(self, other=None):
        super().__init__()
        if other is not None:
            other.AttentionLabel_1.setHidden(True)
            other.AttentionLabel_2.setHidden(True)


class AlarmClockAlreadyExists(QWidget):
    def __init__(self, other):
        super().__init__()
        uic.loadUi('Ui/AlarmClockExistsUi.ui', self)
        self.setWindowTitle(NAME)
        self.other = other
        self.setWindowModality(Qt.ApplicationModal)
        self.OkButton.clicked.connect(self.confirm)

    def confirm(self):
        self.other.setWindowModality(Qt.ApplicationModal)
        self.close()

    def keyPressEvent(self, event):
        key = event.key()
        if key == 16777220:
            self.confirm()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    primary_screen = app.desktop().primaryScreen()
    desktop_size = app.desktop().screenGeometry(primary_screen).size()
    ex = FirstWindow(desktop_size)
    ex.showMaximized()
    sys.exit(app.exec())
