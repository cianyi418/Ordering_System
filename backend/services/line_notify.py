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
    # check footer all button's uri
        try:
            footer_contents = message["contents"]["footer"]["contents"]
            for btn in footer_contents:
                action = btn.get("action", {})
                uri = action.get("uri")
                if uri and ';' in uri:
                    uri_clean = uri.replace(';', '')
                    logging.warning("🚨 URI 中含有非法分號，已移除：%s", uri_clean)
                    action["uri"] = uri_clean
        except Exception as e:
            logging.warning("⚠️ 無法檢查 URI：%s", e)
    else:
        raise ValueError(f"Unsupported message type: {message_type}")
    

    payload = {
        "to": uid,
        "messages": [message]
    }

    def remove_semicolon_uri(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "uri" and isinstance(v, str) and ";" in v:
                    print("移除分號前:", v)
                    obj[k] = v.replace(";", "")
                else:
                    remove_semicolon_uri(v)
        elif isinstance(obj, list):
            for item in obj:
                remove_semicolon_uri(item)

    remove_semicolon_uri(payload)

    print("=== 檢查移除分號後的 payload ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("footer uri:", payload["messages"][0]["contents"]["footer"]["contents"][0]["action"]["uri"])
    print("型態:", type(payload["messages"][0]["contents"]["footer"]["contents"][0]["action"]["uri"]))

    logging.info("📤 準備推播：%s", payload)
    print("=== 最終送出的 payload ===")
    logging.info("=== 最終送出的 payload ===\n%s", json.dumps(payload, ensure_ascii=False, indent=2))

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