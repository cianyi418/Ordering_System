import requests
import os
from dotenv import load_dotenv
from ..config import LINE_CHANNEL_ACCESS_TOKEN


load_dotenv()  # load environment variables from .env file

# 你的長效 Channel Access Token（請保密）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
if not LINE_CHANNEL_ACCESS_TOKEN:
    raise EnvironmentError("❌ LINE_CHANNEL_ACCESS_TOKEN is missing. Please check .env or deployment environment variables.")


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