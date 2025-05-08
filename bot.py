from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.error import TelegramError
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

# Инициализация логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AUTHORIZED_USER_ID = 812761972
cut_buffer = None
copy_buffer = None
TOKEN = "6563553728:AAGVhTKvRsQ2R6PBLuzxMRPCt-EGd-K5Ny4"

def is_program_running(program_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if program_name.lower() in proc.info['name'].lower():
            return True
    return False

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Ошибка при обработке обновления {update}: {context.error}")

async def safe_reply(update: Update, text: str):
    if update.callback_query:
        await update.callback_query.message.reply_text(text)
    elif update.message:
        await update.message.reply_text(text)
    else:
        logger.warning("Не удалось отправить сообщение: неизвестный тип update.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {update.effective_user.id} tried to use the bot.")
        return
    logger.info(f"User {update.effective_user.id} started the bot.")
    keyboard = [
        [InlineKeyboardButton("Help", callback_data='/help')],
        [InlineKeyboardButton("Status", callback_data='/status')],
        [InlineKeyboardButton("Take Screenshot", callback_data='/screenshot')],
        [InlineKeyboardButton("Paste Text", callback_data='/paste_text')],
        [InlineKeyboardButton("Clipboard Status", callback_data='/clipboard_status')],
        [InlineKeyboardButton("Restart", callback_data='/restart')],
        [InlineKeyboardButton("Shutdown", callback_data='/shutdown')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Бот запущен. Выберите команду:", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {update.effective_user.id} tried to use the help command.")
        return
    logger.info(f"User {update.effective_user.id} requested help.")
    help_text = (
        "Доступные команды:\n"
        "/start - Меню кнопок\n"
        "/help - Помощь\n"
        "/status - Статус системы\n"
        "/find_process <имя> - Найти процесс\n"
        "/screenshot - Скриншот\n"
        "/open <программа> - Открыть программу\n"
        "/copy_text <текст> - Копировать текст\n"
        "/paste_text - Вставить текст\n"
        "/list_files <путь> - Файлы в директории\n"
        "/search <путь> <шаблон> - Поиск файлов\n"
        "/send_file <путь> - Отправить файл\n"
        "/copy_file <файл> - Копировать файл\n"
        "/cut_file <файл> - Вырезать файл\n"
        "/paste_file <папка> - Вставить файл\n"
        "/clipboard_status - Состояние буфера\n"
        "/restart - Перезагрузка\n"
        "/shutdown - Выключение"
    )
    
    # Проверяем источник вызова
    if update.message:
        await update.message.reply_text(help_text)
    elif update.callback_query:
        await update.callback_query.message.reply_text(help_text)

async def system_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"User {user_id} requested system status.")

    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    status_message = (
        f"🖥 Состояние системы:\n\n"
        f"🔧 Загрузка CPU: {cpu_usage}%\n"
        f"🧠 Память: {memory.percent}% ({memory.used // (1024**2)} MB из {memory.total // (1024**2)} MB)\n"
        f"💾 Диск: {disk.percent}% ({disk.used // (1024**3)} GB из {disk.total // (1024**3)} GB)"
    )

    await safe_reply(update, status_message)

async def find_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        return
    name = ' '.join(context.args)
    if not name:
        await update.message.reply_text("Пример: /find_process chrome")
        return
    found = [p.info['name'] for p in psutil.process_iter(['name']) if name.lower() in p.info['name'].lower()]
    await update.message.reply_text('\n'.join(found) if found else "Процессы не найдены.")
    logger.info(f"find_process called with arguments: {context.args}")

async def take_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {update.effective_user.id} tried to take a screenshot.")
        return
    logger.info(f"User {update.effective_user.id} requested a screenshot.")
    screenshot = pyautogui.screenshot()
    byte_io = io.BytesIO()
    screenshot.save(byte_io, format='PNG')
    byte_io.seek(0)
    await update.message.reply_photo(byte_io)

async def open_program(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {update.effective_user.id} tried to open a program.")
        return
    logger.info(f"User {update.effective_user.id} requested to open a program.")
    program = ' '.join(context.args)
    if not program:
        await update.message.reply_text("Пример: /open notepad.exe или /open C:/Path/To/App.exe")
        return
    try:
        subprocess.Popen(program)
        await update.message.reply_text(f"Программа запущена: {program}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка запуска: {e}")
        logger.error(f"Error starting program {program}: {e}")

async def close_program(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {update.effective_user.id} tried to close a program.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Пример: /close chrome")
        return
    process_name = ' '.join(context.args)
    found_process = None

    for proc in psutil.process_iter(['pid', 'name']):
        if process_name.lower() in proc.info['name'].lower():
            found_process = proc
            break
    
    if found_process:
        try:
            found_process.terminate()  # Завершаем процесс
            await update.message.reply_text(f"Процесс {process_name} завершен.")
            logger.info(f"User {update.effective_user.id} closed process {process_name}.")
        except Exception as e:
            await update.message.reply_text(f"Ошибка при завершении процесса: {e}")
            logger.error(f"Error closing process {process_name}: {e}")
    else:
        await update.message.reply_text(f"Процесс {process_name} не найден.")

async def copy_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {update.effective_user.id} tried to copy text.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Пример: /copy_text Hello World")
        return
    text = ' '.join(context.args)
    pyperclip.copy(text)
    await update.message.reply_text(f"Текст скопирован: {text}")
    logger.info(f"User {update.effective_user.id} copied text: {text}")

async def paste_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {update.effective_user.id} tried to paste text.")
        return
    text = pyperclip.paste()
    await update.message.reply_text(f"Текст из буфера обмена: {text}")
    logger.info(f"User {update.effective_user.id} pasted text: {text}")

async def search_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {update.effective_user.id} tried to search for files.")
        return
    path = context.args[0] if context.args else ""
    pattern = context.args[1] if len(context.args) > 1 else ""
    if not path or not pattern:
        await update.message.reply_text("Пример: /search C:/Path/To/Directory *.txt")
        return
    matching_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if fnmatch.fnmatch(file, pattern):
                matching_files.append(os.path.join(root, file))
    if matching_files:
        await update.message.reply_text("\n".join(matching_files))
    else:
        await update.message.reply_text("Файлы не найдены.")

async def send_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {update.effective_user.id} tried to send a file.")
        return
    file_path = ' '.join(context.args)
    if not file_path:
        await update.message.reply_text("Пример: /send_file C:/Path/To/File.txt")
        return
    if os.path.isfile(file_path):
        with open(file_path, 'rb') as f:
            await update.message.reply_document(f)
    else:
        await update.message.reply_text(f"Файл {file_path} не найден.")

async def copy_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {update.effective_user.id} tried to copy file.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Пример: /copy_file C:/path/to/file.txt")
        return
    file_path = ' '.join(context.args)
    try:
        if os.path.exists(file_path):
            global copy_buffer
            copy_buffer = file_path
            await update.message.reply_text(f"Файл скопирован: {file_path}")
            logger.info(f"User {update.effective_user.id} copied file: {file_path}")
        else:
            await update.message.reply_text(f"Файл не найден: {file_path}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при копировании файла: {e}")
        logger.error(f"Error copying file {file_path}: {e}")

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {update.effective_user.id} tried to list files.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Пример: /list_files C:/path/to/directory")
        return
    directory = ' '.join(context.args)
    try:
        if os.path.isdir(directory):
            files = os.listdir(directory)
            file_list = '\n'.join(files) if files else "Папка пуста."
            await update.message.reply_text(f"Содержимое папки {directory}:\n{file_list}")
            logger.info(f"User {update.effective_user.id} listed files in {directory}.")
        else:
            await update.message.reply_text(f"Папка не найдена: {directory}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при получении содержимого папки: {e}")
        logger.error(f"Error listing files in {directory}: {e}")

async def paste_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {update.effective_user.id} tried to paste file.")
        return
    if not copy_buffer:
        await update.message.reply_text("Нет файла в буфере обмена.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Пример: /paste_file C:/path/to/destination/")
        return
    destination = ' '.join(context.args)
    try:
        shutil.copy(copy_buffer, destination)
        await update.message.reply_text(f"Файл вставлен в: {destination}")
        logger.info(f"User {update.effective_user.id} pasted file to: {destination}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при вставке файла: {e}")
        logger.error(f"Error pasting file to {destination}: {e}")

async def cut_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {update.effective_user.id} tried to cut file.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Пример: /cut_file C:/path/to/file.txt")
        return
    file_path = ' '.join(context.args)
    try:
        if os.path.exists(file_path):
            global cut_buffer
            cut_buffer = file_path
            await update.message.reply_text(f"Файл вырезан: {file_path}")
            logger.info(f"User {update.effective_user.id} cut file: {file_path}")
        else:
            await update.message.reply_text(f"Файл не найден: {file_path}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при вырезании файла: {e}")
        logger.error(f"Error cutting file {file_path}: {e}")

async def clipboard_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {update.effective_user.id} tried to check clipboard status.")
        return

    clipboard_content = pyperclip.paste()
    message_text = (
        f"Текущий контент в буфере обмена:\n{clipboard_content}"
        if clipboard_content else
        "Буфер обмена пуст."
    )

    if update.callback_query:
        await update.callback_query.message.reply_text(message_text)
    elif update.message:
        await update.message.reply_text(message_text)

    logger.info(f"User {update.effective_user.id} checked clipboard content: {'non-empty' if clipboard_content else 'empty'}.")

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {update.effective_user.id} tried to restart.")
        return

    if update.callback_query:
        await update.callback_query.message.reply_text("Система будет перезагружена.")
    elif update.message:
        await update.message.reply_text("Система будет перезагружена.")

    logger.info("System restart initiated.")
    os.system("shutdown /r /t 5")


async def shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {update.effective_user.id} tried to shutdown.")
        return

    if update.callback_query:
        await update.callback_query.message.reply_text("Система будет выключена.")
    elif update.message:
        await update.message.reply_text("Система будет выключена.")

    logger.info("System shutdown initiated.")
    os.system("shutdown /s /t 5")

# --- Для других команд добавляем логи и проверки на источник вызова ---

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    command = query.data
    await query.answer()
    
    # Обработка кнопок с логами
    if command == '/help':
        logger.info(f"User {update.effective_user.id} pressed the 'Help' button.")
        await help_command(update, context)
    elif command == '/status':
        logger.info(f"User {update.effective_user.id} pressed the 'Status' button.")
        await system_status(update, context)
    elif command == '/screenshot':
        logger.info(f"User {update.effective_user.id} pressed the 'Screenshot' button.")
        await take_screenshot(update, context)
    elif command == '/paste_text':
        logger.info(f"User {update.effective_user.id} pressed the 'Paste Text' button.")
        await paste_text(update, context)
    elif command == '/clipboard_status':
        logger.info(f"User {update.effective_user.id} pressed the 'Clipboard Status' button.")
        await clipboard_status(update, context)
    elif command == '/restart':
        logger.info(f"User {update.effective_user.id} pressed the 'Restart' button.")
        await restart(update, context)
    elif command == '/shutdown':
        logger.info(f"User {update.effective_user.id} pressed the 'Shutdown' button.")
        await shutdown(update, context)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", system_status))
    app.add_handler(CommandHandler("screenshot", take_screenshot))
    app.add_handler(CommandHandler("find_process", find_process))
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
    app.add_error_handler(error_handler)
    app.add_handler(CallbackQueryHandler(button))

    logger.info("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    if sys.platform.startswith("win") and sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
