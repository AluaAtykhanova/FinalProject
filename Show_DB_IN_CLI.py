import sqlite3

# Подключение к базе данных
conn = sqlite3.connect('/home/alua/FinalProject/video_info_server.db')
cursor = conn.cursor()

# Извлечение данных из базы данных
cursor.execute("SELECT * FROM video_info")
rows = cursor.fetchall()

# Вывод данных в консоль
for row in rows:
    print(row)

# Закрытие соединения с базой данных
conn.close()
