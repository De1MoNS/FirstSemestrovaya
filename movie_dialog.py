import os
from datetime import datetime
from PyQt6.QtWidgets import QDialog, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.uic import loadUiType

UI_PATH = os.path.join(os.path.dirname(__file__), 'movie_dialog.ui')
Ui_MovieDialog, _ = loadUiType(UI_PATH)


class MovieDialog(QDialog, Ui_MovieDialog):
    def __init__(self, db_manager, parent=None, movie_data=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.movie_data = movie_data
        self.is_edit_mode = movie_data is not None
        self.poster_path = None

        self.setupUi(self)

        self.yearSpin.setRange(1900,2025)

        self.setup_connections()
        self.load_genres()

        if self.is_edit_mode:
            self.load_movie_data()
            self.setWindowTitle("Редактирование фильма")
            self.titleLabel.setText("Редактирование фильма")

    def setup_connections(self):
        self.buttonBox.accepted.connect(self.save_movie)
        self.buttonBox.rejected.connect(self.reject)
        self.loadPosterBtn.clicked.connect(self.load_poster)

    def load_genres(self):
        # загружает список жанров из базы данных, добавляя их в список
        genres = self.db_manager.get_genres()
        self.genreCombo.clear()
        self.genreCombo.addItem("Не выбран", 0)
        for genre in genres:
            self.genreCombo.addItem(genre['name'], genre['id'])

    def load_movie_data(self):
        if self.movie_data:
            # заполнение текстовых и числовых полей
            self.titleEdit.setText(self.movie_data.get('title', ''))
            self.yearSpin.setValue(self.movie_data.get('year', datetime.now().year))
            self.directorEdit.setText(self.movie_data.get('director', ''))
            self.ratingSpin.setValue(self.movie_data.get('rating', 0) or 0)
            self.descriptionEdit.setPlainText(self.movie_data.get('description', ''))
            self.watchedCheck.setChecked(self.movie_data.get('is_watched', False))

            # установка выбранного жанра
            genre_id = self.movie_data.get('genre_id')
            if genre_id:
                for i in range(self.genreCombo.count()):
                    if self.genreCombo.itemData(i) == genre_id:
                        self.genreCombo.setCurrentIndex(i)
                        break
            # если указан путь и сущ-ет файл, загружаем постер
            poster_path = self.movie_data.get('poster_path')
            if poster_path and os.path.exists(poster_path):
                self.load_poster_image(poster_path)
                self.poster_path = poster_path

    def load_poster(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите постер", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.load_poster_image(file_path)
            self.poster_path = file_path

    def load_poster_image(self, file_path):
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            # масштабирует и сохраняет соотношение сторона
            scaled_pixmap = pixmap.scaled(100, 150, Qt.AspectRatioMode.KeepAspectRatio)
            self.posterImageLabel.setPixmap(scaled_pixmap)
            self.posterImageLabel.setText("")  # убирает текст

    def save_movie(self):
        # проверка названия
        title = self.titleEdit.text().strip()
        if not title:
            QMessageBox.warning(self, "Ошибка", "Введите название фильма")
            return
        # сбор данных
        year = self.yearSpin.value()
        genre_id = self.genreCombo.currentData()
        if genre_id == 0:
            genre_id = None

        director = self.directorEdit.text().strip() or None
        rating = self.ratingSpin.value() or None
        description = self.descriptionEdit.toPlainText().strip() or None
        is_watched = self.watchedCheck.isChecked()

        try:
            if self.is_edit_mode:
                # режим редактирования
                success = self.db_manager.update_movie(
                    self.movie_data['id'],
                    title=title,
                    year=year,
                    genre_id=genre_id,
                    director=director,
                    rating=rating,
                    description=description,
                    poster_path=self.poster_path,
                    is_watched=is_watched
                )
            else:
                # режим добавления
                movie_id = self.db_manager.add_movie(
                    title=title,
                    year=year,
                    genre_id=genre_id,
                    director=director,
                    rating=rating,
                    description=description,
                    poster_path=self.poster_path
                )
                success = movie_id is not None

                if success and is_watched:
                    self.db_manager.update_movie(movie_id, is_watched=True)
            # закрывает диалог, при успешном сохранении
            if success:
                self.accept()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить фильм")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")

