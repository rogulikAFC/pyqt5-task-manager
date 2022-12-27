import sys
from datetime import datetime
import json
from time import sleep

from quotations_scrapper import random_quotation
from design2 import Ui_MainWindow, StringBox

import schedule

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtCore import QThread
from PyQt5.QtSql import QSqlDatabase
from PyQt5.QtWidgets import QMainWindow, QApplication, QSpinBox,\
    QVBoxLayout, QLineEdit, QPlainTextEdit,\
    QDateTimeEdit, QPushButton, QCheckBox, \
    QScrollArea, QListWidget, QListWidgetItem, \
    QMessageBox, QSystemTrayIcon, QMenu, QAction
from PyQt5 import uic
from PyQt5 import QtGui


con = QSqlDatabase.addDatabase('QSQLITE')
con.setDatabaseName('db.sqlite3')


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        ui = Ui_MainWindow()
        ui.setupUi(self)

        icon = QtGui.QIcon(u'./icon.png')

        self.setWindowTitle('Task manager')
        self.setWindowIcon(icon)

        if not con.open():
            print('db couldnt open')
            return None

        # con.exec(
        #     """
        #     ALTER TABLE tasks
        #     DROP FOREIGN KEY category_id;
        #     """
        # )

        # con.exec(
        #     """
        #     ALTER TABLE tasks
        #     ADD CONSTRAINT category_id
        #         INTEGER REFERENCES categories (id) ON DELETE CASCADE ON UPDATE CASCADE;
        #     """
        # )

        self.category_select = self.findChild(
            StringBox, 'category_select'
        )

        self.status_select = self.findChild(
            QSpinBox, 'status_select'
        )

        self.all_tasks = self.findChild(
            QVBoxLayout, 'tasks_layout'
        )

        self.all_tasks.setAlignment(Qt.AlignTop)

        self.tasks_page = 0

        self.next_page_btn = self.findChild(
            QPushButton, 'pushButton_2'
        )

        self.last_page_btn = self.findChild(
            QPushButton, 'pushButton_3'
        )

        self.name_inp = self.findChild(
            QLineEdit, 'name'
        )

        self.description_inp = self.findChild(
            QPlainTextEdit, 'description'
        )

        self.category_inp = self.findChild(
            QSpinBox, 'category_inp'
        )

        self.status_inp = self.findChild(
            QSpinBox, 'status_inp'
        )

        self.datetime = self.findChild(
            QDateTimeEdit, 'datetime'
        )

        self.change_btn = self.findChild(
            QPushButton, 'change_btn'
        )

        self.new_task_btn = self.findChild(
            QPushButton, 'new_task_btn'
        )

        self.category_name_inp = self.findChild(
            QLineEdit, 'category_name_inp'
        )

        self.new_category_btn = self.findChild(
            QPushButton, 'new_category_btn'
        )

        self.category_scroll = self.findChild(
            QScrollArea, 'category_scroll'
        )

        self.categories_layout = self.findChild(
            QListWidget, 'category_scroll_vl'
        )

        self.find_tasks_button = self.findChild(
            QPushButton, 'find_tasks_btn'
        )

        self.in_tray_option = self.findChild(
            QCheckBox, 'in_tray_option'
        )

        self.notifications_option = self.findChild(
            QCheckBox, 'notifications_option'
        )

        self.change_btn.clicked.connect(
            self.create_task
        )

        self.next_page_btn.clicked.connect(
            self.plus_change_page
        )

        self.last_page_btn.clicked.connect(
            self.minus_change_page
        )

        self.new_task_btn.clicked.connect(
            self.unselect_task
        )

        self.new_category_btn.clicked.connect(
            self.create_category
        )

        self.categories_layout.itemActivated.connect(
            self.delete_category
        )

        self.find_tasks_button.clicked.connect(
            self.filter_tasks
        )

        self.notifications_option.stateChanged.connect(
            self.change_settings
        )

        self.in_tray_option.stateChanged.connect(
            self.change_settings
        )

        self.set_all_tasks()
        self.set_categories()
        self.load_settings()
        self.selected_task = False

        icon = QtGui.QIcon(u'./icon.png')

        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip('Task manager')
        self.tray.setVisible(True)

        self.tray_menu = QMenu()

        tell_quotation = QAction(
            'Скажи мотивирующую цитату!', self
        )
        tell_quotation.triggered.connect(
            self.show_quotation_msg
        )

        self.tray_menu.addAction(
            tell_quotation
        )

        show = QAction('Открыть', self)
        show.triggered.connect(
            self.show
        )
        self.tray_menu.addAction(show)

        self.tray.setContextMenu(self.tray_menu)

        self.dedline_checker = TaskReminder()

        self.notification_timer = QTimer()
        self.notification_timer.timeout.connect(
            self.dedline_checker.start
        )
        self.notification_timer.start(5000)

        # self.connect(
        #     self.dedline_checker,
        #     self.dedline_checker.notification_signal,
        #     self.show_notification
        # )

        self.dedline_checker.notification_signal.connect(
            self.show_notification
        )

        self.unselect_task()

    def plus_change_page(self):
        print(f'page is {self.tasks_page}')

        print(f'set all tasks is {self.set_all_tasks()}')

        self.tasks_page += 1

        if self.set_all_tasks() is not False:
            if self.tasks_page > len(self.get_all_tasks()):
                self.tasks_page -= 1

        else:
            self.tasks_page -= 1

    def minus_change_page(self):
        print(f'page is {self.tasks_page}')

        if self.tasks_page <= 0:
            return None

        self.tasks_page -= 1
        self.set_all_tasks()

    def set_all_tasks(self, tasks: list[dict] = None):
        if not tasks:
            all_tasks_list = self.get_all_tasks()

        else:
            all_tasks_list = tasks

        try:
            page_tasks_list = all_tasks_list[
                self.tasks_page
            ]

        except:
            self.tasks_page = 0
            self.set_all_tasks(all_tasks_list)
            return None

        while self.all_tasks.count():
            child = self.all_tasks.takeAt(0)

            if child.widget():
                child.widget().deleteLater()

        for task in page_tasks_list:
            print(task)
            button = QPushButton()
            self.all_tasks.addWidget(button)

            is_system = False

            for key, value in task.items():
                if key == 'name':
                    button.setText(value)

                elif key == 'is_system':
                    is_system = True

                elif key == 'id':
                    if not is_system:
                        button.setObjectName(f'task_{value}')

                    if is_system:
                        button.setObjectName('system_button')

                elif key == 'status_id':
                    color = str()

                    if value == 1:  # В процессе
                        color = '#BAE7C3'   # light green

                    elif value == 2:    # Отложено
                        color = '#D5BAE7'   # light purple

                    elif value == 3:    # Завершено
                        color = '#E7A3A3'   # light red

                    button.setStyleSheet(
                        f'background-color: "{color}"'
                    )

                elif key == 'slot':
                    button.clicked.connect(value)

        for i in range(self.all_tasks.count()):
            widget = self.all_tasks.itemAt(i).widget()

            if widget.objectName() != 'system_button':
                widget.clicked.connect(
                    self.view_task
                )
                widget.setContextMenuPolicy(
                    Qt.CustomContextMenu
                )
                widget.customContextMenuRequested.connect(
                    self.delete_task
                )

        # try:
        #     self.dedline_checker.get_names_and_dates()

        # except:
        #     print('cannot set deadline reminder')

        return True

    def get_all_tasks(self, chunk_size: int = 17) -> list[dict]:
        all_tasks_query = con.exec(
            'SELECT * FROM tasks ORDER BY status_id;'
        )

        tasks_list = list()

        while all_tasks_query.next():
            tasks_list.append(
                {
                    'id': all_tasks_query.value(0),
                    'name': all_tasks_query.value(1),
                    'date': all_tasks_query.value(5),
                    'category_id': all_tasks_query.value(3),
                    'status_id': all_tasks_query.value(4)
                }
            )

        if chunk_size:
            final_list = list()

            for i in range(0, len(tasks_list), chunk_size):
                final_list.append(tasks_list[i:i+chunk_size])

            return final_list

        else:
            return tasks_list

    def filter_tasks(self, tasks_list: list[dict] = None, chunk_size: int = 17) -> list[dict]:
        print(tasks_list)

        if not tasks_list:
            tasks_list = self.get_all_tasks(False)

        category_name = self.category_select.textFromValue(
            self.category_select.value()
        )
        status_name = self.status_select.textFromValue(
            self.status_select.value()
        )
        print(category_name, status_name)

        status_obj = con.exec(
            f'SELECT id FROM statuses WHERE name="{status_name}"'
        )
        status_obj.first()
        status = status_obj.value(0)

        category_obj = con.exec(
            f'SELECT id FROM categories WHERE name="{category_name}"'
        )
        category_obj.first()
        category = category_obj.value(0)

        same_category = list()
        same_status = list()

        for task in tasks_list:
            for key, value in task.items():
                if key == 'category_id':
                    if value == category:
                        same_category.append(task)

                elif key == 'status_id':
                    if value == status:
                        same_status.append(task)

        sorted_list = list()

        for task in same_category:
            for key, value in task.items():
                if key == 'status_id':
                    if value == status:
                        sorted_list.append(task)

        for task in same_status:
            for key, value in task.items():
                if key == 'category_id':
                    if value == category:
                        sorted_list.append(task)

        print(sorted_list)

        if len(sorted_list) == 0:
            self.set_all_tasks(
                [[
                    {
                        'is_system': True,
                        'id': 1,
                        'name': 'Ничего не найдено. Нажмите, чтобы показать все',
                        'slot': self.set_all_tasks,
                    }
                ]]
            )

            return None

        sorted2_list = list()

        for task in sorted_list:
            if task in sorted2_list:
                continue

            else:
                sorted2_list.append(task)

        print(sorted2_list)

        if chunk_size:
            final_list = list()

            for i in range(0, len(sorted2_list), chunk_size):
                final_list.append(sorted2_list[i:i+chunk_size])

            print(len(final_list))
            self.set_all_tasks(final_list)

    def create_task(self):
        if not con.open():
            print('db couldnt open')

            return None

        name = self.name_inp.text()
        description = self.description_inp.toPlainText()
        category = self.category_inp.textFromValue(
            self.category_inp.value()
        )
        status = self.status_inp.textFromValue(
            self.status_inp.value()
        )
        deadline = self.datetime.dateTime().toPyDateTime()

        status_id = con.exec(
            f'SELECT id FROM statuses WHERE name="{status}";'
        )
        status_id.first()

        category_id = con.exec(
            f'SELECT id FROM categories WHERE name="{category}";'
        )
        category_id.first()

        if self.selected_task:

            columns = con.exec(
                'PRAGMA table_info(tasks)'
            )

            keys_list = list()

            while columns.next():
                keys_list.append(columns.value(1))

            for key, value in zip(
                keys_list,
                [self.selected_task, name, description,
                 category_id.value(0), status_id.value(0), deadline]
            ):
                if type(value) is str:
                    con.exec(
                        f'UPDATE tasks SET {key}="{value}" WHERE id={self.selected_task}'
                    )

                elif type(value) is int:
                    con.exec(
                        f'UPDATE tasks SET {key}={value} WHERE id={self.selected_task}'
                    )

                if type(value) is datetime:
                    con.exec(
                        f'UPDATE tasks SET {key}=datetime("{value}") WHERE id={self.selected_task}'
                    )

                print(key, value)

            self.unselect_task()
            self.set_all_tasks()

            return None

        con.exec(
            f'INSERT INTO tasks (name, description, category_id, status_id, deadline) VALUES ("{name}", "{description}", {category_id.value(0)}, {status_id.value(0)}, datetime("{str(deadline)}"));'
        )

        self.unselect_task()
        self.set_all_tasks()

        # con.exec(
        #     """
        #     DROP TABLE tasks;
        #     """
        # )

        # con.exec(
        #     """
        #     CREATE TABLE tasks (
        #         id INTEGER PRIMARY KEY AUTOINCREMENT,
        #         name TEXT NOT NULL,
        #         description TEXT,
        #         category_id INTEGER NOT NULL REFERENCES categories (id) ON DELETE CASCADE ON UPDATE CASCADE,
        #         status_id INTEGER NOT NULL REFERENCES statuses (id) ON DELETE CASCADE ON UPDATE CASCADE,
        #         deadline DATETIME
        #     );
        #     """
        # )

        print('clicked')
        return None

    def view_task(self):
        print(self.sender().objectName())
        task_id = self.sender().objectName().\
            split('_')[1]

        self.selected_task = task_id
        print(self.selected_task)

        task = con.exec(
            f'SELECT * FROM tasks WHERE id="{task_id}"'
        )
        task.first()

        name = task.value(1)
        description = task.value(2)
        category_id = task.value(3)
        status_id = task.value(4)
        deadline = task.value(5)

        deadline_datetime = datetime.strptime(
            deadline, '%Y-%m-%d %H:%M:%S'
        )

        category = con.exec(
            f'SELECT name FROM categories WHERE id={category_id}'
        )
        category.first()
        print(category.value(0))
        print(self.category_inp.values)

        status = con.exec(
            f'SELECT name FROM statuses WHERE id={status_id}'
        )
        status.first()
        print(self.status_inp.values)
        print(status.value(0))

        global category_for_inp, status_for_inp
        category_for_inp = int()
        status_for_inp = int()

        for value, value_id in self.category_inp.values.items():
            if value == category.value(0):
                category_for_inp = value_id

        for value, value_id in self.status_inp.values.items():
            if value == status.value(0):
                status_for_inp = value_id

        print(name, description, category_id, status_id, deadline)

        self.name_inp.setText(name)
        self.description_inp.setPlainText(description)
        self.category_inp.setValue(category_for_inp)
        self.status_inp.setValue(status_for_inp)
        self.datetime.setDateTime(deadline_datetime)

    def unselect_task(self):
        self.selected_task = False
        self.name_inp.setText('Название задачи')
        self.description_inp.setPlainText('Описание задачи')
        self.category_inp.setValue(1)
        self.status_inp.setValue(1)

        self.datetime.setDateTime(
            # datetime.strptime(
            #     '01-01-2000 0:00', '%d-%m-%Y %H:%M'
            # )
            datetime.now()
        )

        print(self.selected_task)

    def set_categories(self):
        self.categories_layout.clear()

        categories = con.exec(
            'SELECT * FROM categories'
        )

        categories_list = list()

        while categories.next():
            item = QListWidgetItem(categories.value(1))
            categories_list.append(categories.value(1))
            self.categories_layout.addItem(item)

        print(categories_list)
        self.category_inp.setStrings(categories_list)
        self.category_select.setStrings(categories_list)

    def create_category(self):
        cat_name = self.category_name_inp.text()

        con.exec(
            f'INSERT INTO categories (name) VALUES ("{cat_name}")'
        )

        self.set_categories()
        self.unselect_task()
        print('lol')

    def delete_category(self, item):
        category_name = item.text()

        category = con.exec(
            f'SELECT id FROM categories WHERE name="{category_name}"'
        )

        category.first()
        category_id = category.value(0)

        tasks = con.exec(
            f'SELECT name FROM tasks WHERE category_id={category_id}'
        )

        tasks_list = list()

        while tasks.next():
            print(tasks.value(0))
            tasks_list.append(
                tasks.value(0)
            )

        tasks_str = ''
        joins = 0
        not_joined = 0

        if len(tasks_list) > 0:
            for task in tasks_list:
                if joins == 0:
                    tasks_str += f'"{task}"'

                elif joins > 0:
                    if joins > 5:
                        not_joined += 1

                    else:
                        tasks_str += f', "{task}"'

                joins += 1

            if joins > 5:
                tasks_str += f' и еще {not_joined} задач'

        else:
            tasks_str = 'Категория пуста'

        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Question)
        message_box.setWindowTitle(
            f'Удалить категорию "{category_name}"?'
        )

        if len(tasks_list) > 0:
            message_box.setText(
                f'Вместе с ней удалятся {tasks_str}'
            )
        else:
            message_box.setText(
                tasks_str
            )

        message_box.setStandardButtons(
            QMessageBox.Ok | QMessageBox.Cancel
        )

        retval = message_box.exec_()

        if retval == 4194304:   # cancel
            return None

        elif retval == 1024:    # accept
            print('accepted')

            con.exec(
                f'DELETE FROM categories WHERE name="{category_name}"'
            )

            self.set_categories()

            con.exec(
                f'DELETE FROM tasks WHERE category_id={category_id}'
            )

            self.set_all_tasks()
            self.unselect_task()

            print(f'category {category_name} deleted')

    def delete_task(self):
        task = self.sender()
        task_id = task.objectName().split('_')[1]
        print(task_id)

        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Question)
        message_box.setWindowTitle(
            f'Удаление задачи'
        )
        message_box.setText(
            f'Удалить "{task.text()}"?'
        )
        message_box.setStandardButtons(
            QMessageBox.Ok | QMessageBox.Cancel
        )

        retval = message_box.exec_()

        if retval == 4194304:   # cancel
            return None

        elif retval == 1024:    # accept
            print('accepted')

            con.exec(
                f'DELETE FROM tasks WHERE id={task_id}'
            )

        self.set_all_tasks()
        self.unselect_task()

    def load_settings(self):
        settings_file = open('settings.json')
        settings_data = json.load(
            settings_file
        )

        in_tray = settings_data.get('in_tray')
        notifications = settings_data.get('notifications')

        self.in_tray_option.setChecked(in_tray)
        self.notifications_option.setChecked(notifications)

    def change_settings(self):
        in_tray = self.in_tray_option.isChecked()
        notifications = self.notifications_option.isChecked()

        print(in_tray, notifications)

        new_settings = {
            'in_tray': in_tray,
            'notifications': notifications
        }

        settings_file = open('settings.json', 'w')
        settings_file.write(json.dumps(new_settings))

    def show_quotation_msg(self):
        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Information)
        message_box.setWindowTitle(
            'Цитата'
        )
        message_box.setText(
            random_quotation()
        )

        message_box.exec_()

    def show_notification(self, signal):
        if not self.notifications_option.isChecked():
            return None

        notification = QMessageBox()
        notification.setWindowTitle(
            'Task manager'
        )
        notification.setText(
            f'До дедлайна задачи "{signal[0]}" осталось {signal[1]} минут(a)'
        )
        notification.setIcon(
            notification.Information
        )
        notification.exec_()

    def closeEvent(self, event):
        if self.in_tray_option.isChecked():
            event.ignore()
            self.hide()
            app.setQuitOnLastWindowClosed(False)

        else:
            app.setQuitOnLastWindowClosed(True)


class TaskReminder(QThread):
    notification_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__(parent=app)

        self.tasks = self.get_names_and_dates()
        self.notifications_list = list()

    def get_names_and_dates(self) -> dict:
        tasks = con.exec(
            'SELECT name, deadline, status_id FROM tasks'
        )

        final_dict = dict()

        while tasks.next():
            date = datetime.strptime(
                tasks.value(1), '%Y-%m-%d %H:%M:%S'
            )
            status_id = tasks.value(2)

            if status_id != 3:
                final_dict[tasks.value(0)] = date

        self.tasks = final_dict
        return final_dict

    def run(self):
        tasks = self.get_names_and_dates()

        now = datetime.now()

        for task, deadline in tasks.items():
            near = deadline - now
            print(near)
            near_days = near.days

            if near_days == 0:
                near_minutes = int(near.total_seconds() // 60)

                if near_minutes > 0 and near_minutes <= 15:
                    if task not in self.notifications_list:
                        print(task)

                        self.notifications_list.append(task)
                        self.notification_signal.emit(
                            [task, near_minutes]
                        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
