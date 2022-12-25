import sys
from datetime import datetime

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel
from PyQt5.QtWidgets import QMainWindow, QApplication, QSpinBox,\
    QVBoxLayout, QLineEdit, QPlainTextEdit,\
    QDateTimeEdit, QPushButton, QLabel, QHBoxLayout,\
    QScrollArea, QListWidget, QListWidgetItem
from PyQt5 import uic

from design2 import Ui_MainWindow, StringBox

con = QSqlDatabase.addDatabase('QSQLITE')
con.setDatabaseName('db.sqlite3')


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle('Task manager')

        ui = Ui_MainWindow()
        ui.setupUi(self)

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

        self.set_all_tasks()
        self.set_categories()
        self.selected_task = False

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

    def set_all_tasks(self):
        all_tasks_list = self.get_all_tasks()

        try:
            page_tasks_list = all_tasks_list[
                self.tasks_page
            ]

        except:
            return False

        while self.all_tasks.count():
            child = self.all_tasks.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for task in page_tasks_list:
            button = QPushButton()
            self.all_tasks.addWidget(button)

            for key, value in task.items():
                if key == 'name':
                    button.setText(value)

                elif key == 'id':
                    button.setObjectName(f'task_{value}')
                    print(value)

        for i in range(self.all_tasks.count()):
            widget = self.all_tasks.itemAt(i).widget()
            widget.clicked.connect(
                self.view_task
            )

        return True

    def get_all_tasks(self):
        all_tasks_query = con.exec(
            'SELECT * FROM tasks;'
        )

        tasks_list = list()

        while all_tasks_query.next():
            tasks_list.append(
                {
                    'id': all_tasks_query.value(0),
                    'name': all_tasks_query.value(1),
                    'date': all_tasks_query.value(4)
                }
            )

        chunk_size = 17

        final_list = list()

        for i in range(0, len(tasks_list), chunk_size):
            final_list.append(tasks_list[i:i+chunk_size])

        return final_list

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
        self.datetime.setDate(deadline_datetime)

    def unselect_task(self):
        self.selected_task = False
        self.name_inp.setText('Название задачи')
        self.description_inp.setPlainText('Описание задачи')
        self.category_inp.setValue(1)
        self.status_inp.setValue(1)

        self.datetime.setDate(
            datetime.strptime(
                '01-01-2000 0:00', '%d-%m-%Y %H:%M'
            )
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
