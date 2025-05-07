from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import subprocess
import logging
import psutil
import pyperclip
import shutil
import pyautogui
import io
import os
import sys
import asyncio
from pathlib import Path

AUTHORIZED_USER_ID = 812761972
cut_buffer = None
copy_buffer = None
TOKEN = "6563553728:AAGVhTKvRsQ2R6PBLuzxMRPCt-EGd-K5Ny4"

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
    keyboard = [
        [InlineKeyboardButton("Help", callback_data='/help')],
        [InlineKeyboardButton("Status", callback_data='/status')],
        [InlineKeyboardButton("Take Screenshot", callback_data='/screenshot')],
        [InlineKeyboardButton("Open Program", callback_data='/open')],
        [InlineKeyboardButton("Search Files", callback_data='/search')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Бот запущен. Выберите команду:", reply_markup=reply_markup)

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

# Теперь добавим InlineKeyboardButton для каждой команды
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    command = query.data

    if command == '/help':
        await help_command(update, context)
    elif command == '/status':
        await system_status(update, context)
    elif command == '/screenshot':
        await take_screenshot(update, context)
    elif command == '/open':
        await open_program(update, context)
    elif command == '/search':
        await search_file(update, context)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", system_status))
    app.add_handler(CommandHandler("screenshot", take_screenshot))
    app.add_handler(CommandHandler("open", open_program))
    app.add_handler(CommandHandler("search", search_file))
    app.add_handler(CallbackQueryHandler(button))

    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    if sys.platform.startswith("win") and sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    main()