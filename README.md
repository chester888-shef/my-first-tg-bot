Core Features

    Quick addition of transactions (expenses/income) by categories.

    Viewing current statistics and balance.

    Restricted access to critical database management commands.

Technologies & Architecture

    Language: Python

    Database: PostgreSQL

    Libraries: telebot

Implementation Details (Under the hood):

    Code structuring based on OOP principles.

    Created a custom Context Manager for safe opening/closing of database connections, preventing memory leaks.

    Written custom Decorators (e.g., @admin_only) to verify user access rights by Telegram ID before executing functions.

How to run locally:

    Clone this repository:
    git clone [https://github.com/your_repository_link.git](https://github.com/your_repository_link.git)

    Install all required dependencies:
    pip install -r requirements.txt

    Create a .env file in the root folder and add your bot token there:
    BOT_TOKEN=your_secret_tg_token

    Run the project:
    python main.py
