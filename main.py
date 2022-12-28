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

        # Добавление трея
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

        # Добавление проверки дедлайнов, уведомлений
        self.dedline_checker = TaskReminder()

        self.notification_timer = QTimer()
        self.notification_timer.timeout.connect(
            self.dedline_checker.start
        )
        self.notification_timer.start(5000)

        self.dedline_checker.notification_signal.connect(
            self.show_deadline_msg
        )

        # Сброс фильтров задач по нажатию ПКМ
        self.find_tasks_button.setContextMenuPolicy(
            Qt.CustomContextMenu
        )
        self.find_tasks_button.customContextMenuRequested.connect(
            self.drop_filters
        )

        self.unselect_task()

    def plus_change_page(self):
        """
        Прокрутка страницы задач вперед
        """
        self.tasks_page += 1

        if self.set_tasks() is not False:
            if self.tasks_page > len(self.get_all_tasks()):
                self.tasks_page -= 1

        else:
            self.tasks_page -= 1

    def minus_change_page(self):
        """
        Прокрутка страницы задач назад
        """
        if self.tasks_page <= 0:
            return None

        self.tasks_page -= 1
        self.set_tasks()

    def set_tasks(self, tasks: list[dict] = None) -> bool:
        """
        Загрузка задач в GUI
        """

        # Определение списка задач для загрузки
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
                        'name': 'Список задач пустой',
                    }
                )

            else:
                self.set_tasks(all_tasks_list)
                return None

        # Очистка задач в GUI
        while self.all_tasks.count():
            child = self.all_tasks.takeAt(0)

            if child.widget():
                child.widget().deleteLater()

        # Обработка полученного списка задач, загрузка в GUI
        for task in page_tasks_list:
            button = QPushButton()
            self.all_tasks.addWidget(button)

            is_system = False

            for key, value in task.items():
                # Установка свойств кнопки задачи

                if key == 'name':
                    button.setText(value)

                # Проверка на то, системная ли кнопка
                # Например, кнопка "Ничего не найдено" будет системной.
                # Это значит, что к ней не применяется свойство цвета,
                # даётся специальное имя объекта (system_button)
                # и стандартный слот (просмотр задачи) заменен на специальный,
                # указанный в поле "slot"

                elif key == 'is_system':
                    is_system = True

                elif key == 'id':
                    if not is_system:
                        button.setObjectName(f'task_{value}')

                    if is_system:
                        button.setObjectName('system_button')

                elif key == 'status_id':
                    # Установка цвета кнопки в зависимости от статуса задачи

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
                    # Установка специального слота
                    button.clicked.connect(value)

        for i in range(self.all_tasks.count()):
            widget = self.all_tasks.itemAt(i).widget()

            if widget.objectName() != 'system_button':
                # Установка стандартных слотов на несистемные кнопки

                widget.clicked.connect(
                    self.view_task
                )

                # Нажатие ПКМ на кнопку задачи
                widget.setContextMenuPolicy(
                    Qt.CustomContextMenu
                )
                widget.customContextMenuRequested.connect(
                    self.delete_task
                )

        return True

    def get_all_tasks(self, chunk_size: int = 17) -> list[dict]:
        """
        Получение всех задач из БД, результат упаковывается в специальный список
        с набором свойств для каждой задачи. 
        """

        # Получение всех задач из БД
        all_tasks_query = con.exec(
            'SELECT * FROM tasks ORDER BY status_id;'
        )

        # Создание списка со свойствами задач
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

        # Деление списка задач на страницы, если задан параметр "chunk_size"
        if chunk_size:
            final_list = list()

            for i in range(0, len(tasks_list), chunk_size):
                final_list.append(tasks_list[i:i+chunk_size])

            return final_list

        else:
            return tasks_list

    def filter_tasks(self, tasks_list: list[dict] = None, chunk_size: int = 17) -> list[dict]:
        """
        Фильтрация всех задач по id статуса и id категории
        """

        if not tasks_list:
            tasks_list = self.get_all_tasks(False)

        # Получение категории и статуса для фильтрации
        category_name = self.category_select.textFromValue(
            self.category_select.value()
        )
        status_name = self.status_select.textFromValue(
            self.status_select.value()
        )

        # Получение названия статуса и категории
        # Будет использовано для соотнесения названия и id статуса и категории
        status_obj = QSqlQuery()
        status_obj.prepare(
            """
            SELECT id FROM statuses WHERE name=?
            """
        )

        status_obj.addBindValue(status_name)
        status_obj.exec()
        status_obj.first()

        # Название статуса
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

        # Название категории
        category = category_obj.value(0)

        # Разделение задач на те, у которых та же категория, что и фильтре
        # и на те, у которых тот же статус, что и в фильтре
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

        # Список задач, которые подошли под фильтр
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

        # Если ничего не подошло под фильтр, то создается системная кнопка,
        # сбрасывающая фильтры
        if len(sorted_list) == 0:
            self.set_tasks(
                [[
                    {
                        'is_system': True,
                        'id': 1,
                        'name': 'Ничего не найдено. Нажмите, чтобы показать все',
                        'slot': self.drop_filters,
                    }
                ]]
            )

            return None

        # Избавление от совпадений в sorted_list
        sorted2_list = list()

        for task in sorted_list:
            if task in sorted2_list:
                continue

            else:
                sorted2_list.append(task)

        # Разделение отфильтрованных задач на страницы
        if chunk_size:
            final_list = list()

            for i in range(0, len(sorted2_list), chunk_size):
                final_list.append(sorted2_list[i:i+chunk_size])

            self.set_tasks(final_list)

    def drop_filters(self):
        """
        Сброс фильтров задач
        """
        self.set_tasks()

        # Установка стандартных значений полей выбора фильтров
        self.status_select.setValue(0)
        self.category_select.setValue(0)

    def create_task(self):
        """
        Создание или изменение задачи
        """

        # Обработка полей формы создания задачи
        name = self.name_inp.text()
        description = self.description_inp.toPlainText()
        category = self.category_inp.textFromValue(
            self.category_inp.value()
        )
        status = self.status_inp.textFromValue(
            self.status_inp.value()
        )
        deadline = self.datetime.dateTime().toPyDateTime()

        # Получение id статуса и категории
        # Будет использовано для соотнесения названия и id статуса и категории
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

        # Обновление задачи, если она выбрана
        if self.selected_task:
            # Получение всех колонок таблицы задач
            columns = con.exec(
                'PRAGMA table_info(tasks)'
            )

            keys_list = list()

            while columns.next():
                keys_list.append(columns.value(1))

            # Обновление задачи
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

        # Создание задачи
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
        Просмотр задачи
        """

        # Получение id задачи
        task_id = self.sender().objectName().\
            split('_')[1]

        self.selected_task = task_id

        # Получение данных задачи
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

        # Получение индекса категории и статуса для их поля выбора
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

        # Установка данных задачи в GUI
        self.name_inp.setText(name)
        self.description_inp.setPlainText(description)
        self.category_inp.setValue(category_for_inp)
        self.status_inp.setValue(status_for_inp)
        self.datetime.setDateTime(deadline_datetime)

    def unselect_task(self):
        """
        Сброс выбранной задачи
        """
        self.selected_task = False
        self.name_inp.setText('Название задачи')
        self.description_inp.setPlainText('Описание задачи')
        self.category_inp.setValue(1)
        self.status_inp.setValue(1)

        self.datetime.setDateTime(
            datetime.now()
        )

    def set_categories(self):
        """
        Получение и загрузка категорий в GUI
        """

        # Очистка списка категорий в GUI
        self.categories_layout.clear()

        # Получение списка категорий
        categories = con.exec(
            'SELECT * FROM categories'
        )

        categories_list = list()

        # Установка категорий в GUI
        while categories.next():
            item = QListWidgetItem(categories.value(1))
            categories_list.append(categories.value(1))
            self.categories_layout.addItem(item)

        # Обновление всех полей ввода категории
        self.category_inp.setStrings(categories_list)
        self.category_select.setStrings(categories_list)

    def create_category(self):
        """
        Создание категории
        """

        # Получение названия категории из формы
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
        Удаление категории
        """
        category_name = item.text()

        # Получение названия категории и задач в этой категории
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

        # Получение списка задач для уведомления об удалении
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

        # Диалоговое окно удаления категории и задач в ней
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
            # Удаление категории и задач в ней

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
        Удаление задачи
        """

        # Получение id задачи
        task = self.sender()
        task_id = task.objectName().split('_')[1]

        # Диалогове окно удаления задачи
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
            # Удаление задачи

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
        # Загрузка настроек

        settings_file = open('settings.json')
        settings_data = json.load(
            settings_file
        )

        # Установка настроек в GUI
        in_tray = settings_data.get('in_tray')
        notifications = settings_data.get('notifications')

        self.in_tray_option.setChecked(in_tray)
        self.notifications_option.setChecked(notifications)

    def change_settings(self):
        """
        Изменение настроек
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
        Уведомление с мотивирующей цитатой
        """
        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Information)
        message_box.setWindowTitle(
            'Цитата'
        )
        message_box.setText(
            random_quotation()
        )

        message_box.exec_()

    def show_deadline_msg(self, signal_data):
        """
        Показ уведомления о дедлайне задачи. Работает только при активированныз уведомлениях
        """
        if not self.notifications_option.isChecked():
            return None

        notification = QMessageBox()
        notification.setWindowTitle(
            'Task manager'
        )
        notification.setText(
            f'До дедлайна задачи "{signal_data[0]}" осталось {signal_data[1]} минут(a)'
        )
        notification.setIcon(
            notification.Information
        )
        notification.exec_()

    def closeEvent(self, event):
        # Если выбрано "Свернуть в трей", то окно сворачивается в трей
        # если не выбрано, то закрывается
        # сворачивание работает только при активированном сворачивании

        if self.in_tray_option.isChecked():
            event.ignore()
            self.hide()
            app.setQuitOnLastWindowClosed(False)

        else:
            app.setQuitOnLastWindowClosed(True)


class TaskReminder(QThread):
    """
    Поток, проверяющий дедлайны задач
    """

    notification_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__(parent=app)

        self.tasks = self.get_names_and_dates()
        self.notifications_list = list()

    def get_names_and_dates(self) -> dict:
        """
        Получение задач, их статуса и дедлайна
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
            # Определение близости дедлайна задачи
            near = deadline - now
            near_days = near.days

            if near_days == 0:
                near_minutes = int(near.total_seconds() // 60)

                if near_minutes > 0 and near_minutes <= 15:
                    # Уведомление о дедлайне, если о нём еще не уведомили

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
