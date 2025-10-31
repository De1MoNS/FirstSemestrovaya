import os
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QMessageBox, QMenu, QFileDialog)
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtCore import Qt
from PyQt6.uic import loadUiType

from models import MoviesTableModel
from movie_dialog import MovieDialog

UI_PATH = os.path.join(os.path.dirname(__file__), 'main_window.ui')
Ui_MainWindow, _ = loadUiType(UI_PATH)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.movies_model = MoviesTableModel()  # модель данных

        self.setupUi(self)
        self.setup_connections()
        self.load_initial_data()

    def setup_connections(self):
        self.addMovieBtn.clicked.connect(self.add_movie)
        self.editMovieBtn.clicked.connect(self.edit_selected_movie)
        self.deleteMovieBtn.clicked.connect(self.delete_selected_movie)
        self.refreshBtn.clicked.connect(self.refresh_data)

        self.searchEdit.textChanged.connect(self.on_filters_changed)
        self.genreCombo.currentIndexChanged.connect(self.on_filters_changed)
        self.yearFromSpin.valueChanged.connect(self.on_filters_changed)
        self.yearToSpin.valueChanged.connect(self.on_filters_changed)
        self.watchedCombo.currentIndexChanged.connect(self.on_filters_changed)

        self.tabWidget.currentChanged.connect(self.on_tab_changed)
        self.moviesTable.doubleClicked.connect(self.edit_selected_movie)
        self.moviesTable.customContextMenuRequested.connect(self.show_context_menu)

        # горячие клавиши
        add_action = QAction(self)
        add_action.setShortcut(QKeySequence("Ctrl+N"))
        add_action.triggered.connect(self.add_movie)
        self.addAction(add_action)

        edit_action = QAction(self)
        edit_action.setShortcut(QKeySequence("Ctrl+E"))
        edit_action.triggered.connect(self.edit_selected_movie)
        self.addAction(edit_action)

        delete_action = QAction(self)
        delete_action.setShortcut(QKeySequence("Delete"))
        delete_action.triggered.connect(self.delete_selected_movie)
        self.addAction(delete_action)

        refresh_action = QAction(self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self.refresh_data)
        self.addAction(refresh_action)

    def load_initial_data(self):
        self.yearFromSpin.setRange(1900, datetime.now().year)
        self.yearToSpin.setRange(1900, datetime.now().year)
        self.yearFromSpin.setValue(1900)
        self.yearToSpin.setValue(datetime.now().year)

        self.watchedCombo.addItems(["Все", "Да", "Нет"])

        # подключает модель данных к таблице фильмов
        self.moviesTable.setModel(self.movies_model)  # использует существующую модель
        self.moviesTable.setSelectionBehavior(self.moviesTable.SelectionBehavior.SelectRows)
        self.moviesTable.setAlternatingRowColors(True)
        self.moviesTable.horizontalHeader().setSectionResizeMode(self.moviesTable.horizontalHeader().ResizeMode.Stretch)
        self.moviesTable.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # создает контекстное меню
        self.context_menu = QMenu(self)
        self.edit_action = self.context_menu.addAction("Редактировать")
        self.delete_action = self.context_menu.addAction("Удалить")
        self.mark_watched_action = self.context_menu.addAction("Отметить просмотренным")
        self.mark_unwatched_action = self.context_menu.addAction("Отметить непросмотренным")

        # подключает действия контекстного меню
        self.edit_action.triggered.connect(self.edit_selected_movie)
        self.delete_action.triggered.connect(self.delete_selected_movie)
        self.mark_watched_action.triggered.connect(self.mark_watched)
        self.mark_unwatched_action.triggered.connect(self.mark_unwatched)

        # загрузка жанров в выпадающий список
        self.load_genres()
        # первичная загрузка фильмов
        self.refresh_data()

    # получаает список жанров из базы данных
    def load_genres(self):
        genres = self.db_manager.get_genres()
        self.genreCombo.clear()
        self.genreCombo.addItem("Все жанры", 0)
        for genre in genres:
            self.genreCombo.addItem(genre['name'], genre['id'])

    # обновляет список фильмов по фильтрам
    def refresh_data(self):
        try:
            filters = {}

            # поиск по названию или режиссеру
            search_text = self.searchEdit.text().strip()
            if search_text:
                filters['search'] = search_text

            # фильтр по жанру
            genre_id = self.genreCombo.currentData()
            if genre_id != 0:
                filters['genre_id'] = genre_id

            # фильтр по году выпуска
            year_from = self.yearFromSpin.value()
            year_to = self.yearToSpin.value()
            if year_from > 1900:
                filters['year_from'] = year_from
            if year_to < datetime.now().year:
                filters['year_to'] = year_to

            # фильтр по статусу просмотра
            watched_filter = self.watchedCombo.currentText()
            if watched_filter == "Да":
                filters['is_watched'] = True
            elif watched_filter == "Нет":
                filters['is_watched'] = False

            # берет фильмы из базы данных с фильтрами
            movies = self.db_manager.get_movies(filters)
            self.movies_model.update_data(movies)

            # обновляет вкладку статистика, если она открыта
            if self.tabWidget.currentIndex() == 1:
                self.update_statistics()

            # кол-во фильмов в статусной строке
            self.statusbar.showMessage(f"Загружено фильмов: {len(movies)}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить данные: {str(e)}")

    def update_statistics(self):
        try:
            stats = self.db_manager.get_statistics()

            # обновление числовых меток
            self.totalMoviesValue.setText(str(stats['total_movies']))
            self.watchedMoviesValue.setText(str(stats['watched_movies']))
            self.avgRatingValue.setText(f"{stats['avg_rating'] or 0:.1f}")

            # статистика
            genre_stats = "\n".join([f"• {g['name']}: {g['count']} фильмов" for g in stats['genres'] if g['count'] > 0])
            stats_text = f"""СТАТИСТИКА КОЛЛЕКЦИИ

            Всего фильмов: {stats['total_movies']}
            Просмотрено: {stats['watched_movies']}
            Средний рейтинг: {stats['avg_rating'] or 0:.1f}

            РАСПРЕДЕЛЕНИЕ ПО ЖАНРАМ:
            {genre_stats}"""

            self.statsText.setPlainText(stats_text)

        except Exception as e:
            print(f"Ошибка статистики: {e}")

    def add_movie(self):
        dialog = MovieDialog(self.db_manager, self)
        if dialog.exec() == MovieDialog.DialogCode.Accepted:
            self.refresh_data()
            QMessageBox.information(self, "Успех", "Фильм добавлен!")

    def edit_selected_movie(self):
        selection = self.moviesTable.selectionModel().selectedRows()
        if not selection:
            QMessageBox.warning(self, "Предупреждение", "Выберите фильм")
            return

        movie = self.movies_model.get_movie(selection[0].row())
        if movie:
            dialog = MovieDialog(self.db_manager, self, movie)
            if dialog.exec() == MovieDialog.DialogCode.Accepted:
                self.refresh_data()
                QMessageBox.information(self, "Успех", "Фильм обновлен!")

    def delete_selected_movie(self):
        selection = self.moviesTable.selectionModel().selectedRows()
        if not selection:
            QMessageBox.warning(self, "Предупреждение", "Выберите фильм")
            return

        movie = self.movies_model.get_movie(selection[0].row())
        if movie:
            reply = QMessageBox.question(
                self, "Подтверждение",
                f"Удалить фильм \"{movie['title']}\"?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                if self.db_manager.delete_movie(movie['id']):
                    self.refresh_data()
                    QMessageBox.information(self, "Успех", "Фильм удален!")

    def mark_watched(self):
        self._mark_watched_status(True)

    def mark_unwatched(self):
        self._mark_watched_status(False)

    def _mark_watched_status(self, watched):
        selection = self.moviesTable.selectionModel().selectedRows()
        if not selection:
            return

        movie = self.movies_model.get_movie(selection[0].row())
        if movie and self.db_manager.update_movie(movie['id'], is_watched=watched):
            self.refresh_data()
            status = "просмотренным" if watched else "непросмотренным"
            QMessageBox.information(self, "Успех", f"Фильм отмечен как {status}!")

    def show_context_menu(self, position):
        selection = self.moviesTable.selectionModel().selectedRows()
        if selection:
            movie = self.movies_model.get_movie(selection[0].row())
            is_watched = movie.get('is_watched', False)
            self.mark_watched_action.setVisible(not is_watched)
            self.mark_unwatched_action.setVisible(is_watched)
            self.context_menu.exec(self.moviesTable.mapToGlobal(position))

    def on_filters_changed(self):
        # перезагружает данные основываясь на фильтрах
        self.refresh_data()

    def on_tab_changed(self, index):
        # при переходе на вкладку статистика, обновляет ее
        if index == 1:
            self.update_statistics()

    def closeEvent(self, event):
        # закрытие соединения с базой данных, при завершении приложения
        self.db_manager.close()
        event.accept()
