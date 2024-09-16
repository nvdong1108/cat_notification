from common.constants import *


def calcu_stop_loss(side, entry):
    if 'SELL' == side:
        return entry * (1+1/LEVERAGE)
    else:
        return entry * (1-1/LEVERAGE)


def calcu_take_profit(cost_per_trade, side, entry):
    if 'SELL' == side:
        return entry - ((cost_per_trade / QUANTITY_PER_TRADE) * TP_RATE)
    else:
        return entry + ((cost_per_trade / QUANTITY_PER_TRADE) * TP_RATE)


def calcu_tk_stop_loss(cost_per_trade,side, entry):
    if 'SELL' == side:
        return (entry + ((cost_per_trade / QUANTITY_PER_TRADE) * SL_RATE))
    else:
        return entry - ((cost_per_trade / QUANTITY_PER_TRADE) * SL_RATE)


