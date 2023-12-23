from pytube import YouTube
from pytube.exceptions import LiveStreamError
from tokens import TOKEN, TARGET_CHAT_ID, api_id, api_hash
from download import download_and_rename_audio 
from telethon import TelegramClient, events, types
import requests
from delete import delete_file 
from datetime import datetime 
from telethon.tl.types import Document
from telethon.utils import pack_bot_file_id
from database import create_table , find_and_send_file_id_from_db, save_video_info_to_db
from server import send_data_to_server, start_server
import asyncio
import threading


log_file_path = 'log.txt'  # Замените на путь к вашему файлу логов

# Используем create_table из database.py и сохраняем переменные
cursor, conn = create_table()

async def main():
    # Установка соединения с TelegramClient асинхронным способом
    async with TelegramClient('anon', api_id, api_hash) as client:
        # Получаем новые сообщения от пользователей
        @client.on(events.NewMessage)
        # Функция обработки новых запросов от пользователей
        async def my_event_handler(event):
            try:

                yt = YouTube(event.text)

                # Получаем текущую дату и время
                current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                
                if not event.text.startswith(("https://www.youtube.com/","https://youtube.com/","https://youtu.be/")):
                    await client.send_message(event.chat_id, 'Извините, это не ссылка на YouTube')
                    # Логгирование ошибки
                    with open(log_file_path, 'a') as log_file:
                        log_file.write(f"[{current_datetime}] Error: {event.text}, No YouTube URL\n")
                    return  # Пропускаем запрос, так как аудиодорожка недоступна

                # Поиск и отправка заголовка для ссылки из базы данных
                if (await find_and_send_file_id_from_db(client, event.text, event.chat_id,cursor,conn)):
                    return
                print("Прекратил поиск ссылки")

                # Проверяем наличие аудиодорожки
                if not yt.streams.filter(only_audio=True):
                    await client.send_message(event.chat_id, 'Извините, но это видео не поддерживает скачивание аудио.')
                    # Логгирование ошибки
                    with open(log_file_path, 'a') as log_file:
                        log_file.write(f"[{current_datetime}] Error: {event.text}, No audio stream available\n")
                    return  # Пропускаем запрос, так как аудиодорожка недоступна

                # Отправляем сообщение о начале загрузки
                message = await client.send_message(event.chat_id, 'Загружаю файл...')

                # Скачиваем видео и переименовываем его
                result = download_and_rename_audio(event.text)

                # Получение объекта с превью видео
                thumbnail_url = yt.thumbnail_url

                # Сохранение превью на локальный диск
                thumbnail_data = requests.get(thumbnail_url).content
                with open('thumbnail.jpg', 'wb') as file:
                    file.write(thumbnail_data)

                async def progress_callback(current, total, message):
                    percent = (current / total) * 100
                    if int(percent) % 5 == 0:
                        await client.edit_message(event.chat_id, message.id, f'Выгружаю аудио в телеграмм: {percent:.2f}%')

                #Отправляем аудио-сообщение
                print(f"Sending audio file...")
                send_file = await client.send_file(event.chat_id, result, caption="Here's an audio message.", thumb=thumbnail_data, attributes=[
                    types.DocumentAttributeAudio(
                        title=yt.title,
                        performer=yt.author,
                        duration= 0
                    )
                ],
                progress_callback=lambda current, total: progress_callback(current, total, message)
                )

                print("Audio file send successfully.")
                # Получаем айди отправленного файла, 
                send_file_id = pack_bot_file_id(send_file.media.document)

                # Сохраняем информацию о видеоролике в файл
                with open(log_file_path, 'a') as log_file:
                    log_file.write(f"Date and Time: {current_datetime}\n")
                    log_file.write(f"Video URL: {event.text}\n")
                    log_file.write(f"Sender ID: {event.sender_id}\n")
                    log_file.write(f"Audio File_file_id: {send_file_id}\n")
                    log_file.write("\n")

                # Сохраняем данные в базе данных
                save_video_info_to_db(current_datetime,event.text,event.sender_id,send_file_id,cursor,conn)
                # Собираем данные для отправки на сервер
                data_to_send = f"{current_datetime},{event.text},{event.sender_id},{send_file_id}"
                print(f"data_to_send: {data_to_send}")

                # Отправляем данные на сервер
                send_data_to_server(data_to_send)

                print(f"Заголовок, сохраненный в базе данных: {send_file_id}")

                await delete_file(result)

            except LiveStreamError:
                await client.send_message(event.chat_id, 'Извините, но это видео является прямым эфиром и не может быть загружено.')
                # Записываем результат в лог-файл
                with open(log_file_path, 'a') as log_file:
                    log_file.write(f"[{current_datetime}] Error: Live stream - {event.text}\n")
                    log_file.write("\n")

            except Exception as e:
                # Обрабатываем возможные ошибки
                await client.send_message(event.chat_id, f'Извините, произошла ошибка,')

                # Записываем результат ошибки в лог-файл
                with open(log_file_path, 'a') as log_file:
                    log_file.write(f"[{current_datetime}] Error: {event.text}, {str(e)}\n")
                    log_file.write("\n")

        await client.start()
        print("Bot has started.")

        # Бесконечный цикл ввода
        while True:
            user_input = await asyncio.to_thread(input, "Type '.' and press Enter to stop.")
            if user_input == ".":
                # При получении сигнала остановки сервера
                stop_event.set()
                break

        print("Stopping the bot.")

if __name__ == "__main__":
    stop_event = threading.Event()

    # Создаем и запускаем поток сервера
    server_thread = threading.Thread(target=start_server, args=(stop_event,))
    server_thread.start()

    # Запускаем асинхронный код бота в основном потоке
    asyncio.run(main())

    # Отправляем HTTP-запрос на сервер после завершения работы бота
    response = requests.get('http://localhost:5555/close_server')  # Пример URL-адреса, на который отправляется запрос
    print(response.text)  # Пример обработки ответа от сервера

    server_thread.join()
# timeout=1
    print("Program terminated.")