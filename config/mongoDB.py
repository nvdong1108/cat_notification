
from pymongo import MongoClient, errors
from pymongo.errors import CollectionInvalid
from urllib.parse import quote_plus
from datetime import datetime
from bson.objectid import ObjectId
import uuid
username = "nvdong"
password = "Vandong123"
encoded_password = quote_plus(password)
cluster = "cluster0.tkiscbi.mongodb.net"
params = "?retryWrites=true&w=majority&appName=Cluster0"
# mongodb+srv://nvdong:V@nd0ng1108@cluster0.tkiscbi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
connection_string = f"mongodb+srv://{username}:{encoded_password}@{cluster}/{params}"
client = MongoClient(connection_string)
db = client.test
collection_name = 'tb_order'


def update_order(params, update_fields):
    try:
        collection = db[collection_name]
        filter = {key: value for key, value in params.items() if value is not None}
        update_data = {key: value for key, value in update_fields.items()}
        result = collection.update_many(filter, {"$set": update_data})
        if result.modified_count > 0:
            print(f"update order success")
            return True
        else:
            print(f"Not found order data to update")
            return False
    except Exception as e:
        print(f"Lỗi khi cập nhật đơn hàng: {e}")
        return False


def select_orders_by_status(status):
    try:
        collection = db[collection_name]
        query = {"status": status}
        result = collection.find(query)
        return list(result)

    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu từ collection '{collection_name}': {e}")
        return None


def select_orders(params= None):
    try:
        collection = db[collection_name]

        if params is None or not params:
            query = {}
        else:
            query = {key: value for key, value in params.imtems()}
        result = collection.find(query)
        return list(result)

    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu từ collection '{collection_name}': {e}")
        return None


def insert_order(order_data):
    try:
        collection = db.tb_order
        seq = uuid.uuid4()
        order_data['seq'] = str(seq)
        current_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        order_data['creat-time'] = current_time
        result = collection.insert_one(order_data)
        print(f"Đã thêm đơn hàng mới có orderId: {order_data['orderId']} vào collection 'tb_order'.")
        return result.inserted_id

    except Exception as e:
        print(f"Lỗi khi thêm đơn hàng: {e}")


def drop_collection(collection_name):
    try:
        db.drop_collection(collection_name)
        print(f"Đã xóa collection '{collection_name}' thành công.")
    except CollectionInvalid:
        print(f"Collection '{collection_name}' không tồn tại.")


def create_collection(collection_name):
    existing_collections = db.list_collection_names()
    if collection_name in existing_collections:
        print(f"Collection '{collection_name}' đã tồn tại.")
    else:
        try:
            db.create_collection(collection_name, validator={
                '$jsonSchema': {
                    'bsonType': 'object',
                    'required': ['symbol', 'side', 'price', 'status'],
                    'properties': {
                        'seq': {'bsonType': 'string'},
                        'orderId': {'bsonType': 'string'},
                        'symbol': {'bsonType': 'string'},
                        'side': {'bsonType': 'string'},
                        'price': {'bsonType': 'double'},
                        'stop-loss': {'bsonType': ['double', 'null']},
                        'take-profit': {'bsonType': ['double', 'null']},
                        'leverage': {'bsonType': ['int', 'null']},
                        'status': {'bsonType': 'string'},
                        'result': {'bsonType': ['string', 'null']},
                        'indicator': {'bsonType': ['string', 'null']},
                        'cost': {'bsonType': ['double', 'null']},
                        'creat-time': {'bsonType': ['string','null']},
                        'desc': {'bsonType': ['string', 'null']}
                    }
                }
            })
            print(f"Tạo collection '{collection_name}' thành công.")
        except errors.CollectionInvalid:
            print(f"Lỗi khi tạo collection '{collection_name}'.")


if __name__ == "__main__":
    order_data = {
        'orderId': 'ORD001',
        'symbol': 'BTCUSDT',
        'side': 'buy',
        'price': 35000.0,
        'stop-loss': 1.0,
        'take-profit': 1.0,
        'leverage': 10,
        'status': 'open',
        'result': None,
        'indicator': 'RSI',
        'cost': 10.0,
        'desc': 'New order for BTCUSD'
    }
    print(db.list_collection_names())
    # drop_collection(collection_name)
    # create_collection(collection_name)
    # insert_order(order_data)
    params = {
        'status': "open"
    }
      # Điền _id của đơn hàng cần cập nhật
    update_fields = {
        "status": "closed",
        "desc": "close all order"
    }
    # update_order(params, update_fields)
    result = select_orders()
    print("\n\n")
    print(result)