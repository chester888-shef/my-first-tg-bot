
def _parse_positive_amount(raw_value):
    try:
        amount = float(raw_value)
    except (ValueError, TypeError):
        return 0.0

    if amount > 0:
        return amount
    return 0.0


def income_f(income_message):
    return _parse_positive_amount(income_message)


def expense_f(expense_message, category_message=None):
    return _parse_positive_amount(expense_message)


def target_f(target_message):
    return _parse_positive_amount(target_message)


def get_stat_all(rows):
    expense_all_me = []
    expense_all_valya = []
    income_all = []

    for row in rows:
        trans_type = row["type"] if isinstance(row, dict) else row[2]
        amount = row["amount"] if isinstance(row, dict) else row[3]
        category = row["category"] if isinstance(row, dict) else row[4]

        if trans_type == "expense" and category == "На себе":
            expense_all_me.append(amount)
        elif trans_type == "expense" and category == "На Валю":
            expense_all_valya.append(amount)
        elif trans_type == "income":
            income_all.append(amount)

    total_income = sum(income_all)
    total_expense_me = sum(expense_all_me)
    total_expense_valya = sum(expense_all_valya)
    balance = total_income - total_expense_me - total_expense_valya

    return total_income, total_expense_me, total_expense_valya, balance