
class ShareState:
    order = None
    count_call_api_position = 0

    @classmethod
    def get_oder_info(cls):
        if cls.order is None:
            return "ShareState.Order is None"
        order = cls.order
        return (
            f"*** ShareState.Order is: \n"
            f"      Order ID:               {order.get('order_id')}\n"
            f"      Side:                   {order.get('side')}\n"
            f"      Status:                 {order.get('status')}\n"
            f"      Stoploss Order ID:      {order.get('stoploss_order_id')}\n"
            f"      Takeprofit Order ID:    {order.get('takeprofit_order_id')}\n"
        )

    @classmethod
    def reset_order(cls):
        cls.order = None

    """
    1. check_open_order
        - had position
        - open order
    2. open_orders
    """
    @classmethod
    def set_order(cls, order_id, side, status):
        print(f"\n*** SET NEW ORDER: {order_id} STATUS {status} SIDE {side} SUCCESS\n")
        cls.order = {
            'order_id': order_id,
            'side': side,
            'status': status,
            'stoploss_order_id': None,
            'takeprofit_order_id': None,
            'condition_change_loss': 0.5,
            'price_profit': None
        }


    @classmethod
    def update_order(cls, order_id, status=None, stop_loss=None, take_profit=None,
                     condition_change_loss=None):
        if cls.order and cls.order.get('order_id') == order_id:
            if status is not None:
                cls.order['status'] = status
                print(f"*** UPDATE STORAGE ORDER STATUS = {status} SUCCESS ")
            if stop_loss is not None:
                cls.order['stoploss_order_id'] = stop_loss
                print(f"*** UPDATE STORAGE ORDER STOPLOSS_ORDER_ID = {stop_loss} SUCCESS ")
            if take_profit is not None:
                cls.order['takeprofit_order_id'] = take_profit
                print(f"*** UPDATE STORAGE ORDER TAKEPROFIT_ORDER_ID = {take_profit} SUCCESS ")
            if condition_change_loss is not None:
                cls.order['condition_change_loss'] = condition_change_loss
                print(f"*** UPDATE STORAGE ORDER CONDITION_CHANGE_LOSS = {condition_change_loss} SUCCESS ")
        else:
            print(f"Order with ID {order_id} not found or doesn't exist.")

    @classmethod
    def update_order_stop_loss_id(cls, stop_loss_id):
        if cls.order:
            cls.order['stoploss_order_id'] = stop_loss_id
            print(f"*** UPDATE STORAGE ORDER STOPLOSS_ORDER_ID = {stop_loss_id} SUCCESS ")
        return False

    # *********************** is TRUE *********************** #

    @classmethod
    def is_true_none_order(cls):
        """print(f"check is order None {cls.order}")"""
        if cls.order:
            order_id = cls.order.get('order_id')
            status = cls.order.get('status')
            if order_id:
                return False
            if status:
                return False
        return True

    @classmethod
    def is_true_bug_miss_open_order_stop_loss(cls):
        if cls.order:
            order_id = cls.order.get('order_id')
            status = cls.order.get('status')
            if order_id is None or status is None:
                return False
            if status != 'FILLED':
                return False
            stop_loss_id = cls.order.get('stoploss_order_id')
            if stop_loss_id is None:
                return True

            return False
        return False

    @classmethod
    def is_true_bug_miss_open_order_take_profit(cls):
        if cls.order:
            order_id = cls.order.get('order_id')
            status = cls.order.get('status')
            if order_id is None or status is None:
                return False
            if status != 'FILLED':
                return False
            stop_loss_id = cls.order.get('takeprofit_order_id')
            if stop_loss_id is None:
                return True

            return False
        return False

    @classmethod
    def is_handle_price_stop_loss(cls):
        if cls.order:
            stop_loss_id = cls.order.get('stoploss_order_id')
            if stop_loss_id:
                return True
            return False
        return False



    # *********************** equals  *********************** #

    @classmethod
    def equals_order_id(cls, order_id):
        if cls.order:
            value = cls.order.get('order_id')
            return order_id == value
        return False

    @classmethod
    def equals_order_stop_loss_id(cls, order_id):
        if cls.order:
            value = cls.order.get('stoploss_order_id')
            return order_id == value
        return False

    @classmethod
    def equals_order_take_profit_id(cls, order_id):
        if cls.order:
            value = cls.order.get('takeprofit_order_id')
            return order_id == value
        return False

    # *********************** GET *********************** #

    @classmethod
    def get_order_id(cls):
        if cls.order:
            return cls.order.get('order_id')
        return None

    @classmethod
    def get_order_status(cls):
        if cls.order:
            return cls.order.get('status')
        return None

    @classmethod
    def get_side(cls):
        if cls.order:
            return cls.order.get('side')
        return None

    @classmethod
    def get_order_stop_loss_id(cls):
        if cls.order:
            return cls.order.get('stoploss_order_id')
        return None

    @classmethod
    def get_order_take_profit_id(cls):
        if cls.order:
            return cls.order.get('takeprofit_order_id')
        return None

    @classmethod
    def get_price_profit(cls):
        if cls.order:
            return cls.order.get('price_profit')
        return None

    @classmethod
    def get_condition_change_loss(cls):
        if cls.order:
            return cls.order.get('condition_change_loss')
        return None




