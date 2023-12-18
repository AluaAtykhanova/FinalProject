import os

async def delete_file(file_path):
    """
    Асинхронная функция для удаления файла.

    Параметры:
    - file_path (str): Путь к файлу, который требуется удалить.

    Возвращает:
    - None
    """
    try:
        # Попытка удаления файла
        os.remove(file_path)
        print(f'Файл {file_path} успешно удален.')
    except OSError as e:
        print(f'Ошибка при удалении файла {file_path}: {e}')
