import subprocess
import sys
import os


def create_executable():
    print("Создание .exe файла")

    try:
        # команда PyInstaller с добавлением UI файлов
        result = subprocess.run([
            'pyinstaller',
            '--onefile',
            '--windowed',
            '--name=MovieManager',
            '--add-data', 'main_window.ui;.',  # добавляет UI файлы
            '--add-data', 'movie_dialog.ui;.',
            'main.py'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✓ .exe файл создан")
            print("Находится в папке 'dist/MovieManager.exe'")
        else:
            print("✖ Ошибка при создании .exe файла")
            print(result.stderr)

    except Exception as e:
        print(f"✖ Ошибка: {e}")
        print("Убедитесь, что PyInstaller установлен: pip install pyinstaller")


if __name__ == '__main__':
    create_executable()
