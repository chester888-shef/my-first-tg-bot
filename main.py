from unittest import result

import telebot
import socket
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

from buttons import main_menu , stats_menu , expense_menu
from function import income_f , expense_f , target_f , get_stat_all
from database import get_connection,  add_transactions, add_goals, get_statistics, get_current_goal

old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [response for response in responses if response[0] == socket.AF_INET]
socket.getaddrinfo = new_getaddrinfo


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    bot.reply_to(
        message,
        f"Привіт, {user_name}! Твій персональний фінансовий помічник запущено.",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda msg: msg.text == "Статистика")
def handle_stat_btn(message):
    bot.send_message(
        message.chat.id,
        "За який період показати звіт?",
        reply_markup=stats_menu()
    )
@bot.message_handler(func= lambda msg: msg.text == "Витрати")
def handle_expense_btn(message):
    bot.send_message(
        message.chat.id,
        "Оберіть категорію витрат:",
        reply_markup=expense_menu()
    )

@bot.message_handler(func = lambda msg: msg.text == "Внести дохід")
def ask_income(message):
    income_sent_msg = bot.send_message(message.chat.id,'Введіть суму доходу: ')
    bot.register_next_step_handler(income_sent_msg, save_income_function)

def save_income_function(message):
    result = income_f(message.text)
    if result == 0:
        error_msg = bot.send_message(message.chat.id ,'Введіть число більше нуля ')
        bot.register_next_step_handler(error_msg , save_income_function)
    else:
        add_transactions('MyTee', message.text, 'income')
        bot.send_message(message.chat.id,f'Успішно внесено: {result} грн')

@bot.callback_query_handler(func=lambda call: call.data in ['expense_me', 'expense_valya'])
def ask_expense(call):
    bot.answer_callback_query(call.id)
    if call.data == 'expense_me':
        category_message = 'На себе'
    elif call.data == 'expense_valya':
        category_message = 'На Валю'

    sent_msg = bot.send_message(call.message.chat.id, f'Введіть суму для категорії "{category_message}":')
    bot.register_next_step_handler(sent_msg , save_expense_function, category_message)

def save_expense_function(message, category_message):
    result = expense_f(message.text , category_message)
    if result == 0:
        error_msg = bot.send_message(message.chat.id ,'Введіть число більше нуля ')
        bot.register_next_step_handler(error_msg , save_expense_function, category_message)
    else:
        add_transactions(category_message, result , 'expense')
        bot.send_message(message.chat.id,f'У категорію витрат: {category_message}, успішно внесено: {result} грн')


@bot.message_handler(func=lambda msg: msg.text == 'Ціль')
def ask_target(message):
    # 1. Дістаємо поточний баланс (використовуємо твій готовий механізм)
    rows = get_statistics('stats_all')
    result = get_stat_all(rows)
    current_balance = result[3]

    current_goal = get_current_goal()
    if current_goal is not None:
        current_goal = float(current_goal)
    if current_goal is None or current_balance >= current_goal:

        if current_goal is not None and current_balance >= current_goal:
            bot.send_message(message.chat.id, f"Вітаю! Ти успішно досягнув своєї цілі у {current_goal} грн!")

        income_sent_msg = bot.send_message(message.chat.id, 'Введіть суму нової цілі: ')
        bot.register_next_step_handler(income_sent_msg, save_target_function)

    else:
        remaining = current_goal - current_balance
        bot.send_message(
            message.chat.id,
            f" У тебе вже є активна ціль: {current_goal} грн.\n"
            f" Поточний баланс: {current_balance} грн.\n"
            f" Залишилося накопичити: {remaining} грн.\n\n"
            f"Нову ціль можна буде встановити тільки після досягнення цієї!"
        )

def save_target_function(message):
    result = target_f(message.text)
    if result == 0:
       result =  bot.send_message(message.chat.id, 'Помилка, введіть суму більше нуля')
       bot.register_next_step_handler(result , save_target_function)
    else:
        bot.send_message(message.chat.id, f'Ціль у {result} грн успішно прийнята! ')
        add_goals(result)


@bot.callback_query_handler(func=lambda call: call.data in [ 'stats_week', 'stats_month', 'stats_year', 'stats_all'])
def handle_stats_selection(call):
    bot.answer_callback_query(call.id)

    if call.data == 'stats_week':
        period = "тиждень"
    elif call.data == 'stats_month':
        period = "місяць"
    elif call.data == 'stats_year':
        period = "рік"
    elif call.data == 'stats_all':
        period = "за весь час"

    rows = get_statistics(call.data)
    result = get_stat_all(rows)

    bot.send_message(
        call.message.chat.id,
        f"Ваша статистика за {period}:\n\n"
        f" Зароблено (Дохід): {result[0]} грн\n"
        f" Витрати на себе: {result[1]} грн\n"
        f" Витрати на Валю: {result[2]} грн\n\n"
        f" Чистий залишок: {result[3]} грн\n"
    )

@bot.message_handler(func = lambda msg: msg.text =='Баланс')
def ask_balance(message):
    rows = get_statistics('stats_all')
    result = get_stat_all(rows)
    bot.send_message(message.chat.id, f'Ваш поточний баланс становить {result[3]} грн. Але справжні вершини ще попереду)' )



bot.remove_webhook()
bot.get_updates(offset=-1)
print("Запуск бота з кнопками... Перевірка зв'язку з Телеграмом...")
bot.infinity_polling()