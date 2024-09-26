import datetime
import json
import sys
import stopit
import threading
import sqlite3
import os
import websocket
import pyglet

from PyQt5 import uic
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidgetItem, QMessageBox, QInputDialog, QComboBox, \
    QCompleter, QVBoxLayout, QWidget, QPushButton


class Futures(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Приветствие')
        self.setGeometry(100, 100, 400, 200)
        self.setFixedSize(400, 200)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        self.combo_box1 = QComboBox(self)
        self.combo_box2 = QComboBox(self)
        self.button = QPushButton('Применить', self)
        self.button.setEnabled(True)

        self.futures = ["btcusdt", "ethusdt", "bchusdt", "eosusdt", "ltcusdt", "trxusdt", "etcusdt",
                        "linkusdt", "xlmusdt", "adausdt", "xmrusdt", "dashusdt", "zecusdt", "xtzusdt", "bnbusdt",
                        "atomusdt",
                        "outusdt", "iotausdt", "batusdt", "vetusdt", "neousdt",
                        'qtumusdt', 'iostusdt']

        self.combo_box1.setEditable(True)
        self.combo_box2.setEditable(True)

        layout.addWidget(self.combo_box1)
        layout.addWidget(self.combo_box2)
        layout.addWidget(self.button)

        self.combo_box1.addItems(self.futures)
        self.combo_box2.addItems(self.futures)

        completer = QCompleter(self.futures, self.combo_box1)
        completer.setCaseSensitivity(0)
        self.combo_box1.setCompleter(completer)

        completer = QCompleter(self.futures, self.combo_box2)
        completer.setCaseSensitivity(0)
        self.combo_box2.setCompleter(completer)

        central_widget.setLayout(layout)

        self.button.clicked.connect(self.start)

    def start(self):
        if self.combo_box1.currentText() not in self.futures or self.combo_box2.currentText() not in self.futures:
            mesege = QMessageBox()
            mesege.setWindowTitle('Предупреждением')
            mesege.setText('Вы ввели неправильное значение фьчерсов или оно пустое!')
            mesege.setIcon(QMessageBox.Warning)
            mesege.setStandardButtons(QMessageBox.Ok)
            mesege.exec()

        if self.combo_box1.currentText() == self.combo_box2.currentText():
            mesege = QMessageBox()
            mesege.setWindowTitle('Ошибка')
            mesege.setText('Вы ввели одинаковые название фьючерсов!')
            mesege.setIcon(QMessageBox.Critical)
            mesege.setStandardButtons(QMessageBox.Ok)
            mesege.exec()

        else:
            reply = QMessageBox.question(self, 'Подтверждение',
                                         'Вы хотите загрузить ваши старые будильники?(Если вы их не создавали то просто'
                                         ' нажмите "No")',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                if os.path.isfile('database.db'):
                    Project(self.combo_box1.currentText(), self.combo_box2.currentText()).show()
                    self.close()
                else:
                    conn = sqlite3.connect('database.db')
                    cursor = conn.cursor()
                    cursor.execute('''CREATE TABLE alarms (
                        id    INTEGER PRIMARY KEY ASC AUTOINCREMENT
                                      UNIQUE,
                        price TEXT    UNIQUE
                    );
                    ''')

                    cursor.execute('''CREATE TABLE futurs (
                        id          INTEGER PRIMARY KEY ASC AUTOINCREMENT
                                            UNIQUE,
                        futurs_name TEXT    UNIQUE,
                        futurs_id   TEXT    
                    ); ''')

                    conn.commit()
                    conn.close()
                    Project(self.combo_box1.currentText(), self.combo_box2.currentText()).show()
                    self.close()

            else:
                if os.path.isfile('database.db'):
                    Project(self.combo_box1.currentText(), self.combo_box2.currentText(), yes=True).show()
                    self.close()
                else:
                    conn = sqlite3.connect('database.db')
                    cursor = conn.cursor()
                    cursor.execute('''CREATE TABLE alarms (
        id    INTEGER PRIMARY KEY ASC AUTOINCREMENT
                      UNIQUE,
        price TEXT    UNIQUE
    );
    ''')

                    cursor.execute('''CREATE TABLE futurs (
        id          INTEGER PRIMARY KEY ASC AUTOINCREMENT
                            UNIQUE,
        futurs_name TEXT    UNIQUE,
        futurs_id   TEXT    
    ); ''')
                    conn.commit()
                    conn.close()
                    Project(self.combo_box1.currentText(), self.combo_box2.currentText()).show()
                    self.close()


class Project(QMainWindow):
    def __init__(self, coin1, coin2, yes=False):
        super().__init__()
        uic.loadUi('release.ui', self)

        self.coin1 = coin1
        self.coin2 = coin2

        self.label.setPixmap(QIcon(
            'alarm.png').pixmap(
            QSize(100, 50)))

        self.label_2.setPixmap(QIcon(
            'alarm.png').pixmap(
            QSize(100, 50)))

        # Срабатывает, если пользователь согласился вернуть старые будильники?
        if yes:
            self.yes_method()
        self.Test_2.clicked.connect(self.text1)

        if coin1 not in Futures().futures:
            self.add_alaem.setEnabled(False)

        if coin2 not in Futures().futures:
            self.add_alaem1.setEnabled(False)

        # Монета 1
        self.segnel = self.latest_coin_price_1.model()
        self.segnel.rowsInserted.connect(self.work_an_alarms)
        self.alarms.itemDoubleClicked.connect(self.doubleClicked_alarm)
        self.add_alaem.clicked.connect(self.add_alaemer)

        # Монета 2
        self.segnel_1 = self.latest_coin_price_3.model()
        self.segnel_1.rowsInserted.connect(self.work_an_alarms1)
        self.alarms_1.itemDoubleClicked.connect(self.doubleClicked_alarm1)
        self.add_alaem1.clicked.connect(self.add_alaemer)

        self.thread = threading.Thread(target=Socket,
                                       args=(f'wss://fstream.binance.com:443/ws/{coin1}@aggTrade', self,))

        self.thread1 = threading.Thread(target=Socket1,
                                        args=(f'wss://fstream.binance.com:443/ws/{coin2}@aggTrade', self))

        self.thread.start()
        self.thread1.start()

    def add_alaemer(self):
        text, ok = QInputDialog.getText(self, "Добавить будильник?", "Введите значение:")
        try:
            if self.sender() == self.add_alaem:
                if ok and float(text):
                    text = str(text)
                    checkbox_item = QListWidgetItem(text)
                    checkbox_item.setCheckState(2)
                    self.alarms.addItem(checkbox_item)
            else:
                if ok and float(text):
                    text = str(text)
                    checkbox_item = QListWidgetItem(text)
                    checkbox_item.setCheckState(2)
                    self.alarms_1.addItem(checkbox_item)
        except ValueError:
            mesege = QMessageBox()
            mesege.setWindowTitle('Ошибка')
            mesege.setText('Вы ввели неправильное значение')
            mesege.setIcon(QMessageBox.Critical)
            mesege.setStandardButtons(QMessageBox.Cancel)
            mesege.exec()


    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Подтверждение',
                                     'Вы уверены, что хотите закрыть приложение?(При закрытии будильники сохраняться)',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        list_id = list()
        list_id1 = list()

        if reply == QMessageBox.Yes:
            con = sqlite3.connect('database.db')
            if self.coin1 in Futures().futures:
                for item in range(len(self.alarms)):
                    cur = con.cursor()
                    signal = self.alarms.item(item).text()
                    cur.execute(f'INSERT or ignore INTO alarms (price) VALUES("{signal}")')
                    list_id.append(cur.execute(f'select id from alarms where price= "{signal}"').fetchone()[0])
                    con.commit()

                cur = con.cursor()
                cur.execute(f'INSERT INTO futurs(futurs_name, futurs_id) VALUES("{self.coin1}", "{list_id}")'
                            f'ON CONFLICT (futurs_name) DO UPDATE SET futurs_id="{list_id}"')
                con.commit()
            if self.coin2 in Futures().futures:
                for item1 in range(len(self.alarms_1)):
                    cur = con.cursor()
                    signal1 = self.alarms_1.item(item1).text()
                    cur.execute(f'INSERT or ignore INTO alarms (price) VALUES("{signal1}")')
                    list_id1.append(cur.execute(f'select id from alarms where price= "{signal1}"').fetchone()[0])
                    con.commit()

                cur = con.cursor()
                cur.execute(f'INSERT INTO futurs(futurs_name, futurs_id) VALUES("{self.coin2}", "{list_id1}")'
                            f'ON CONFLICT (futurs_name) DO UPDATE SET futurs_id="{list_id1}"')
                con.commit()
                con.close()
            # останавливает все. Использую именно это действие, т.к поток отказыватся останавливатсья при закрытии
            # программыю. И при импорировке в .exe и закрытии программы, она остаёться работать в фоновом режиме и
            # единственный способ ее закрыть это заходить в диспетчер и останавливать процесс.

            stopit.__all__()
        else:
            event.ignore()

    def doubleClicked_alarm(self):
        if self.alarms.selectedItems():
            mesege = QMessageBox()
            mesege.setWindowTitle('Уточнение')
            mesege.setText('Вы точно хотите удалить будильник?')
            mesege.setIcon(QMessageBox.Question)
            mesege.setStandardButtons(QMessageBox.Ok | QMessageBox.No)
            mesege.exec()

            if mesege.clickedButton().text() == 'OK':
                self.alarms.takeItem(self.alarms.selectedIndexes()[0].row())

    def doubleClicked_alarm1(self):
        if self.alarms_1.selectedItems():
            mesege = QMessageBox()
            mesege.setWindowTitle('Уточнение')
            mesege.setText('Вы точно хотите удалить будильник?')
            mesege.setIcon(QMessageBox.Question)
            mesege.setStandardButtons(QMessageBox.Ok | QMessageBox.No)
            mesege.exec()

            if mesege.clickedButton().text() == 'OK':
                self.alarms_1.takeItem(self.alarms_1.selectedIndexes()[0].row())

    def music(self):
        song = pyglet.media.load('Waves-1.mp3')
        song.play()

    def text1(self):
        s = self.textEdit_3.text().strip()
        if s:
            with open('notes.text', 'a', encoding='utf-8') as file:
                file.write(s)
                file.write(''
                           ''
                           ''
                           ''
                           ''
                           ''
                           '\n')

    def yes_method(self):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        futer_id = cursor.execute(f'select futurs_id from futurs where futurs_name = "{self.coin1}"').fetchone()
        if futer_id:
            if eval(futer_id[0]):
                for item in eval(futer_id[0]):
                    text = cursor.execute(f'select price from alarms where id= {item}').fetchone()[0]
                    checkbox_item = QListWidgetItem(text)
                    checkbox_item.setCheckState(2)
                    self.alarms.addItem(checkbox_item)

        futer_id = cursor.execute(f'select futurs_id from futurs where futurs_name = "{self.coin2}"').fetchone()

        if futer_id:
            if eval(futer_id[0]):
                for item in eval(futer_id[0]):
                    text = cursor.execute(f'select price from alarms where id= {item}').fetchone()[0]
                    checkbox_item = QListWidgetItem(text)
                    checkbox_item.setCheckState(2)
                    self.alarms_1.addItem(checkbox_item)

    def work_an_alarms(self):
        filter_1 = list(filter(lambda x: x.checkState() > 0, [self.alarms.item(i) for i in range(self.alarms.count())]))

        filter_2 = list(
            filter(lambda x: x.text() == self.latest_coin_price_1.item(self.latest_coin_price_1.count() - 1).text(),
                   filter_1))

        if any(filter_2):
            self.music()
            for i in filter_2:
                i.setCheckState(0)

    def work_an_alarms1(self):
        filter_1 = list(
            filter(lambda x: x.checkState() > 0, [self.alarms_1.item(i) for i in range(self.alarms_1.count())]))

        filter_2 = list(
            filter(lambda x: float(x.text()) == self.latest_coin_price_3.item(self.latest_coin_price_3.count() - 1).text(),
                   filter_1))

        if any(filter_2):
            self.music()
            for i in filter_2:
                i.setCheckState(0)


class Socket(websocket.WebSocketApp):
    def __init__(self, url, mainwindow):
        super().__init__(url=url)
        self.window = mainwindow
        self.last_message_datetime = None
        self.on_message = lambda i, msg: self.message(msg)
        self.run_forever()

    def message(self, msg):
        current_datatime = datetime.datetime.now()

        if (self.last_message_datetime is not None and
                current_datatime - self.last_message_datetime < datetime.timedelta(seconds=1)):
            return

        self.last_message_datetime = current_datatime

        price = '123'
        self.window.latest_coin_price_1.addItem(price)

        if len(self.window.latest_coin_price_1) == 11:
            self.window.latest_coin_price_1.takeItem(0)


class Socket1(websocket.WebSocketApp):
    def __init__(self, url, mainwindow):
        super().__init__(url=url)
        self.window = mainwindow
        self.last_message_datetime = None
        self.on_message = lambda i, msg: self.message(msg)
        self.run_forever()

    def message(self, msg):
        current_datatime = datetime.datetime.now()

        if (self.last_message_datetime is not None and
                current_datatime - self.last_message_datetime < datetime.timedelta(seconds=1)):
            return

        self.last_message_datetime = current_datatime

        price = '123'
        self.window.latest_coin_price_3.addItem(price)

        if len(self.window.latest_coin_price_3) == 11:
            self.window.latest_coin_price_3.takeItem(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Futures()
    ex.show()
    sys.exit(app.exec())
