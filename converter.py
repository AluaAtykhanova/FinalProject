import os

def rename_file(file_path):
    """
    Функция для переименования файла, изменяя его расширение на .mp3.

    Параметры:
    - file_path (str): Путь к файлу, который требуется переименовать.

    Возвращает:
    - str: Новый путь к переименованному файлу.
    """
    try:
        # Получаем список элементов пути
        path_elements = os.path.split(file_path)
        print(f"Converter.py 1. {path_elements}")

        # Разделяем имя файла и расширение
        base_name, extension = os.path.splitext(path_elements[1])

        # Изменяем только расширение на .mp3
        new_path_elements = path_elements[:-1] + (f"{base_name}.mp3",)
        print(f"2. {new_path_elements}")

        # Собираем новый путь
        new_path = os.path.join(*new_path_elements)
        print(f"3. {new_path}")

        # Переименовываем файл
        os.rename(file_path, new_path)
        print(f"Файл успешно переименован: {file_path} -> {new_path}")
        return new_path
    except Exception as e:
        print(f"Ошибка при переименовании файла: {e}")
        return None

# Пример использования
# file_path = '/home/alua/FinalProject/ПРОХОДИМ ОТОМЭ ТАРЕЛКИ.mp4'
# rename_file(file_path)
