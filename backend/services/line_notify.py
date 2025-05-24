import requests
from backend.config import LINE_CHANNEL_ACCESS_TOKEN

def send_line_message(uid, message_type='text', content='Hello'):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }

    message = {
        "type": message_type,
        "altText": "訂單通知" if message_type == 'flex' else content
    }

    if message_type == 'text':
        message['text'] = content
    elif message_type == 'flex':
        message['contents'] = content
    else:
        raise ValueError(f"Unsupported message type: {message_type}")

    payload = {
        "to": uid,
        "messages": [message]
    }

    response = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers=headers,
        json=payload
    )

    return response.status_code, response.text