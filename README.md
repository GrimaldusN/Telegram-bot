# Telegram File Management Bot

Telegram bot for managing files and applications on your PC. It allows you to perform various operations such as starting programs, viewing directories, reading and deleting files, and much more. The bot is built with Python and uses the `python-telegram-bot` library.

## Features

- **File Management**:
  - View and delete files
  - View directories
  - Send files through the bot
  - Cut, copy, and paste files
  
- **Application Management**:
  - Launch applications installed on your PC
  
- **Clipboard Operations**:
  - Manage clipboard content
  
## Technologies Used

- **Python** - The primary programming language.
- **python-telegram-bot** - Library for interacting with Telegram API.
- **os** - For interacting with the operating system.
- **shutil** - For file operations like copying and moving files.
  
## Installation

To run this bot, follow these steps:

1. Clone this repository to your local machine:
    ```bash
    git clone https://github.com/GrimaldusN/Telegram-bot.git

2. Navigate into the project directory:
    cd Telegram-bot

3. Install the required dependencies:
    pip install -r requirements.txt

4. Create a Telegram bot by talking to BotFather on Telegram and obtain your bot's API token.

5. Set up your bot by adding your bot's token to a .env file:
    TELEGRAM_TOKEN=your_bot_token_here

6. Run the bot:
    python bot.py

## Usage

Once the bot is running, you can start interacting with it directly in Telegram. Use the available commands to perform file and application management tasks. The bot supports both private messages and group chats.

### Commands

- **/start** - Starts the bot and shows a welcome message.
- **/help** - Displays a list of available commands and instructions.
- **/files** - Shows a list of files in the current directory.
- **/delete [filename]** - Deletes a specified file.
- **/view [filename]** - Previews the contents of a file (works for images and text files).
- **/send [filename]** - Sends a file through the bot.
- **/cut [filename]** - Cuts (moves) a specified file.
- **/copy [filename]** - Copies a specified file.
- **/paste [destination]** - Pastes the file to a given destination directory.
- **/rename [old_name] [new_name]** - Renames a specified file.
- **/launch [application_name]** - Launches a specified application installed on your PC.
- **/clipboard** - Displays the current content of your clipboard.
- **/set_clipboard [content]** - Sets the clipboard content to the specified text.

## Contributing

If you'd like to contribute to this project, feel free to fork the repository and submit pull requests. Please make sure to follow the coding style and write clear commit messages.