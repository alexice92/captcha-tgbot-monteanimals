# Telegram Bot with CAPTCHA and Stoplist Functionality

This repository contains a Telegram bot implemented using the [Aiogram](https://docs.aiogram.dev/) framework. The bot is designed to manage chat members with CAPTCHA verification and includes functionality for maintaining a stoplist.

## Features

- **CAPTCHA Verification**: New members are required to solve a CAPTCHA by selecting the correct emoji.
- **Stoplist Management**: Users can be restricted and managed via a stoplist.
- **Message Lifetime**: Automatic deletion of bot messages after a configurable time.
- **Easy Configuration**: Configuration through a `configs.py` file for API tokens and timeouts.

## Project Structure

- **`main.py`**: Entry point of the bot, containing the main logic.
- **`bot_responses.py`**: Contains predefined bot messages for different scenarios.
- **`captcha_questions.py`**: Logic for generating CAPTCHA questions and options.
- **`configs.py`**: Configuration file for API tokens and timeout settings.
- **`file_manager.py`**: Manages file operations like loading and saving stoplists.
- **`stoplist_manager.py`**: Functions for handling the stoplist (add, remove, check users).
- **`requirements.txt`**: Dependencies required to run the bot.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/your-repository.git
   cd your-repository

2. **Install dependencies**:

pip install -r requirements.txt

3. **Set up configuration**:

    Edit the configs.py file to include your bot's API token:

    API_TOKEN = 'your-telegram-bot-token'

4. **Run the bot**:

    python main.py

##  Usage

    Add the bot to a group to enable CAPTCHA verification for new members.
    The bot restricts users who fail the CAPTCHA or are listed in the stoplist.

##  Files

    Procfile: Used for deployment on Heroku.
    requirements.txt: Contains all the required dependencies.
    Stoplist Files:
        ModeratedUsers.txt or stoplist.csv is used to manage and store restricted users.

##  Configuration

    CAPTCHA Settings:
        Customize the CAPTCHA timeout and messages in configs.py and bot_responses.py.
    Stoplist:
        Manage the stoplist via the provided file management functions in stoplist_manager.py.

##  Deployment

    The project includes a Procfile for deployment on Heroku. To deploy:

    Commit all changes and push them to a GitHub repository.
    Create a Heroku app:

      heroku create

##  Deploy the app:

      git push heroku main

##  Contributing

    Contributions are welcome! Please fork the repository and create a pull request with your changes.

##  License

    This project is licensed under the MIT License. See the LICENSE file for more details.
