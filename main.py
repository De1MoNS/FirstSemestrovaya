import sys
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow
from database import DatabaseManager


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Movie Manager")

    db_manager = DatabaseManager()
    db_manager.initialize_database()

    window = MainWindow(db_manager)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
