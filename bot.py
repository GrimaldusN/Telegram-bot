import logging
import sys
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import start, help_command, system_status, take_screenshot, clipboard_status, restart, shutdown, button, show_file_operations_menu, find_process, open_program, close_program, list_files, search_file, ask_archive_format, ask_extract_file, system_menu, system_callback_handler, handle_archive_upload, handle_document, handle_text_input, send_logs

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

AUTHORIZED_USER_ID = 812761972
TOKEN = "6563553728:AAGVhTKvRsQ2R6PBLuzxMRPCt-EGd-K5Ny4"

def check_unrar():
    unrar_path = 'unrar.exe'

    # Проверяем наличие unrar.exe в PATH или в текущей директории
    if not any(os.access(os.path.join(path, unrar_path), os.X_OK) for path in os.getenv("PATH").split(os.pathsep)):
        if not os.path.isfile(unrar_path):
            print("ERROR: unrar.exe not found. Please download and place it in the bot directory or ensure it's in your PATH.")
            sys.exit("unrar.exe not found!")

check_unrar()

def main():
    app = Application.builder().token(TOKEN).build()

    # Стандартные команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", system_status))
    app.add_handler(CommandHandler("get_logs", send_logs))
    app.add_handler(CommandHandler("system_menu", system_menu))
    app.add_handler(CommandHandler("screenshot", take_screenshot))
    app.add_handler(CommandHandler("show_file_operations_menu", show_file_operations_menu))
    app.add_handler(CommandHandler("find_process", find_process))
    app.add_handler(CommandHandler("open", open_program))
    app.add_handler(CommandHandler("close", close_program))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_input))
    app.add_handler(CommandHandler("list_files", list_files))
    app.add_handler(CommandHandler("search", search_file))
    app.add_handler(CommandHandler("clipboard_status", clipboard_status))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("shutdown", shutdown))
    app.add_handler(CommandHandler("archive", ask_archive_format))
    app.add_handler(CommandHandler("extract", ask_extract_file))

    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CallbackQueryHandler(system_callback_handler))  # Обработка прочих кнопок

    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))  # Обработка файла для архивации
    app.add_handler(MessageHandler(filters.Document.ALL, handle_archive_upload))  # Для распаковки — при необходимости фильтровать


    logger.info("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    if sys.platform.startswith("win") and sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()