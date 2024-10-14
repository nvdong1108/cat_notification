
class ShareState:
    order = None

    @classmethod
    def reset_order(cls):
        cls.order = None

    @classmethod
    def set_order(cls, order_id, side, status):
        cls.order = {
            'order_id': order_id,
            'status': status,
            'side': side,
            'stoploss_order_id': None,
            'takeprofit_order_id': None
        }

    @classmethod
    def update_order(cls, order_id, status='NEW', stop_loss=None, take_profit=None):
        if cls.order and cls.order.get('order_id') == order_id:
            if status is not None:
                cls.order['status'] = status
            if stop_loss is not None:
                cls.order['stoploss_order_id'] = stop_loss
            if take_profit is not None:
                cls.order['takeprofit_order_id'] = take_profit
        else:
            print(f"Order with ID {order_id} not found or doesn't exist.")

    @classmethod
    def get_order_status(cls):
        if cls.order:
            return cls.order.get('status')
        return None

    @classmethod
    def is_none_order(cls):
        print(f"check is order None {cls.order}")
        if cls.order:
            order_id = cls.order.get('order_id')
            status = cls.order.get('status')
            if order_id:
                return False
            if status:
                return False
        return True

    @classmethod
    def get_order_id(cls, order_id):
        if cls.order:
            value = cls.order.get('order_id')
            return order_id == value
        return False

    @classmethod
    def get_order_stop_loss_id(cls, order_id):
        if cls.order:
            value = cls.order.get('stoploss_order_id')
            return order_id == value
        return False

    @classmethod
    def get_order_take_profit_id(cls, order_id):
        if cls.order:
            value = cls.order.get('takeprofit_order_id')
            return order_id == value
        return False



