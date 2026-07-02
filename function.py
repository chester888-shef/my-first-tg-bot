def income_f(income_message):
    try:
        income = float(income_message)
        if income > 0:
            return income
    except ValueError:
        return 0

def expense_f(expense_message, category_message):
        try:
            expense = float(expense_message)
            if expense > 0:
                return expense
        except ValueError:
            return 0

def target_f(target_message):
    try:
        expense = float(target_message)
        if expense > 0:
           #додаємо в таблицю SQL
            return expense
    except ValueError:
        return 0

def get_stat_all(rows):
    expense_all_me = []
    expense_all_valya = []
    income_all = []
    for row in rows:
        if row[4] == 'На себе':
            expense_all_me.append(row[3])
        elif row[4] == 'На Валю':
            expense_all_valya.append(row[3])
        elif row[2] == 'income': 
            income_all.append(row[3])
    stat_all = sum(income_all) - sum(expense_all_valya) - sum(expense_all_me)
    return sum(income_all), sum(expense_all_me) , sum(expense_all_valya) , stat_all
