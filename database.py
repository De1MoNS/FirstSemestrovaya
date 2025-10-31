import sqlite3
import os
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path="movies.db"):
        self.db_path = db_path
        self.connection = None

    def connect(self):
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
        return self.connection

    def initialize_database(self):
        conn = self.connect()
        cursor = conn.cursor()

        # создает таблицу жанров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS genres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')

        # создает таблицу фильмов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                year INTEGER NOT NULL,
                genre_id INTEGER,
                director TEXT,
                rating REAL,
                description TEXT,
                poster_path TEXT,
                is_watched BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (genre_id) REFERENCES genres (id)
            )
        ''')

        # если таблица пуста, добавляет стандартные жанры
        self._create_default_genres(cursor)
        conn.commit()

    def _create_default_genres(self, cursor):
        genres = ['Драма', 'Комедия', 'Боевик', 'Триллер', 'Ужасы',
                  'Фантастика', 'Фэнтези', 'Мелодрама', 'Приключения',
                  'Детектив', 'Исторический']

        # проверка, есть ли жанры в таблице
        cursor.execute("SELECT COUNT(*) FROM genres")
        if cursor.fetchone()[0] == 0:  # если нет, добавляем
            for genre in genres:
                cursor.execute('INSERT INTO genres (name) VALUES (?)', (genre,))

    def add_movie(self, title, year, genre_id, director=None, rating=None, description=None, poster_path=None):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO movies (title, year, genre_id, director, rating, description, poster_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, year, genre_id, director, rating, description, poster_path))

        conn.commit()
        return cursor.lastrowid

    def update_movie(self, movie_id, **kwargs):

        conn = self.connect()
        cursor = conn.cursor()

        updates = []
        params = []

        # формирует список полей, которым нужны обновления
        for field, value in kwargs.items():
            if value is not None:
                updates.append(f"{field} = ?")
                params.append(value)

        if not updates:
            return False

        params.append(movie_id)
        query = f"UPDATE movies SET {', '.join(updates)} WHERE id = ?"

        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0

    def delete_movie(self, movie_id):
        # удаляет фильм по ID
        conn = self.connect()
        cursor = conn.cursor()

        # получает данные фильма
        movie = self.get_movie(movie_id)
        if movie and movie['poster_path'] and os.path.exists(movie['poster_path']):
            try:
                os.remove(movie['poster_path'])  # удаляет файл постера
            except:
                pass

        cursor.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
        conn.commit()
        return cursor.rowcount > 0

    def get_movies(self, filters=None):
        # получает список фильмов с фильтрами
        conn = self.connect()
        cursor = conn.cursor()

        query = '''
            SELECT m.*, g.name as genre_name
            FROM movies m
            LEFT JOIN genres g ON m.genre_id = g.id
            WHERE 1=1
        '''
        params = []

        if filters:
            if filters.get('genre_id'):
                query += " AND m.genre_id = ?"
                params.append(filters['genre_id'])

            if filters.get('year_from'):
                query += " AND m.year >= ?"
                params.append(filters['year_from'])

            if filters.get('year_to'):
                query += " AND m.year <= ?"
                params.append(filters['year_to'])

            if filters.get('is_watched') is not None:
                query += " AND m.is_watched = ?"
                params.append(filters['is_watched'])

            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query += " AND (m.title LIKE ? OR m.director LIKE ?)"
                params.extend([search_term, search_term])

        query += " ORDER BY m.title"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_movie(self, movie_id):
        # получает один фильм по ID
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT m.*, g.name as genre_name
            FROM movies m
            LEFT JOIN genres g ON m.genre_id = g.id
            WHERE m.id = ?
        ''', (movie_id,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_genres(self):
        # получает список жанров
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM genres ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self):
        # получает статистику
        conn = self.connect()
        cursor = conn.cursor()

        # основная статистика
        cursor.execute('''
            SELECT 
                COUNT(*) as total_movies,
                COUNT(CASE WHEN is_watched THEN 1 END) as watched_movies,
                AVG(rating) as avg_rating
            FROM movies
        ''')
        stats = dict(cursor.fetchone())

        # распределение по жанрам
        cursor.execute('''
            SELECT g.name, COUNT(m.id) as count
            FROM genres g
            LEFT JOIN movies m ON g.id = m.genre_id
            GROUP BY g.id, g.name
            ORDER BY count DESC
        ''')
        stats['genres'] = [dict(row) for row in cursor.fetchall()]

        return stats

    def close(self):
        if self.connection:
            self.connection.close()
