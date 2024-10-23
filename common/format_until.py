

def format_price(amt):
    if amt is None:
        raise ValueError(f"E001. Value amt is None")
    try:
        amt_int =int(amt)
    except (ValueError, TypeError):
        raise ValueError(f"E002. Value amt is format wrong. Amt is {amt}, can't convert to int")
    return f"{amt_int:,} USDT"


def format_rsi(rsi):
    if rsi is None:
        raise ValueError(f"E001. Value amt is None")
    try:
        return int(rsi)
    except (ValueError, TypeError):
        raise ValueError(f"E002. Value amt is format wrong. Amt is {rsi}, can't convert to int")


def format_amt(amt):
    if amt is None:
        raise ValueError(f"E003. Value amt is None")
    try:
        return f"{amt: .2f} USDT"
    except (Exception):
        raise Exception(f"Can't format_amt value amt. Amt is {amt} ")


def format_percent(percent):
    if percent is None:
        raise ValueError(f"E003. Value amt is None")
    try:
        return f"{percent: .2f} %"
    except (Exception):
        raise Exception(f"Can't format_amt value amt. Amt is {percent} ")







