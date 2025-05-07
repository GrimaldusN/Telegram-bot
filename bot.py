import subprocess
import logging
import psutil
import pyperclip
import shutil
import pyautogui
import io
import os
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

AUTHORIZED_USER_ID = 812761972
cut_buffer = None
copy_buffer = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_program_running(program_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if program_name.lower() in proc.info['name'].lower():
            return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    await update.message.reply_text("Бот запущен. Жду команду!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    help_text = (
        "Доступные команды:\n"
        "/start - Запускает бота\n"
        "/help - Показывает этот список\n"
        "/status - Информация о состоянии системы (CPU, память, диск)\n"
        "/find_process <имя процесса> - Ищет процессы по имени\n"
        "/screenshot - Сделать скриншот экрана и отправить\n"
        "/open <программа> - Открывает указанную программу\n"
        "/close <имя процесса> - Закрывает указанную программу\n"
        "/copy_text <текст> - Копирует текст в буфер обмена\n"
        "/paste_text - Вставляет текст из буфера обмена\n"
        "/list_files <путь> - Список файлов в указанной директории\n"
        "/search <имя_файла> - Ищет файлы по имени на диске C\n"
        "/send_file <путь к файлу> - Отправляет файл в Telegram\n"
        "/copy_file <файл> - Копирует файл в буфер\n"
        "/cut_file <путь к файлу> - Вырезает файл\n"
        "/paste_file <путь к папке> - Вставляет файл в папку\n"
        "/clipboard_status - Показывает содержимое буфера\n"
        "/restart - Перезагрузить систему\n"
        "/shutdown - Выключить систему\n"
    )
    await update.message.reply_text(help_text)

async def system_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return

    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    status = (
        f"Загрузка процессора: {cpu_usage}%\n"
        f"Использование памяти: {memory}%\n"
        f"Использование диска: {disk}%"
    )
    await update.message.reply_text(status)

async def find_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return

    query = ' '.join(context.args).lower()
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        if query in proc.info['name'].lower():
            processes.append(f"PID: {proc.info['pid']} - {proc.info['name']}")

    if processes:
        await update.message.reply_text("\n".join(processes))
    else:
        await update.message.reply_text(f"Процессы с именем '{query}' не найдены.")

async def take_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return

    screenshot = pyautogui.screenshot()
    byte_io = io.BytesIO()
    screenshot.save(byte_io, format='PNG')
    byte_io.seek(0)
    await update.message.reply_photo(byte_io)

async def open_program(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    args = context.args
    if not args:
        await update.message.reply_text("Пример: /open notepad")
        return
    program = ' '.join(args)
    if is_program_running(program):
        await update.message.reply_text(f"Программа {program} уже запущена.")
    else:
        try:
            subprocess.Popen(program)
            await update.message.reply_text(f"Открываю: {program}")
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {e}")

async def close_program(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return

    args = context.args
    if not args:
        await update.message.reply_text("Пример: /close notepad.exe")
        return

    program_name = ' '.join(args).lower()
    closed = False

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and program_name in proc.info['name'].lower():
                proc.terminate()
                closed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if closed:
        await update.message.reply_text(f"Процесс {program_name} завершён.")
    else:
        await update.message.reply_text(f"Процесс {program_name} не найден или не удалось завершить.")

async def copy_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    text = ' '.join(context.args)
    if not text:
        await update.message.reply_text("Пример: /copy_text Hello, world!")
        return
    pyperclip.copy(text)
    await update.message.reply_text("Текст скопирован в буфер обмена.")

async def paste_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    text = pyperclip.paste()
    await update.message.reply_text(f"Содержимое буфера:\n{text}")

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return

    path = ' '.join(context.args) or '.'  # Путь по умолчанию — текущая директория
    try:
        files = os.listdir(path)
        if files:
            await update.message.reply_text("\n".join(files))
        else:
            await update.message.reply_text("В этой директории нет файлов.")
    except FileNotFoundError:
        await update.message.reply_text("Директория не найдена.")

async def search_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return

    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Пример: /search my_document.txt")
        return

    found_files = []
    for root, dirs, files in os.walk("C:/"):  # Ищем на диске C
        for file in files:
            if query.lower() in file.lower():
                found_files.append(os.path.join(root, file))

    if found_files:
        await update.message.reply_text("\n".join(found_files))
    else:
        await update.message.reply_text("Файлы не найдены.")

async def send_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    args = context.args
    if not args:
        await update.message.reply_text("Пример: /send_file C:\\путь\\к\\файлу.txt")
        return
    file_path = ' '.join(args)
    if not Path(file_path).exists():
        await update.message.reply_text("Файл не найден.")
        return
    try:
        await update.message.reply_document(document=open(file_path, "rb"))
    except Exception as e:
        await update.message.reply_text(f"Ошибка при отправке файла: {e}")

async def copy_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global copy_buffer
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    args = context.args
    if not args:
        await update.message.reply_text("Пример: /copy_file C:\\путь\\к\\файлу.txt")
        return
    file_path = ' '.join(args)
    if not Path(file_path).exists():
        await update.message.reply_text("Файл не найден.")
        return
    copy_buffer = file_path
    await update.message.reply_text(f"Файл подготовлен для копирования: {file_path}")

async def cut_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cut_buffer
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    args = context.args
    if not args:
        await update.message.reply_text("Пример: /cut_file C:\\путь\\к\\файлу.txt")
        return
    file_path = ' '.join(args)
    if not Path(file_path).exists():
        await update.message.reply_text("Файл не найден.")
        return
    cut_buffer = file_path
    await update.message.reply_text(f"Файл подготовлен к перемещению: {file_path}")

async def paste_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cut_buffer, copy_buffer
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    args = context.args
    if not args:
        await update.message.reply_text("Пример: /paste_file C:\\путь\\к\\папке")
        return
    dest_folder = ' '.join(args)
    try:
        if cut_buffer:
            dest = Path(dest_folder) / Path(cut_buffer).name
            shutil.move(cut_buffer, dest)
            await update.message.reply_text(f"Файл перемещён в: {dest}")
            cut_buffer = None
        elif copy_buffer:
            dest = Path(dest_folder) / Path(copy_buffer).name
            shutil.copy(copy_buffer, dest)
            await update.message.reply_text(f"Файл скопирован в: {dest}")
        else:
            await update.message.reply_text("Нет файла в буфере. Используй /copy_file или /cut_file.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def clipboard_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return

    if cut_buffer:
        await update.message.reply_text(f"📁 Вырезан: {cut_buffer}")
    elif copy_buffer:
        await update.message.reply_text(f"📄 Скопирован: {copy_buffer}")
    else:
        await update.message.reply_text("Буфер пуст.")

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return

    await update.message.reply_text("Перезагружаю систему...")
    subprocess.call(["shutdown", "/r", "/t", "1"])

async def shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return

    await update.message.reply_text("Выключаю систему...")
    subprocess.call(["shutdown", "/s", "/t", "1"])  


if __name__ == '__main__':
    app = ApplicationBuilder().token("6563553728:AAGVhTKvRsQ2R6PBLuzxMRPCt-EGd-K5Ny4").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", system_status))
    app.add_handler(CommandHandler("find_process", find_process))
    app.add_handler(CommandHandler("screenshot", take_screenshot))
    app.add_handler(CommandHandler("open", open_program))
    app.add_handler(CommandHandler("close", close_program))
    app.add_handler(CommandHandler("copy_text", copy_text))
    app.add_handler(CommandHandler("paste_text", paste_text))
    app.add_handler(CommandHandler("list_files", list_files))
    app.add_handler(CommandHandler("search", search_file))
    app.add_handler(CommandHandler("send_file", send_file))
    app.add_handler(CommandHandler("copy_file", copy_file))
    app.add_handler(CommandHandler("cut_file", cut_file))
    app.add_handler(CommandHandler("paste_file", paste_file))
    app.add_handler(CommandHandler("clipboard_status", clipboard_status))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("shutdown", shutdown))

    print("Бот запущен")
    app.run_polling()