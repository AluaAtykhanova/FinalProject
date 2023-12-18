import sqlite3

def create_table():
    """
    Создает таблицу video_info в базе данных, если она не существует.
    Возвращает курсор и соединение с базой данных.
    """
    conn = sqlite3.connect('video_info.db')  # Устанавливает соединение с базой данных
    cursor = conn.cursor()  # Создает объект курсора для взаимодействия с базой данных

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_time TEXT,
            video_url TEXT,
            sender_id INTEGER,
            file_id INTEGER
        )
    ''')
    conn.commit()
    return cursor, conn

# bot.py

async def find_and_send_file_id_from_db(client, video_url, chat_id, cursor, conn):
    """
    Ищет file_id по video_url в базе данных и отправляет его клиенту.
    Возвращает 1, если найден, и 0 в противном случае.
    """
    try:
        cursor.execute('''
            SELECT file_id FROM video_info
            WHERE video_url = ?
        ''', (video_url,))
        result = cursor.fetchone()

        if result:
            file_id = result[0]
            await client.send_message(chat_id, file=file_id)
            return 1
    except Exception as e:
        print(f"Error while searching for file_id: {str(e)}")

def save_video_info_to_db(current_datetime, video_url, sender_id, send_file_id, cursor, conn):
    """
    Сохраняет информацию о видео в базе данных.
    Предполагается, что у вас уже есть курсор и соединение с базой данных.
    """
    cursor.execute('''
        INSERT INTO video_info (date_time, video_url, sender_id, file_id)
        VALUES (?, ?, ?, ?)
    ''', (current_datetime, video_url, sender_id, send_file_id))
    conn.commit()
    # cursor.close()
