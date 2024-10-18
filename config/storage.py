
class ShareState:
    order = None
    count_call_api_position = 0

    @classmethod
    def reset_order(cls):
        cls.order = None

    @classmethod
    def set_order(cls, order_id, side, status):
        print(f"\n*** SET NEW ORDER: {order_id} STATUS {status} SIDE {side} SUCCESS\n")
        cls.order = {
            'order_id': order_id,
            'side': side,
            'status': status,
            'stoploss_order_id': None,
            'takeprofit_order_id': None
        }

    @classmethod
    def update_order(cls, order_id, status=None, stop_loss=None, take_profit=None):
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
        else:
            print(f"Order with ID {order_id} not found or doesn't exist.")



    @classmethod
    def is_none_order(cls):
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
    def is_bug_miss_open_order_stop_loss(cls):
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
    def is_bug_miss_open_order_take_profit(cls):
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
    def get_order_id(cls, order_id):
        if cls.order:
            value = cls.order.get('order_id')
            return order_id == value
        return False

    @classmethod
    def check_order_stop_loss_id(cls, order_id):
        if cls.order:
            value = cls.order.get('stoploss_order_id')
            return order_id == value
        return False

    @classmethod
    def check_order_take_profit_id(cls, order_id):
        if cls.order:
            value = cls.order.get('takeprofit_order_id')
            return order_id == value
        return False

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





