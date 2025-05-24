import requests
import os


# Replace your Channel Access Token（long-lived）
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

def send_line_message(user_id, message):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
    }
    payload = {
        'to': user_id,
        'messages': [
            {
                'type': 'text',
                'text': message
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    print('Status:', response.status_code)
    print('Response:', response.text)

if __name__ == '__main__':
    LINE_TEST_UID = os.environ.get('LINE_TEST_UID')  # 替換成你的測試用戶 ID
    send_line_message(LINE_TEST_UID, '這是一封測試訊息 📬')