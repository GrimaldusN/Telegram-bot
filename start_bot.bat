@echo off

REM Устанавливаем рабочую директорию на папку с ботом
cd /d "C:\Telegram bot"

REM Проверка существования виртуального окружения
IF NOT EXIST "C:\Users\Multimedia3\venvfas\Scripts\activate.bat" (
    echo Виртуальное окружение не найдено!
    pause
    exit /b
)

REM Активируем виртуальное окружение
call "C:\Users\Multimedia3\venvfas\Scripts\activate.bat"

REM Проверка доступности Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python не найден!
    pause
    exit /b
)

REM Запускаем бота
python bot.py

REM Ожидаем нажатия клавиши перед закрытием окна
pause
