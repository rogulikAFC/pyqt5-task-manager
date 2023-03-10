import sys
from datetime import datetime
import json

from quotations_scrapper import random_quotation
from design2 import Ui_MainWindow, StringBox

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtCore import QThread
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from PyQt5.QtWidgets import QMainWindow, QApplication, QSpinBox,\
    QVBoxLayout, QLineEdit, QPlainTextEdit,\
    QDateTimeEdit, QPushButton, QCheckBox, \
    QScrollArea, QListWidget, QListWidgetItem, \
    QMessageBox, QSystemTrayIcon, QMenu, QAction
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

        self.set_tasks()
        self.set_categories()
        self.load_settings()
        self.selected_task = False

        # ???????????????????? ????????
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip('Task manager')
        self.tray.setVisible(True)

        self.tray_menu = QMenu()

        tell_quotation = QAction(
            '?????????? ???????????????????????? ????????????!', self
        )
        tell_quotation.triggered.connect(
            self.show_quotation_msg
        )

        self.tray_menu.addAction(
            tell_quotation
        )

        show = QAction('??????????????', self)
        show.triggered.connect(
            self.show
        )
        self.tray_menu.addAction(show)

        self.tray.setContextMenu(self.tray_menu)

        # ???????????????????? ???????????????? ??????????????????, ??????????????????????
        self.dedline_checker = TaskReminder()

        self.notification_timer = QTimer()
        self.notification_timer.timeout.connect(
            self.dedline_checker.start
        )
        self.notification_timer.start(5000)

        self.dedline_checker.notification_signal.connect(
            self.show_deadline_msg
        )

        # ?????????? ???????????????? ?????????? ???? ?????????????? ??????
        self.find_tasks_button.setContextMenuPolicy(
            Qt.CustomContextMenu
        )
        self.find_tasks_button.customContextMenuRequested.connect(
            self.drop_filters
        )

        self.unselect_task()

    def plus_change_page(self):
        """
        ?????????????????? ???????????????? ?????????? ????????????
        """
        self.tasks_page += 1

        if self.set_tasks() is not False:
            if self.tasks_page > len(self.get_all_tasks()):
                self.tasks_page -= 1

        else:
            self.tasks_page -= 1

    def minus_change_page(self):
        """
        ?????????????????? ???????????????? ?????????? ??????????
        """
        if self.tasks_page <= 0:
            return None

        self.tasks_page -= 1
        self.set_tasks()

    def set_tasks(self, tasks: list[dict] = None) -> bool:
        """
        ???????????????? ?????????? ?? GUI
        """

        # ?????????????????????? ???????????? ?????????? ?????? ????????????????
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
            page_tasks_list = list()

            if len(all_tasks_list) == 0:
                page_tasks_list.append(
                    {
                        'is_system': True,
                        'id': False,
                        'name': '???????????? ?????????? ????????????',
                    }
                )

            else:
                self.set_tasks(all_tasks_list)
                return None

        # ?????????????? ?????????? ?? GUI
        while self.all_tasks.count():
            child = self.all_tasks.takeAt(0)

            if child.widget():
                child.widget().deleteLater()

        # ?????????????????? ?????????????????????? ???????????? ??????????, ???????????????? ?? GUI
        for task in page_tasks_list:
            button = QPushButton()
            self.all_tasks.addWidget(button)

            is_system = False

            for key, value in task.items():
                # ?????????????????? ?????????????? ???????????? ????????????

                if key == 'name':
                    button.setText(value)

                # ???????????????? ???? ????, ?????????????????? ???? ????????????
                # ????????????????, ???????????? "???????????? ???? ??????????????" ?????????? ??????????????????.
                # ?????? ????????????, ?????? ?? ?????? ???? ?????????????????????? ???????????????? ??????????,
                # ???????????? ?????????????????????? ?????? ?????????????? (system_button)
                # ?? ?????????????????????? ???????? (???????????????? ????????????) ?????????????? ???? ??????????????????????,
                # ?????????????????? ?? ???????? "slot"

                elif key == 'is_system':
                    is_system = True

                elif key == 'id':
                    if not is_system:
                        button.setObjectName(f'task_{value}')

                    if is_system:
                        button.setObjectName('system_button')

                elif key == 'status_id':
                    # ?????????????????? ?????????? ???????????? ?? ?????????????????????? ???? ?????????????? ????????????

                    color = str()

                    if value == 1:  # ?? ????????????????
                        color = '#BAE7C3'   # light green

                    elif value == 2:    # ????????????????
                        color = '#D5BAE7'   # light purple

                    elif value == 3:    # ??????????????????
                        color = '#E7A3A3'   # light red

                    button.setStyleSheet(
                        f'background-color: "{color}"'
                    )

                elif key == 'slot':
                    # ?????????????????? ???????????????????????? ??????????
                    button.clicked.connect(value)

        for i in range(self.all_tasks.count()):
            widget = self.all_tasks.itemAt(i).widget()

            if widget.objectName() != 'system_button':
                # ?????????????????? ?????????????????????? ???????????? ???? ?????????????????????? ????????????

                widget.clicked.connect(
                    self.view_task
                )

                # ?????????????? ?????? ???? ???????????? ????????????
                widget.setContextMenuPolicy(
                    Qt.CustomContextMenu
                )
                widget.customContextMenuRequested.connect(
                    self.delete_task
                )

        return True

    def get_all_tasks(self, chunk_size: int = 17) -> list[dict]:
        """
        ?????????????????? ???????? ?????????? ???? ????, ?????????????????? ?????????????????????????? ?? ?????????????????????? ????????????
        ?? ?????????????? ?????????????? ?????? ???????????? ????????????. 
        """

        # ?????????????????? ???????? ?????????? ???? ????
        all_tasks_query = con.exec(
            'SELECT * FROM tasks ORDER BY status_id;'
        )

        # ???????????????? ???????????? ???? ???????????????????? ??????????
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

        # ?????????????? ???????????? ?????????? ???? ????????????????, ???????? ?????????? ???????????????? "chunk_size"
        if chunk_size:
            final_list = list()

            for i in range(0, len(tasks_list), chunk_size):
                final_list.append(tasks_list[i:i+chunk_size])

            return final_list

        else:
            return tasks_list

    def filter_tasks(self, tasks_list: list[dict] = None, chunk_size: int = 17) -> list[dict]:
        """
        ???????????????????? ???????? ?????????? ???? id ?????????????? ?? id ??????????????????
        """

        if not tasks_list:
            tasks_list = self.get_all_tasks(False)

        # ?????????????????? ?????????????????? ?? ?????????????? ?????? ????????????????????
        category_name = self.category_select.textFromValue(
            self.category_select.value()
        )
        status_name = self.status_select.textFromValue(
            self.status_select.value()
        )

        # ?????????????????? ???????????????? ?????????????? ?? ??????????????????
        # ?????????? ???????????????????????? ?????? ?????????????????????? ???????????????? ?? id ?????????????? ?? ??????????????????
        status_obj = QSqlQuery()
        status_obj.prepare(
            """
            SELECT id FROM statuses WHERE name=?
            """
        )

        status_obj.addBindValue(status_name)
        status_obj.exec()
        status_obj.first()

        # ???????????????? ??????????????
        status = status_obj.value(0)

        category_obj = QSqlQuery()
        category_obj.prepare(
            """
            SELECT id FROM categories WHERE name=?
            """
        )
        category_obj.addBindValue(category_name)
        category_obj.exec()
        category_obj.first()

        # ???????????????? ??????????????????
        category = category_obj.value(0)

        # ???????????????????? ?????????? ???? ????, ?? ?????????????? ???? ???? ??????????????????, ?????? ?? ??????????????
        # ?? ???? ????, ?? ?????????????? ?????? ???? ????????????, ?????? ?? ?? ??????????????
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

        # ???????????? ??????????, ?????????????? ?????????????? ?????? ????????????
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

        # ???????? ???????????? ???? ?????????????? ?????? ????????????, ???? ?????????????????? ?????????????????? ????????????,
        # ???????????????????????? ??????????????
        if len(sorted_list) == 0:
            self.set_tasks(
                [[
                    {
                        'is_system': True,
                        'id': 1,
                        'name': '???????????? ???? ??????????????. ??????????????, ?????????? ???????????????? ??????',
                        'slot': self.drop_filters,
                    }
                ]]
            )

            return None

        # ???????????????????? ???? ???????????????????? ?? sorted_list
        sorted2_list = list()

        for task in sorted_list:
            if task in sorted2_list:
                continue

            else:
                sorted2_list.append(task)

        # ???????????????????? ?????????????????????????????? ?????????? ???? ????????????????
        if chunk_size:
            final_list = list()

            for i in range(0, len(sorted2_list), chunk_size):
                final_list.append(sorted2_list[i:i+chunk_size])

            self.set_tasks(final_list)

    def drop_filters(self):
        """
        ?????????? ???????????????? ??????????
        """
        self.set_tasks()

        # ?????????????????? ?????????????????????? ???????????????? ?????????? ???????????? ????????????????
        self.status_select.setValue(0)
        self.category_select.setValue(0)

    def create_task(self):
        """
        ???????????????? ?????? ?????????????????? ????????????
        """

        # ?????????????????? ?????????? ?????????? ???????????????? ????????????
        name = self.name_inp.text()
        description = self.description_inp.toPlainText()
        category = self.category_inp.textFromValue(
            self.category_inp.value()
        )
        status = self.status_inp.textFromValue(
            self.status_inp.value()
        )
        deadline = self.datetime.dateTime().toPyDateTime()

        # ?????????????????? id ?????????????? ?? ??????????????????
        # ?????????? ???????????????????????? ?????? ?????????????????????? ???????????????? ?? id ?????????????? ?? ??????????????????
        status_id = QSqlQuery()
        status_id.prepare(
            """
            SELECT id FROM statuses WHERE name=?
            """
        )
        status_id.addBindValue(status)
        status_id.exec()
        status_id.first()

        category_id = QSqlQuery()
        category_id = con.exec(
            """
            SELECT id FROM categories WHERE name=?
            """
        )
        category_id.addBindValue(category)
        category_id.exec()
        category_id.first()

        # ???????????????????? ????????????, ???????? ?????? ??????????????
        if self.selected_task:
            # ?????????????????? ???????? ?????????????? ?????????????? ??????????
            columns = con.exec(
                'PRAGMA table_info(tasks)'
            )

            keys_list = list()

            while columns.next():
                keys_list.append(columns.value(1))

            # ???????????????????? ????????????
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

            self.unselect_task()
            self.set_tasks()

            return None

        # ???????????????? ????????????
        insert_task = QSqlQuery()
        insert_task.prepare(
            """
            INSERT INTO tasks (name, description, category_id, status_id, deadline)
            VALUES (?, ?, ?, ?, datetime(?))
            """
        )
        insert_task.addBindValue(name)
        insert_task.addBindValue(description)
        insert_task.addBindValue(
            category_id.value(0)
        )
        insert_task.addBindValue(
            status_id.value(0)
        )
        insert_task.addBindValue(
            str(deadline)
        )
        insert_task.exec()

        self.unselect_task()
        self.set_tasks()

        # CREATE TABLE tasks (
        #     id INTEGER PRIMARY KEY AUTOINCREMENT,
        #     name TEXT NOT NULL,
        #     description TEXT,
        #     category_id INTEGER NOT NULL REFERENCES categories (id) ON DELETE CASCADE ON UPDATE CASCADE,
        #     status_id INTEGER NOT NULL REFERENCES statuses (id) ON DELETE CASCADE ON UPDATE CASCADE,
        #     deadline DATETIME

    def view_task(self):
        """
        ???????????????? ????????????
        """

        # ?????????????????? id ????????????
        task_id = self.sender().objectName().\
            split('_')[1]

        self.selected_task = task_id

        # ?????????????????? ???????????? ????????????
        task = QSqlQuery()
        task.prepare(
            """
            SELECT * FROM tasks WHERE id=?
            """
        )
        task.addBindValue(task_id)
        task.exec()
        task.first()

        name = task.value(1)
        description = task.value(2)
        category_id = task.value(3)
        status_id = task.value(4)
        deadline = task.value(5)

        try:
            deadline_datetime = datetime.strptime(
                deadline, '%Y-%m-%d %H:%M:%S'
            )

        except:
            deadline_datetime = datetime.strftime(
                deadline, '%Y-%m-%d %H:%M:%S.%f'
            )

        # ?????????????????? ?????????????? ?????????????????? ?? ?????????????? ?????? ???? ???????? ????????????
        category = QSqlQuery()
        category.prepare(
            """
            SELECT name FROM categories WHERE id=?
            """
        )
        category.addBindValue(category_id)
        category.exec()
        category.first()

        status = QSqlQuery()
        status.prepare(
            """
            SELECT name FROM statuses WHERE id=?
            """
        )
        status.addBindValue(status_id)
        status.exec()
        status.first()

        global category_for_inp, status_for_inp
        category_for_inp = int()
        status_for_inp = int()

        for value, value_id in self.category_inp.values.items():
            if value == category.value(0):
                category_for_inp = value_id

        for value, value_id in self.status_inp.values.items():
            if value == status.value(0):
                status_for_inp = value_id

        # ?????????????????? ???????????? ???????????? ?? GUI
        self.name_inp.setText(name)
        self.description_inp.setPlainText(description)
        self.category_inp.setValue(category_for_inp)
        self.status_inp.setValue(status_for_inp)
        self.datetime.setDateTime(deadline_datetime)

    def unselect_task(self):
        """
        ?????????? ?????????????????? ????????????
        """
        self.selected_task = False
        self.name_inp.setText('???????????????? ????????????')
        self.description_inp.setPlainText('???????????????? ????????????')
        self.category_inp.setValue(1)
        self.status_inp.setValue(1)

        self.datetime.setDateTime(
            datetime.now()
        )

    def set_categories(self):
        """
        ?????????????????? ?? ???????????????? ?????????????????? ?? GUI
        """

        # ?????????????? ???????????? ?????????????????? ?? GUI
        self.categories_layout.clear()

        # ?????????????????? ???????????? ??????????????????
        categories = con.exec(
            'SELECT * FROM categories'
        )

        categories_list = list()

        # ?????????????????? ?????????????????? ?? GUI
        while categories.next():
            item = QListWidgetItem(categories.value(1))
            categories_list.append(categories.value(1))
            self.categories_layout.addItem(item)

        # ???????????????????? ???????? ?????????? ?????????? ??????????????????
        self.category_inp.setStrings(categories_list)
        self.category_select.setStrings(categories_list)

    def create_category(self):
        """
        ???????????????? ??????????????????
        """

        # ?????????????????? ???????????????? ?????????????????? ???? ??????????
        cat_name = self.category_name_inp.text()

        category_insert = QSqlQuery()
        category_insert.prepare(
            """
            INSERT INTO categories (name) VALUES (?)
            """
        )
        category_insert.addBindValue(cat_name)
        category_insert.exec()

        self.set_categories()
        self.unselect_task()

    def delete_category(self, item):
        """
        ???????????????? ??????????????????
        """
        category_name = item.text()

        # ?????????????????? ???????????????? ?????????????????? ?? ?????????? ?? ???????? ??????????????????
        category = QSqlQuery()
        category.prepare(
            """
            SELECT id FROM categories WHERE name=?
            """
        )
        category.addBindValue(category_name)
        category.exec()
        category.first()
        category_id = category.value(0)

        tasks = QSqlQuery()
        tasks.prepare(
            """
            SELECT name FROM tasks WHERE category_id=?
            """
        )
        tasks.addBindValue(category_id)
        tasks.exec()

        tasks_list = list()

        # ?????????????????? ???????????? ?????????? ?????? ?????????????????????? ???? ????????????????
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
                tasks_str += f' ?? ?????? {not_joined} ??????????'

        else:
            tasks_str = '?????????????????? ??????????'

        # ???????????????????? ???????? ???????????????? ?????????????????? ?? ?????????? ?? ??????
        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Question)
        message_box.setWindowTitle(
            f'?????????????? ?????????????????? "{category_name}"?'
        )

        if len(tasks_list) > 0:
            message_box.setText(
                f'???????????? ?? ?????? ???????????????? {tasks_str}'
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
            # ???????????????? ?????????????????? ?? ?????????? ?? ??????

            category_delete = QSqlQuery()
            category_delete.prepare(
                """
                DELETE FROM categories WHERE name=?
                """
            )
            category_delete.addBindValue(category_name)
            category_delete.exec()

            self.set_categories()

            tasks_delete = QSqlQuery()
            tasks_delete.prepare(
                """
                DELETE FROM tasks WHERE category_id=?
                """
            )
            tasks_delete.addBindValue(category_id)
            tasks_delete.exec()

            self.set_tasks()
            self.unselect_task()

    def delete_task(self):
        """
        ???????????????? ????????????
        """

        # ?????????????????? id ????????????
        task = self.sender()
        task_id = task.objectName().split('_')[1]

        # ?????????????????? ???????? ???????????????? ????????????
        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Question)
        message_box.setWindowTitle(
            f'???????????????? ????????????'
        )
        message_box.setText(
            f'?????????????? "{task.text()}"?'
        )
        message_box.setStandardButtons(
            QMessageBox.Ok | QMessageBox.Cancel
        )

        retval = message_box.exec_()

        if retval == 4194304:   # cancel
            return None

        elif retval == 1024:    # accept
            # ???????????????? ????????????

            task_delete = QSqlQuery()
            task_delete.prepare(
                """
                DELETE FROM tasks WHERE id=?
                """
            )
            task_delete.addBindValue(task_id)
            task_delete.exec()

        self.set_tasks()
        self.unselect_task()

    def load_settings(self):
        # ???????????????? ????????????????

        settings_file = open('settings.json')
        settings_data = json.load(
            settings_file
        )

        # ?????????????????? ???????????????? ?? GUI
        in_tray = settings_data.get('in_tray')
        notifications = settings_data.get('notifications')

        self.in_tray_option.setChecked(in_tray)
        self.notifications_option.setChecked(notifications)

    def change_settings(self):
        """
        ?????????????????? ????????????????
        """

        in_tray = self.in_tray_option.isChecked()
        notifications = self.notifications_option.isChecked()

        new_settings = {
            'in_tray': in_tray,
            'notifications': notifications
        }

        settings_file = open('settings.json', 'w')
        settings_file.write(json.dumps(new_settings))

    def show_quotation_msg(self):
        """
        ?????????????????????? ?? ???????????????????????? ??????????????
        """
        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Information)
        message_box.setWindowTitle(
            '????????????'
        )
        message_box.setText(
            random_quotation()
        )

        message_box.exec_()

    def show_deadline_msg(self, signal_data):
        """
        ?????????? ?????????????????????? ?? ???????????????? ????????????. ???????????????? ???????????? ?????? ???????????????????????????? ????????????????????????
        """
        if not self.notifications_option.isChecked():
            return None

        notification = QMessageBox()
        notification.setWindowTitle(
            'Task manager'
        )
        notification.setText(
            f'???? ???????????????? ???????????? "{signal_data[0]}" ???????????????? {signal_data[1]} ??????????(a)'
        )
        notification.setIcon(
            notification.Information
        )
        notification.exec_()

    def closeEvent(self, event):
        # ???????? ?????????????? "???????????????? ?? ????????", ???? ???????? ?????????????????????????? ?? ????????
        # ???????? ???? ??????????????, ???? ??????????????????????
        # ???????????????????????? ???????????????? ???????????? ?????? ???????????????????????????? ????????????????????????

        if self.in_tray_option.isChecked():
            event.ignore()
            self.hide()
            app.setQuitOnLastWindowClosed(False)

        else:
            app.setQuitOnLastWindowClosed(True)


