import logging
import psutil
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import traceback

# Конфигурация
TOKEN = "6563553728:AAGVhTKvRsQ2R6PBLuzxMRPCt-EGd-K5Ny4"
CHAT_ID = "812761972"

# Функция для отправки сообщений в Telegram
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {
        "chat_id": CHAT_ID,
        "text": message
    }
    response = requests.post(url, data=params)
    if response.status_code != 200:
        logging.error(f"Ошибка при отправке уведомления: {response.text}")

# Функция для проверки наличия процесса
def check_process(process_name: str):
    """Проверка запущен ли процесс с данным именем."""
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        if process_name.lower() in proc.info['name'].lower():
            return proc.info['pid']  # Возвращаем ID процесса
    return None  # Процесс не найден

# Функция мониторинга процессов
def monitor_process(process_name: str):
    """Мониторинг процесса с уведомлением при сбое."""
    pid = check_process(process_name)
    if not pid:
        send_telegram_message(f"⚠️ Процесс {process_name} упал или не запущен!")
    else:
        logging.info(f"Процесс {process_name} работает, PID: {pid}")

# Функция для обработки ошибок
def handle_error():
    try:
        # Твой код, где может произойти ошибка
        raise ValueError("Пример ошибки!")
    except Exception as e:
        error_message = f"❌ Ошибка: {str(e)}\n"
        error_message += f"Подробнее:\n{traceback.format_exc()}"
        send_telegram_message(error_message)

# Инициализация планировщика задач для мониторинга
def start_monitoring():
    scheduler = BackgroundScheduler()
    # Периодически проверяем процесс
    scheduler.add_job(monitor_process, 'interval', minutes=1, args=['example_process_name'])
    scheduler.start()