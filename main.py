import sys
from time import sleep

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel
from PyQt5.QtWidgets import QMainWindow, QApplication, QSpinBox,\
    QVBoxLayout, QLineEdit, QPlainTextEdit,\
    QDateTimeEdit, QPushButton, QLabel
from PyQt5 import uic

from design import Ui_MainWindow, StringBox

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

        self.set_all_tasks()

    def set_all_tasks(self):
        all_tasks_list = self.get_all_tasks()

        for task in all_tasks_list:
            button = QPushButton()
            self.all_tasks.addWidget(button)

            for key, value in task.items():
                if key == 'name':
                    button.setText(value)

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

        return tasks_list

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

        print(name)
        print(description)
        print(category)
        print(status)
        print(type(datetime))

        status_id = con.exec(
            f'SELECT id FROM statuses WHERE name="{status}";'
        )
        status_id.first()

        category_id = con.exec(
            f'SELECT id FROM categories WHERE name="{category}";'
        )
        category_id.first()

        print(category_id.value(0), status_id.value(0))

        con.exec(
            f'INSERT INTO tasks (name, category_id, status_id, deadline) VALUES ("{name}", {category_id.value(0)}, {status_id.value(0)}, datetime("{str(datetime)}"));'
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
        #         category_id INTEGER NOT NULL REFERENCES categories (id) ON DELETE CASCADE ON UPDATE CASCADE,
        #         status_id INTEGER NOT NULL REFERENCES statuses (id) ON DELETE CASCADE ON UPDATE CASCADE,
        #         deadline DATETIME
        #     );
        #     """
        # )

        print('clicked')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # ui = Ui_MainWindow()
    window = MainWindow()
    # ui.setupUi(window)
    # window.load_elements()
    window.show()
    sys.exit(app.exec_())