class TaskReminder(QThread):
    """
    ??????????, ?????????????????????? ???????????????? ??????????
    """

    notification_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__(parent=app)

        self.tasks = self.get_names_and_dates()
        self.notifications_list = list()

    def get_names_and_dates(self) -> dict:
        """
        ?????????????????? ??????????, ???? ?????????????? ?? ????????????????
        """
        tasks = con.exec(
            'SELECT name, deadline, status_id FROM tasks'
        )

        final_dict = dict()

        while tasks.next():
            try:
                date = datetime.strptime(
                    tasks.value(1), '%Y-%m-%d %H:%M:%S'
                )

            except:
                continue

            status_id = tasks.value(2)

            if status_id != 3:
                final_dict[tasks.value(0)] = date

        self.tasks = final_dict
        return final_dict

    def run(self):
        tasks = self.get_names_and_dates()
        now = datetime.now()

        for task, deadline in tasks.items():
            # ?????????????????????? ???????????????? ???????????????? ????????????
            near = deadline - now
            near_days = near.days

            if near_days == 0:
                near_minutes = int(near.total_seconds() // 60)

                if near_minutes > 0 and near_minutes <= 15:
                    # ?????????????????????? ?? ????????????????, ???????? ?? ?????? ?????? ???? ??????????????????

                    if task not in self.notifications_list:
                        self.notifications_list.append(task)
                        self.notification_signal.emit(
                            [task, near_minutes]
                        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
