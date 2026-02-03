from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

def get_total_units(useful_life, period, computation):
    if useful_life <= 0:
        return 0

    period = period.upper()
    computation = computation.upper()

    if period == computation:
        return useful_life

    if period == 'YEAR':
        total_days = useful_life * 365
    elif period == 'MONTH':
        total_days = useful_life * 30
    else:  # DAY
        total_days = useful_life

    if computation == 'YEAR':
        return total_days // 365
    elif computation == 'MONTH':
        return total_days // 30
    else:
        return total_days



def get_elapsed_units(capitalization_date, computation):
    if not capitalization_date:
        return 0

    today = date.today()

    if isinstance(capitalization_date, datetime):
        capitalization_date = capitalization_date.date()

    if today <= capitalization_date:
        return 0

    delta = relativedelta(today, capitalization_date)
    computation = computation.upper()

    if computation == 'YEAR':
        return delta.years
    elif computation == 'MONTH':
        return delta.years * 12 + delta.months
    else:  # DAY
        return (today - capitalization_date).days



def straight_line(total_amount, residual_value, total_units, elapsed_units):
    if total_units == 0:
        return Decimal("0.00")

    depreciable = total_amount - residual_value
    accumulated = (depreciable / total_units) * elapsed_units
    return accumulated.quantize(Decimal("0.01"))



def reducing_balance(total_amount, residual_value, useful_life, elapsed_units, computation):
    cost = Decimal(str(total_amount))
    residual = Decimal(str(residual_value))

    if useful_life <= 0 or elapsed_units <= 0:
        return Decimal("0.00")

    
    annual_rate = Decimal("1") - (residual / cost) ** (Decimal("1") / Decimal(str(useful_life)))

    
    period = computation.upper()
    if period == "MONTH":
        rate = annual_rate / Decimal("12")
    elif period == "DAY":
        rate = annual_rate / Decimal("365")
    else:
        rate = annual_rate

    nbv = cost
    for _ in range(int(elapsed_units)):
        depreciation = nbv * rate
        nbv -= depreciation
        if nbv < residual:
            nbv = residual
            break

    accumulated = cost - nbv
    return accumulated.quantize(Decimal("0.01"))


def double_declining(total_amount, residual_value, useful_life, elapsed_units, computation):
    cost = Decimal(str(total_amount))
    residual = Decimal(str(residual_value))

    
    annual_rate = Decimal("2") / Decimal(str(useful_life))

    
    period = computation.upper()
    if period == "MONTH":
        rate = annual_rate / Decimal("12")
    elif period == "DAY":
        rate = annual_rate / Decimal("365")
    else:
        rate = annual_rate

    nbv = cost
    for _ in range(int(elapsed_units)):
        depreciation = nbv * rate
        nbv -= depreciation
        if nbv < residual:
            nbv = residual
            break

    accumulated = cost - nbv
    return accumulated.quantize(Decimal("0.01"))
