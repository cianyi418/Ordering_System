import requests
import logging
import json
import copy
from backend.config import LINE_CHANNEL_ACCESS_TOKEN

# === Send LINE Flex or Text message ===
def send_line_message(uid, message_type='text', content='Hello'):

    if message_type == 'text':
        message = {
            "type": "text",
            "text": content
        }

    elif message_type == 'flex':
        alt_text = content.get("altText", "📦 老宅私廚 訂單通知")
        flex_content = content.get("contents")

        message = {
            "type": "flex",
            "altText": alt_text,
            "contents": flex_content
        }

    else:
        raise ValueError(f"Unsupported message type: {message_type}")

    # === Send push ===
    try:
        response = requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers = {
                "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
            },
            json = {
                "to": uid,
                "messages": [message]
            }
        )

        print(f"📤 LINE 推播結果：{response.status_code}")
        print("DEBUG: LINE API 回應 headers =", response.headers)
        print("DEBUG: LINE API 回應 body =", response.text)

        try:
            response_json = response.json()
            print("DEBUG: LINE API 回應 JSON =", json.dumps(response_json, ensure_ascii=False))
        except ValueError:
            print("DEBUG: LINE API 回應非 JSON 格式")

        if response.status_code != 200:
            logging.error("❌ 推播失敗：%s %s", response.status_code, response.text)
        else:
            logging.info("✅ 推播成功：%s", uid)

        return response.status_code, response.text

    except Exception as e:
        logging.exception("❗ 推播時發生例外錯誤")
        print("DEBUG: 推播例外錯誤 =", str(e))
        return 500, str(e)
