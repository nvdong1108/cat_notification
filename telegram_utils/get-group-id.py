import requests

def get_updates(api_token):
    url = f"https://api.telegram.org/bot{api_token}/getUpdates"
    response = requests.get(url)
    return response.json()

def find_group_id(updates):
    group_ids = []
    for update in updates["result"]:
        if "message" in update:
            chat = update["message"]["chat"]
            if chat["type"] in ["group", "supergroup","channel"]:
                group_ids.append(chat["id"])
    return group_ids if group_ids else None

if __name__ == "__main__":
    # Thay thế bằng API Token của bot bạn
    api_token = "6837177530:AAFUTQeVB7zf7pR6z_8iJFZYxxY7WYdLSN4"

    # Lấy cập nhật
    updates = get_updates(api_token)

    # Tìm ID của nhóm
    group_id = find_group_id(updates)

    if group_id:
        print(f"Group ID: {group_id}")
    else:
        print("Không tìm thấy nhóm nào.")
