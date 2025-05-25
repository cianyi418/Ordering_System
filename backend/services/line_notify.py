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
        message = {
            "type": "flex",
            "altText": content.get("altText", "📦 老宅私廚 訂單通知"),
            "contents": content["contents"]
        }
        # check if the message contains a URI in the footer
        try:
            uri = message["contents"]["footer"]["contents"][0]["action"]["uri"]
            print(f"🚨 檢查 URI：{uri}")
            if ';' in uri:
                uri_clean = uri.replace(';', '')
                logging.warning("🚨 URI 中含有非法分號，已移除：%s", uri_clean)
                message["contents"]["footer"]["contents"][0]["action"]["uri"] = uri_clean
        except Exception as e:
            logging.warning("⚠️ 無法檢查 URI：%s", e)
    else:
        raise ValueError(f"Unsupported message type: {message_type}")

    payload = {
        "to": uid,
        "messages": [message]
    }

    logging.info("📤 準備推播：%s", payload)
    print("=== 最終送出的 payload ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

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