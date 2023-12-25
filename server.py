import socket
import csv
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import sqlite3
import os

# Путь к файлу базы данных сервера
server_db_file_path = "/home/alua/FinalProject/video_info_server.db"
bot_db_file_path = "/home/alua/FinalProject/video_info.db"

class MyRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """
        Обработчик GET-запросов.
        """
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Hello, this is your server.")
        elif self.path == '/data':
            # Подключение к базе данных и отправка данных клиенту
            conn = sqlite3.connect(server_db_file_path)
            create_table(conn)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM video_info")
            rows = cursor.fetchall()
            response = "\n".join(str(row) for row in rows)
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(response.encode('utf-8', 'ignore'))
        elif self.path == '/close_server':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Server stopped.")
        else:
            self.send_error(404, 'Not Found')

    def do_POST(self):
        """
        Обработчик POST-запросов.
        """
        if self.path == '/data':
            content_length = int(self.headers['Content-Length'])
            # Читаем данные из тела запроса
            data = self.rfile.read(content_length).decode('utf-8')
            
            # Обработка данных (пример: вставка данных в базу данных)
            conn = sqlite3.connect(server_db_file_path)
            create_table(conn)
            cursor = conn.cursor()
            # Пример: разбор данных как CSV
            reader = csv.reader([data], delimiter=',')
            for row in reader:
                cursor.execute("INSERT INTO video_info (date_time, video_url, sender_id, file_id) VALUES (?, ?, ?, ?)", row)
            conn.commit()

            # Отправляем успешный ответ
            try:
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Data received and processed successfully.")
            except BrokenPipeError:
                print("Client closed the connection before response could be sent.")
        else:
            self.send_error(404, 'Not Found')

def create_table(conn):
    """
    Создает таблицу video_info в базе данных, если она не существует.
    """
    cursor = conn.cursor()
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

def copy_data(conn_source, conn_destination):
    """
    Копирует данные из одной базы данных в другую.
    """
    cursor_source = conn_source.cursor()
    cursor_destination = conn_destination.cursor()

    # Выбираем все данные из базы данных бота
    cursor_source.execute("SELECT * FROM video_info")
    rows = cursor_source.fetchall()

    # Вставляем скопированные данные в базу данных сервера
    for row in rows:
        cursor_destination.execute("INSERT INTO video_info (id,date_time, video_url, sender_id, file_id) VALUES (?,?, ?, ?, ?)", row)

    # Сохраняем изменения в базе данных сервера
    conn_destination.commit()

# Код для запуска и работы сервера
def start_server(stop_event):
    try:
        # Проверка существования файла перед его удалением
        if os.path.exists(server_db_file_path):
            os.remove(server_db_file_path)
            print(f"File {server_db_file_path} removed successfully")
        else:
            print(f"File {server_db_file_path} does not exist")

        # Создаем соединение с базой данных сервера (video_info_server.db)
        conn_server = sqlite3.connect(server_db_file_path)
        create_table(conn_server)

        # Создаем соединение с базой данных бота (video_info.db)
        conn_bot = sqlite3.connect(bot_db_file_path)

        # Копируем данные из базы данных бота в базу данных сервера
        copy_data(conn_bot, conn_server)

        # Запуск веб-сервера
        server = HTTPServer(('localhost', 5555), MyRequestHandler)
        print("[INFO] Server listening on port 5555...")

        # Ожидаем новое подключение
        while not stop_event.is_set():
            server.handle_request()
            
    except Exception as e:
        print(f"Error in start_server: {str(e)}")
    finally:
        # Закрытие сервера
        server.server_close()
        # Ваш код завершения работы сервера...

# Код для того чтобы бот отправил данные на сервер
def send_data_to_server(data):
    """
    Отправляет данные на сервер с использованием простого HTTP-протокола.
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client.connect(('localhost', 5555))
        # Используем POST-запрос и передаем данные в теле запроса
        request = f"POST /data HTTP/1.1\r\nHost: localhost\r\nContent-Length: {len(data)}\r\n\r\n{data}"
        client.sendall(request.encode())
        
        # Set a timeout for receiving data to avoid indefinite waiting
        client.settimeout(5)  # Set the timeout to 5 seconds (adjust as needed)
        
        response = client.recv(1024)
        print(response.decode())
    except socket.timeout:
        print("Socket timeout. No response received.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()  # Всегда закрываем соединение, даже если произошла ошибка

