import requests
import logging
import json
from backend.config import LINE_CHANNEL_ACCESS_TOKEN


def send_line_message(uid, message_type='text', content='Hello'):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }

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

    payload = {
        "to": uid,
        "messages": [message]
    }

    # === Remove all uri semicolons in payload ===
    def clean_uri_recursively(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "uri" and isinstance(v, str):
                    if ";" in v:
                        logging.warning("🚨 移除非法 URI 分號: %s", v)
                        obj[k] = v.replace(";", "").strip()
                else:
                    clean_uri_recursively(v)
        elif isinstance(obj, list):
            for item in obj:
                clean_uri_recursively(item)

    clean_uri_recursively(payload)

    # === Debug Log ===
    logging.info("📤 準備推播 Payload:\n%s", json.dumps(payload, ensure_ascii=False, indent=2))
    print("📤 LINE Payload:\n", json.dumps(payload, ensure_ascii=False, indent=2))

    # === Send push ===
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
