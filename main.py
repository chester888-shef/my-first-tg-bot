import logging
import os
import socket
import threading

import telebot
from dotenv import load_dotenv
from flask import Flask

from buttons import main_menu, stats_menu, expense_menu
from function import income_f, expense_f, target_f, get_stat_all
from database import add_transactions, add_goals, get_statistics, get_current_goal

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("Змінна оточення TOKEN не задана (.env)")

bot = telebot.TeleBot(TOKEN)

CATEGORY_INCOME = "Дохід"
CATEGORY_EXPENSE_ME = "На себе"
CATEGORY_EXPENSE_VALYA = "На Валю"

PERIOD_LABELS = {
    "stats_week": "тиждень",
    "stats_month": "місяць",
    "stats_year": "рік",
    "stats_all": "за весь час",
}

old_getaddrinfo = socket.getaddrinfo

def _ipv4_only_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [response for response in responses if response[0] == socket.AF_INET]

socket.getaddrinfo = _ipv4_only_getaddrinfo

def _ask_amount_with_retry(chat_id, prompt, next_step_callback, *extra_args):
    sent_msg = bot.send_message(chat_id, prompt)
    bot.register_next_step_handler(sent_msg, next_step_callback, *extra_args)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_name = message.from_user.first_name
    bot.reply_to(
        message,
        f"Привіт, {user_name}! Твій персональний фінансовий помічник запущено.",
        reply_markup=main_menu(),
    )

@bot.message_handler(func=lambda msg: msg.text == "Статистика")
def handle_stat_btn(message):
    bot.send_message(
        message.chat.id,
        "За який період показати звіт?",
        reply_markup=stats_menu(),
    )

@bot.message_handler(func=lambda msg: msg.text == "Витрати")
def handle_expense_btn(message):
    bot.send_message(
        message.chat.id,
        "Оберіть категорію витрат:",
        reply_markup=expense_menu(),
    )

@bot.message_handler(func=lambda msg: msg.text == "Внести дохід")
def ask_income(message):
    _ask_amount_with_retry(message.chat.id, "Введіть суму доходу: ", save_income_function)

def save_income_function(message):
    result = income_f(message.text)
    if result == 0:
        error_msg = bot.send_message(message.chat.id, "Введіть число більше нуля")
        bot.register_next_step_handler(error_msg, save_income_function)
        return

    saved = add_transactions(CATEGORY_INCOME, result, "income", message.chat.id)
    if saved:
        bot.send_message(
            message.chat.id,
            f"До вашого балансу успішно внесено: {result} грн, вітаємо з новими перемогами!",
        )
    else:
        bot.send_message(
            message.chat.id,
            "Сталася помилка при збереженні доходу. Спробуйте, будь ласка, ще раз трохи пізніше.",
        )

@bot.callback_query_handler(func=lambda call: call.data in ["expense_me", "expense_valya"])
def ask_expense(call):
    bot.answer_callback_query(call.id)

    category_map = {
        "expense_me": CATEGORY_EXPENSE_ME,
        "expense_valya": CATEGORY_EXPENSE_VALYA,
    }
    category_message = category_map[call.data]

    _ask_amount_with_retry(
        call.message.chat.id,
        f'Введіть суму для категорії "{category_message}":',
        save_expense_function,
        category_message,
    )

def save_expense_function(message, category_message):
    result = expense_f(message.text, category_message)
    if result == 0:
        error_msg = bot.send_message(message.chat.id, "Введіть число більше нуля")
        bot.register_next_step_handler(error_msg, save_expense_function, category_message)
        return

    saved = add_transactions(category_message, result, "expense", message.chat.id)
    if saved:
        bot.send_message(
            message.chat.id,
            f"У категорію витрат: {category_message}, успішно внесено: {result} грн",
        )
    else:
        bot.send_message(
            message.chat.id,
            "Сталася помилка при збереженні витрати. Спробуйте, будь ласка, ще раз трохи пізніше.",
        )

@bot.message_handler(func=lambda msg: msg.text == "Ціль")
def ask_target(message):
    chat_id = message.chat.id
    rows = get_statistics("stats_all", chat_id)
    result = get_stat_all(rows)
    current_balance = result[3]

    current_goal = get_current_goal(chat_id)
    if current_goal is not None:
        current_goal = float(current_goal)

    if current_goal is None or current_balance >= current_goal:
        if current_goal is not None and current_balance >= current_goal:
            bot.send_message(
                chat_id, f"Вітаю! Ти успішно досягнув своєї цілі у {current_goal} грн!"
            )
        _ask_amount_with_retry(chat_id, "Введіть суму нової цілі: ", save_target_function)
    else:
        remaining = current_goal - current_balance
        bot.send_message(
            chat_id,
            f" У тебе вже є активна ціль: {current_goal} грн.\n"
            f" Поточний баланс: {current_balance} грн.\n"
            f" Залишилося накопичити: {remaining} грн.\n\n"
            f"Нову ціль можна буде встановити тільки після досягнення цієї!",
        )

def save_target_function(message):
    result = target_f(message.text)
    if result == 0:
        error_msg = bot.send_message(message.chat.id, "Помилка, введіть суму більше нуля")
        bot.register_next_step_handler(error_msg, save_target_function)
        return

    saved = add_goals(result, message.chat.id)
    if saved:
        bot.send_message(message.chat.id, f"Ціль у {result} грн успішно прийнята!")
    else:
        bot.send_message(
            message.chat.id,
            "Сталася помилка при збереженні цілі. Спробуйте, будь ласка, ще раз трохи пізніше.",
        )

@bot.callback_query_handler(
    func=lambda call: call.data in ["stats_week", "stats_month", "stats_year", "stats_all"]
)
def handle_stats_selection(call):
    bot.answer_callback_query(call.id)

    period = PERIOD_LABELS[call.data]
    rows = get_statistics(call.data, call.message.chat.id)
    result = get_stat_all(rows)

    bot.send_message(
        call.message.chat.id,
        f"Ваша статистика за {period}:\n\n"
        f" Зароблено (Дохід): {result[0]} грн\n"
        f" Витрати на себе: {result[1]} грн\n"
        f" Витрати на Валю: {result[2]} грн\n\n"
        f" Чистий залишок: {result[3]} грн\n",
    )

@bot.message_handler(func=lambda msg: msg.text == "Баланс")
def ask_balance(message):
    rows = get_statistics("stats_all", message.chat.id)
    result = get_stat_all(rows)
    bot.send_message(
        message.chat.id,
        f"Ваш поточний баланс становить {result[3]} грн. Але справжні вершини ще попереду)",
    )

@bot.message_handler(func=lambda message: True)
def catch_all(message):
    logger.info("Бот почув текст: '%s'", message.text)

@bot.callback_query_handler(func=lambda call: True)
def catch_all_callbacks(call):
    logger.info("Бот почув callback: '%s'", call.data)

app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def run_bot_forever():
    while True:
        try:
            bot.infinity_polling()
        except Exception:
            logger.exception("Бот впав, перезапускаю polling через 5 секунд")
            import time

            time.sleep(5)

if __name__ == "__main__":
    try:
        bot.remove_webhook()
        bot.get_updates(offset=-1)
    except telebot.apihelper.ApiTelegramException as e:
        logger.warning("Проблема при очищенні updates: %s", e)

    threading.Thread(target=run_web, daemon=True).start()

    logger.info("Запуск бота з кнопками. Перевірка зв'язку з Телеграмом")
    run_bot_forever()