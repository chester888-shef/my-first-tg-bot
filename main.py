import telebot
import socket

from buttons import main_menu , stats_menu , expense_menu
from function import income_f , expense_f , target_f

old_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [response for response in responses if response[0] == socket.AF_INET]
socket.getaddrinfo = new_getaddrinfo

TOKEN = 'your token'
bot = telebot.TeleBot(TOKEN)

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
        bot.send_message(message.chat.id ,'Введіть число більше нуля ')
    else:
        bot.send_message(message.chat.id,f'Успішно внесено: {result} грн')

@bot.callback_query_handler(func=lambda call: call.data in ['expense_me', 'expense_valya'])
def ask_expense(call):
    bot.answer_callback_query(call.id)
    if call.data == 'expense_me':
        category_message = 'На себе'
    else:
        category_message = 'На Валю'

    sent_msg = bot.send_message(call.message.chat.id, f'Введіть суму для категорії "{category_message}":')
    bot.register_next_step_handler(sent_msg , save_expense_function, category_message)

def save_expense_function(message, category_message):
    result = expense_f(message.text , category_message)
    if result == 0:
        bot.send_message(message.chat.id ,'Введіть число більше нуля ')
    else:
        bot.send_message(message.chat.id,f'У категорію: {category_message}, успішно внесено: {result} грн')


@bot.message_handler(func=lambda msg : msg.text == 'Ціль' )
def ask_target(message):
    income_sent_msg = bot.send_message(message.chat.id, 'Введіть суму цілі: ')
    bot.register_next_step_handler(income_sent_msg, save_target_function)

def save_target_function(message):
    result = target_f(message.text)
    if result == 0:
        bot.send_message(message.chat.id, 'Помилка, введіть суму більше нуля')
    else:
        # Тут буде логіка успіху
        bot.send_message(message.chat.id, f'Ціль у {result} грн успішно прийнята! ')


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

    bot.send_message(
        call.message.chat.id,
        f"Запит прийнято! Тут буде виведена твоя статистика за {period}. 📊\n"
        f"Зовсім скоро ми підключимо базу даних, і цей блок оживе!"
    )

@bot.callback_query_handler(func=lambda call: call.data in ['target_remaintogoal']
def hadler_target_function(call):
    bot.answer_callback_query(call.id)




bot.remove_webhook()
bot.get_updates(offset=-1)
print("Запуск бота з кнопками... Перевірка зв'язку з Телеграмом...")
bot.infinity_polling()