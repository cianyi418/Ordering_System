import os
import base64
import json
from dotenv import load_dotenv
from flask import Flask

# === Load .env only in development ===
load_dotenv()

# === Reading environment variables ===
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
LINE_UID = os.getenv("LINE_UID")
LINE_TEST_UID = os.getenv("LINE_TEST_UID")
FLASK_ENV = os.getenv("FLASK_ENV", "development")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
NGROK_BASE_URL = os.getenv("NGROK_BASE_URL", "http://localhost:8080")


# Remove illegal characters at the end (such as semicolons or extra slashes)
ORDER_DETAIL_BASE_URL = os.getenv("ORDER_DETAIL_BASE_URL", "http://localhost:8080").rstrip(";/ ")
VITE_LIFF_ID = os.getenv("VITE_LIFF_ID", "default-liff-id")

# Optional debug print
print("✅ ORDER_DETAIL_BASE_URL:", repr(ORDER_DETAIL_BASE_URL))
print("✅ ORDER_DETAIL_BASE_URL 字元列表：", list(ORDER_DETAIL_BASE_URL))

# === Write the front-end static/config.js to call Vue ===
try:
    app = Flask(__name__)
    config_path = os.path.join(app.static_folder, 'config.js')
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(f'window.APP_CONFIG = {{\n'
                f'  liffId: "{VITE_LIFF_ID}",\n'
                f'  orderDetailBaseUrl: "{ORDER_DETAIL_BASE_URL}"\n'
                f'}};')
    print("✅ static/config.js 已更新")
    print("✅ ORDER_DETAIL_BASE_URL:", repr(ORDER_DETAIL_BASE_URL))
except Exception as e:
    print("⚠️ 無法寫入 static/config.js：", e)

# === Parse Google Sheets key (base64) ===
def get_google_credentials():
    b64 = os.environ.get("GOOGLE_CREDENTIALS_JSON_BASE64")
    if not b64:
        raise ValueError("❌ GOOGLE_CREDENTIALS_JSON_BASE64 未設定")
    try:
        decoded = base64.b64decode(b64).decode("utf-8")
        return json.loads(decoded)
    except Exception as e:
        raise ValueError("❌ 解碼 GOOGLE_CREDENTIALS_JSON_BASE64 失敗: " + str(e))
