def income_f(income_message):
    try:
        income = float(income_message)
        if income > 0:
            return income
            #заносимо в базу даних
    except ValueError:
        return 0

def expense_f(expense_message, category_message):
        try:
            expense = float(expense_message)
            if expense > 0:
                #if category_message == 'На себе':
                    #то заносимо в категорію відповідну
                #else:
                    #то заносимо в категорію витрати
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

