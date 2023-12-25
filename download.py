from pytube import YouTube
import time
from converter import rename_file

def download_and_rename_audio(url):
    """
    Функция для скачивания аудио из YouTube и переименования полученного файла.

    Параметры:
    - url (str): Ссылка на видео в YouTube.

    Возвращает:
    - str: Путь к переименованному аудиофайлу.
    """
    # Засекаем начальное время
    start_time = time.time()

    try:
        # Создаем объект YouTube и получаем аудио-стрим
        yt = YouTube(url)
        audio_file_path = yt.streams.filter(only_audio=True).first().download()
        print(f"Аудиофайл успешно скачан: {audio_file_path}")

        # Переименовываем аудиофайл
        result = rename_file(audio_file_path)
        print(f"Файл успешно переименован: {result}")

        return result
    except Exception as e:
        print(f"Ошибка при скачивании и переименовании: {e}")

    # Засекаем конечное время
    end_time = time.time()

    # Вычисляем время выполнения
    execution_time = end_time - start_time
    print(f"Программа выполнена за {execution_time} секунд")
