import sys
from datetime import datetime

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel
from PyQt5.QtWidgets import QMainWindow, QApplication, QSpinBox,\
    QVBoxLayout, QLineEdit, QPlainTextEdit,\
    QDateTimeEdit, QPushButton, QLabel
from PyQt5 import uic

from design1 import Ui_MainWindow, StringBox

con = QSqlDatabase.addDatabase('QSQLITE')
con.setDatabaseName('db.sqlite3')


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle('Task manager')

        ui = Ui_MainWindow()
        ui.setupUi(self)

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

        self.change_btn.clicked.connect(
            self.create_task
        )

        self.next_page_btn.clicked.connect(
            self.plus_change_page
        )

        self.last_page_btn.clicked.connect(
            self.minus_change_page
        )

        self.set_all_tasks()

        for i in range(self.all_tasks.count()):
            widget = self.all_tasks.itemAt(i).widget()
            widget.clicked.connect(
                self.view_task
            )

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

        return True

    def get_all_tasks(self):
        if not con.open():
            print('db couldnt open')
            return None

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

        chunk_size = 4

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
        datetime = self.datetime.dateTime().toPyDateTime()

        status_id = con.exec(
            f'SELECT id FROM statuses WHERE name="{status}";'
        )
        status_id.first()

        category_id = con.exec(
            f'SELECT id FROM categories WHERE name="{category}";'
        )
        category_id.first()

        con.exec(
            f'INSERT INTO tasks (name, description, category_id, status_id, deadline) VALUES ("{name}", "{description}", {category_id.value(0)}, {status_id.value(0)}, datetime("{str(datetime)}"));'
        )

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

    def view_task(self):
        task_id = self.sender().objectName().\
            split('_')[1]

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
