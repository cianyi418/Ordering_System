import requests
import logging
import json
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

    logging.info("📤 準備推播：%s", payload)
    logging.info((json.dumps(payload, ensure_ascii=False, indent=2)))

    try:
        response = requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers=headers,
            json=payload
        )
        print(f"📤 LINE 推播結果：{response.status_code}")
        print(response.text)


        if response.status_code != 200:
            logging.error("❌ 推播失敗：%s %s", response.status_code, response.text)
        else:
            logging.info("✅ 推播成功：%s", uid)

        return response.status_code, response.text

    except Exception as e:
        logging.exception("❗ 推播時發生例外錯誤")
        return 500, str(e)
