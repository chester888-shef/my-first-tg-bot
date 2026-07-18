from telebot import types

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn_stat = types.KeyboardButton("Статистика")
    btn_income = types.KeyboardButton("Внести дохід")
    btn_expense = types.KeyboardButton("Витрати")
    btn_target = types.KeyboardButton("Ціль")
    btn_balance = types.KeyboardButton("Баланс")

    markup.add(btn_stat, btn_balance)
    markup.add(btn_income, btn_expense)
    markup.add(btn_target)

    return markup

def stats_menu():
    markup = types.InlineKeyboardMarkup()

    btn_week = types.InlineKeyboardButton(text="За тиждень", callback_data="stats_week")
    btn_month = types.InlineKeyboardButton(text="За місяць", callback_data="stats_month")
    btn_year = types.InlineKeyboardButton(text="🗓 За рік", callback_data="stats_year")
    btn_all = types.InlineKeyboardButton(text="♾ За весь час", callback_data="stats_all")

    markup.add(btn_week, btn_month)
    markup.add(btn_year, btn_all)

    return markup

def expense_menu():
    markup = types.InlineKeyboardMarkup()

    btn_me = types.InlineKeyboardButton(text="На себе", callback_data="expense_me")
    btn_valya = types.InlineKeyboardButton(text="На Валю", callback_data="expense_valya")

    markup.add(btn_me, btn_valya)

    return markup