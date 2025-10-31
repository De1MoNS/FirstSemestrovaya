from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PyQt6.QtGui import QColor


class MoviesTableModel(QAbstractTableModel):
    def __init__(self, movies=None):
        super().__init__()
        self.movies = movies or []
        self.headers = ['Название', 'Год', 'Жанр', 'Режиссер', 'Рейтинг', 'Просмотрено']

    def rowCount(self, parent=None):
        # возвращает кол-во строк в модели
        return len(self.movies)

    def columnCount(self, parent=None):
        # возвращает кол-во столбцов в модели
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.movies):
            return None

        movie = self.movies[index.row()]
        column = index.column()

        # отображает основной текст в ячейке
        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0:
                return movie.get('title', '')
            elif column == 1:
                return str(movie.get('year', ''))
            elif column == 2:
                return movie.get('genre_name', 'Не указан')
            elif column == 3:
                return movie.get('director', 'Не указан')
            elif column == 4:
                rating = movie.get('rating')
                return f"{rating:.1f}" if rating else "-"
            elif column == 5:
                return "✓" if movie.get('is_watched') else "✖"

        # выравнивание текста
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if column in [1, 4, 5]:
                return Qt.AlignmentFlag.AlignCenter

        # цвет текста для рейтинга
        elif role == Qt.ItemDataRole.ForegroundRole:
            if column == 4:
                rating = movie.get('rating')
                if rating:
                    if rating >= 8:
                        return QColor('#4CAF50')  # зеленый
                    elif rating >= 6:
                        return QColor('#FFC107')  # желтый
                    else:
                        return QColor('#F44336')  # красный

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        # возвращает данные для заголовков таблицы
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return None

    def update_data(self, movies):
        self.beginResetModel()  # сообщает об изменении данных
        self.movies = movies  # заменяет список
        self.endResetModel()  # сообщает об завершении изменений

    def get_movie(self, row):
        if 0 <= row < len(self.movies):
            return self.movies[row]
        return {}
