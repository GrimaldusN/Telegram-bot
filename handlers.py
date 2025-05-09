import logging
import psutil
import os
import subprocess
import zipfile
import py7zr
import rarfile
import socket
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

SUPPORTED_TEXT_FORMATS = (".txt", ".json", ".ini", ".log", ".md")
AUTHORIZED_USER_ID = 812761972

logger = logging.getLogger(__name__)

cut_buffer = None
copy_buffer = None

def is_program_running(program_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if program_name.lower() in proc.info['name'].lower():
            return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка стартовых кнопок при запуске бота."""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} запустил бота.")
    
    # Создание клавиатуры с кнопками
    keyboard = [
    [InlineKeyboardButton("Help", callback_data='/help')],
    [InlineKeyboardButton("Status", callback_data='/status')],
    [InlineKeyboardButton("Take Screenshot", callback_data='/screenshot')],
    [InlineKeyboardButton("Операции с файлами", callback_data='show_file_operations_menu')],
    [InlineKeyboardButton("Найти процесс", callback_data='/find_process')],
    [InlineKeyboardButton("Открыть программу", callback_data='/open')],
    [InlineKeyboardButton("Закрыть программу", callback_data='/close')],
    [InlineKeyboardButton("Копировать текст", callback_data='/copy_text')],
    [InlineKeyboardButton("Вставить текст", callback_data='/paste_text')],
    [InlineKeyboardButton("Список файлов", callback_data='/list_files')],
    [InlineKeyboardButton("Поиск файла", callback_data='/search')],
    [InlineKeyboardButton("Просмотр файла", callback_data='/view_file')],
    [InlineKeyboardButton("Отправить файл", callback_data='/send_file')],
    [InlineKeyboardButton("Копировать файл", callback_data='/copy_file')],
    [InlineKeyboardButton("Вырезать файл", callback_data='/cut_file')],
    [InlineKeyboardButton("Вставить файл", callback_data='/paste_file')],
    [InlineKeyboardButton("Состояние буфера", callback_data='/clipboard_status')],
    [InlineKeyboardButton("Перезагрузка", callback_data='/restart')],
    [InlineKeyboardButton("Выключение", callback_data='/shutdown')],
    [InlineKeyboardButton("Архивировать", callback_data='/archive')],
    [InlineKeyboardButton("Распаковать", callback_data='/extract')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправка сообщения с кнопками
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я бот для управления вашим компьютером.\nВыберите команду:",
        reply_markup=reply_markup
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Ошибка при обработке обновления {update}: {context.error}")

async def safe_reply(update: Update, text: str):
    if update.callback_query:
        await update.callback_query.message.reply_text(text)
    elif update.message:
        await update.message.reply_text(text)
    else:
        logger.warning("Не удалось отправить сообщение: неизвестный тип update.")

async def system_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized user {update.effective_user.id} tried to use the bot.")
        return
    logger.info(f"User {update.effective_user.id} started the bot.")
    keyboard = [
        [InlineKeyboardButton("Help", callback_data='/help')],
        [InlineKeyboardButton("Status", callback_data='/status')],
        [InlineKeyboardButton("Take Screenshot", callback_data='/screenshot')],
        [InlineKeyboardButton("Операции с файлами", callback_data='show_file_operations_menu')],
        [InlineKeyboardButton("Процессы (по CPU)", callback_data='proc_cpu')],
        [InlineKeyboardButton("Процессы (по памяти)", callback_data='proc_mem')],
        [InlineKeyboardButton("Инфо о сети", callback_data='network_info')],
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
        "/help - Помощь\n"
        "/status - Статус системы\n"
        "/find_process <имя> - Найти процесс\n"
        "/screenshot - Скриншот\n"
        "/open <программа> - Открыть программу\n"
        "/copy_text <текст> - Копировать текст\n"
        "/paste_text - Вставить текст\n"
        "/list_files <путь> - Файлы в директории\n"
        "/search <путь> <шаблон> - Поиск файлов\n"
        "/view_file <путь> - Просмотр файла\n"
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

# Архивация
def archive_file_zip(source_path: str, archive_path: str):
    try:
        with zipfile.ZipFile(archive_path, 'w') as archive:
            archive.write(source_path, arcname=os.path.basename(source_path))
        logger.info(f"ZIP-архив создан: {archive_path}")
    except Exception as e:
        logger.error(f"Ошибка при создании ZIP: {e}")

def archive_file_7z(source_path: str, archive_path: str):
    try:
        with py7zr.SevenZipFile(archive_path, 'w') as archive:
            archive.write(source_path, arcname=os.path.basename(source_path))
        logger.info(f"7z-архив создан: {archive_path}")
    except Exception as e:
        logger.error(f"Ошибка при создании 7z: {e}")

def archive_file_rar(source_path: str, archive_path: str):
    try:
        rarfile.PATH_SEP = '\\'
        os.system(f"rar a -ep1 {archive_path} {source_path}")
        logger.info(f"RAR-архив создан: {archive_path}")
    except Exception as e:
        logger.error(f"Ошибка при создании RAR: {e}")

async def ask_archive_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("ZIP", callback_data="archive_zip"),
            InlineKeyboardButton("7Z", callback_data="archive_7z"),
            InlineKeyboardButton("RAR", callback_data="archive_rar")
        ]
    ]
    await update.message.reply_text("Выберите формат архивации:", reply_markup=InlineKeyboardMarkup(keyboard))

async def archive_format_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["archive_format"] = query.data.split("_")[1]  # zip / 7z / rar
    await query.edit_message_text("Отправьте файл, который нужно заархивировать.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        doc = update.message.document
        if not doc:
            await update.message.reply_text("Пришлите файл.")
            return

        file_path = f"downloads/{doc.file_name}"
        os.makedirs("downloads", exist_ok=True)
        await doc.get_file().download_to_drive(file_path)

        format_ = context.user_data.get("archive_format")
        if not format_:
            await update.message.reply_text("Сначала выберите формат архивации командой /archive.")
            return

        archive_path = file_path + f".{format_}"
        if format_ == "zip":
            archive_file_zip(file_path, archive_path)
        elif format_ == "7z":
            archive_file_7z(file_path, archive_path)
        elif format_ == "rar":
            archive_file_rar(file_path, archive_path)

        with open(archive_path, "rb") as f:
            await update.message.reply_document(f, filename=os.path.basename(archive_path))

    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при обработке документа: {str(e)}")

# Разархивация
def extract_zip(archive_path: str, extract_to: str):
    try:
        with zipfile.ZipFile(archive_path, 'r') as archive:
            archive.extractall(extract_to)
        logger.info(f"ZIP-архив распакован в: {extract_to}")
    except Exception as e:
        logger.error(f"Ошибка при распаковке ZIP: {e}")

def extract_7z(archive_path: str, extract_to: str):
    try:
        with py7zr.SevenZipFile(archive_path, 'r') as archive:
            archive.extractall(path=extract_to)
        logger.info(f"7z-архив распакован в: {extract_to}")
    except Exception as e:
        logger.error(f"Ошибка при распаковке 7z: {e}")

def extract_rar(archive_path: str, extract_to: str):
    try:
        with rarfile.RarFile(archive_path, 'r') as archive:
            archive.extractall(path=extract_to)
        logger.info(f"RAR-архив распакован в: {extract_to}")
    except Exception as e:
        logger.error(f"Ошибка при распаковке RAR: {e}")

async def ask_extract_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправьте ZIP, RAR или 7Z архив для распаковки.")

async def handle_archive_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        doc = update.message.document
        filename = doc.file_name.lower()
        file_path = f"downloads/{doc.file_name}"
        extract_to = "extracted/"

        os.makedirs("downloads", exist_ok=True)
        os.makedirs(extract_to, exist_ok=True)
        await doc.get_file().download_to_drive(file_path)

        if filename.endswith(".zip"):
            extract_zip(file_path, extract_to)
        elif filename.endswith(".7z"):
            extract_7z(file_path, extract_to)
        elif filename.endswith(".rar"):
            extract_rar(file_path, extract_to)
        else:
            await update.message.reply_text("Неподдерживаемый формат архива.")
            return
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при обработке архива: {str(e)}")

    # Отправим список файлов
    files = os.listdir(extract_to)
    if files:
        msg = "Распакованные файлы:\n" + "\n".join(files[:10])
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("Распаковка прошла, но файлы не найдены.")

# Топ процессов
def get_sorted_processes(sort_by="cpu", limit=10):
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            processes.append(proc.info)
        except psutil.NoSuchProcess:
            continue

    key = 'cpu_percent' if sort_by == 'cpu' else 'memory_info'
    sorted_procs = sorted(processes, key=lambda x: x.get(key, 0), reverse=True)

    result = ""
    for proc in sorted_procs[:limit]:
        mem = proc['memory_info'].rss / 1024 / 1024 if proc.get('memory_info') else 0
        result += f"PID: {proc['pid']} | Name: {proc['name']} | CPU: {proc['cpu_percent']}% | RAM: {mem:.2f} MB\n"

    logger.info(f"Сформирован список процессов по {sort_by.upper()}")
    return result or "Нет данных."

# Инфо о сети
def get_network_info():
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)

        output = subprocess.check_output("netsh wlan show interfaces", shell=True, encoding='cp866')
        ssid = signal = "Неизвестно"

        for line in output.splitlines():
            if "SSID" in line and "BSSID" not in line:
                ssid = line.split(":", 1)[1].strip()
            elif "Signal" in line:
                signal = line.split(":", 1)[1].strip()

        logger.info("Сетевые данные успешно получены")
        return f"Имя хоста: {hostname}\nIP-адрес: {ip}\nWi-Fi: {ssid}\nУровень сигнала: {signal}"
    except Exception as e:
        logger.error(f"Ошибка при получении сетевых данных: {e}")
        return f"Ошибка при получении Wi-Fi инфы: {e}"

# Обработка кнопок
async def system_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'proc_cpu':
        result = get_sorted_processes("cpu")
        await query.edit_message_text(f"🔧 Топ процессов по CPU:\n\n{result}")
    elif query.data == 'proc_mem':
        result = get_sorted_processes("mem")
        await query.edit_message_text(f"🧠 Топ процессов по памяти:\n\n{result}")
    elif query.data == 'network_info':
        result = get_network_info()
        await query.edit_message_text(f"🌐 Сетевые данные:\n\n{result}")

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

async def show_file_operations_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, что сообщение существует
    if update.message:
        keyboard = [
            [InlineKeyboardButton("Отправить файл", callback_data='send_file')],
            [InlineKeyboardButton("Скопировать файл", callback_data='copy_file')],
            [InlineKeyboardButton("Вставить файл", callback_data='paste_file')],
            [InlineKeyboardButton("Вырезать файл", callback_data='cut_file')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите операцию с файлом:", reply_markup=reply_markup)
        logger.info("Пользователь запрашивает операцию с файлом.")
    elif update.callback_query:
        # Если это callback_query (например, для кнопки)
        keyboard = [
            [InlineKeyboardButton("Отправить файл", callback_data='send_file')],
            [InlineKeyboardButton("Скопировать файл", callback_data='copy_file')],
            [InlineKeyboardButton("Вставить файл", callback_data='paste_file')],
            [InlineKeyboardButton("Вырезать файл", callback_data='cut_file')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text("Выберите операцию с файлом:", reply_markup=reply_markup)
        logger.info("Пользователь запрашивает операцию с файлом через callback.")

# Логика отправки файла
async def send_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_path = "путь_к_файлу"  # Например, можно запросить путь у пользователя
    try:
        with open(file_path, 'rb') as file:
            await update.message.reply_document(file)
        logger.info(f"Файл {file_path} успешно отправлен.")
    except Exception as e:
        logger.error(f"Ошибка при отправке файла {file_path}: {e}")
        await update.message.reply_text(f"Ошибка при отправке файла: {e}")

# Логика копирования файла
async def copy_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    source_path = "путь_к_оригинальному_файлу"
    destination_path = "путь_к_месту_копирования"
    try:
        shutil.copy(source_path, destination_path)
        logger.info(f"Файл {source_path} успешно скопирован в {destination_path}.")
        await update.message.reply_text("Файл успешно скопирован!")
    except Exception as e:
        logger.error(f"Ошибка при копировании файла {source_path} в {destination_path}: {e}")
        await update.message.reply_text(f"Ошибка при копировании файла: {e}")

# Логика вставки файла (например, из буфера обмена или папки)
async def paste_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    source_path = "путь_к_вставляемому_файлу"
    destination_path = "путь_к_месту_вставки"
    try:
        shutil.copy(source_path, destination_path)
        logger.info(f"Файл {source_path} успешно вставлен в {destination_path}.")
        await update.message.reply_text("Файл успешно вставлен!")
    except Exception as e:
        logger.error(f"Ошибка при вставке файла {source_path} в {destination_path}: {e}")
        await update.message.reply_text(f"Ошибка при вставке файла: {e}")

# Логика вырезания файла
async def cut_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    source_path = "путь_к_файлу"
    destination_path = "путь_к_месту_перемещения"
    try:
        shutil.move(source_path, destination_path)
        logger.info(f"Файл {source_path} успешно перемещен в {destination_path}.")
        await update.message.reply_text("Файл успешно перемещен!")
    except Exception as e:
        logger.error(f"Ошибка при перемещении файла {source_path} в {destination_path}: {e}")
        await update.message.reply_text(f"Ошибка при перемещении файла: {e}")

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

async def view_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id != AUTHORIZED_USER_ID:
            logger.warning(f"Unauthorized user {update.effective_user.id} tried to view file.")
            return

        if not context.args:
            await update.message.reply_text("Укажи путь к файлу после команды, например:\n/viewfile C:\\Users\\file.txt")
            return

        file_path = " ".join(context.args)

        if not os.path.isfile(file_path):
            await update.message.reply_text("Файл не найден.")
            return

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in SUPPORTED_TEXT_FORMATS:
            await update.message.reply_text("Поддерживаются только .txt, .json, .ini и похожие текстовые форматы.")
            return

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read(4096)  # ограничим до 4 KB
            if ext == ".json":
                parsed = json.loads(content)
                content = json.dumps(parsed, indent=2, ensure_ascii=False)
            elif ext == ".ini":
                config = configparser.ConfigParser()
                config.read_string(content)
                content = "\n".join(f"[{section}]\n" + "\n".join(f"{k} = {v}" for k, v in config[section].items()) for section in config.sections())

        await update.message.reply_text(f"Содержимое файла:\n\n{content}")
    
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {file_path}: {e}")
        await update.message.reply_text(f"Ошибка при чтении файла:\n{e}")

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id != AUTHORIZED_USER_ID:
            logger.warning(f"Unauthorized user {update.effective_user.id} tried to list files.")
            return
        if len(context.args) < 1:
            await update.message.reply_text("Пример: /list_files C:/path/to/directory")
            return
        directory = ' '.join(context.args)
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

async def clipboard_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
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
    
    except Exception as e:
        await update.message.reply_text(f"Ошибка при получении содержимого буфера обмена: {e}")
        logger.error(f"Error checking clipboard status: {e}")

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id != AUTHORIZED_USER_ID:
            logger.warning(f"Unauthorized user {update.effective_user.id} tried to restart.")
            return

        if update.callback_query:
            await update.callback_query.message.reply_text("Система будет перезагружена.")
        elif update.message:
            await update.message.reply_text("Система будет перезагружена.")

        logger.info("System restart initiated.")
        os.system("shutdown /r /t 5")
    
    except Exception as e:
        await update.message.reply_text(f"Ошибка при перезагрузке системы: {e}")
        logger.error(f"Error initiating system restart: {e}")

async def shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id != AUTHORIZED_USER_ID:
            logger.warning(f"Unauthorized user {update.effective_user.id} tried to shutdown.")
            return

        if update.callback_query:
            await update.callback_query.message.reply_text("Система будет выключена.")
        elif update.message:
            await update.message.reply_text("Система будет выключена.")

        logger.info("System shutdown initiated.")
        os.system("shutdown /s /t 5")
    
    except Exception as e:
        await update.message.reply_text(f"Ошибка при выключении системы: {e}")
        logger.error(f"Error initiating system shutdown: {e}")

# --- Для других команд добавляем логи и проверки на источник вызова ---

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        command = query.data
        await query.answer()

        # Стандартные команды
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

        # Меню операций с файлами
        elif command == 'show_file_operations_menu':
            await show_file_operations_menu(update, context)
        elif command == 'send_file':
            await send_file(update, context)
        elif command == 'copy_file':
            await copy_file(update, context)
        elif command == 'paste_file':
            await paste_file(update, context)
        elif command == 'cut_file':
            await cut_file(update, context)

        # Архивирование и разархивирование
        elif command.startswith('archive_'):
            logger.info(f"User {update.effective_user.id} selected archive format: {command}")
            await archive_format_callback(update, context)
        elif command == 'extract_file':
            logger.info(f"User {update.effective_user.id} selected to extract file.")
            await ask_extract_file(update, context)

    except Exception as e:
        logger.error(f"Error processing button click: {e}")
        # Проверка на наличие `message`, иначе fallback
        try:
            await update.message.reply_text(f"Ошибка при обработке команды: {e}")
        except:
            await query.edit_message_text(f"Ошибка при обработке команды: {e}")