import os
from dotenv import load_dotenv
import base64
import json

load_dotenv()  # load environment variables from .env file only for local development

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
LINE_UID = os.getenv("LINE_UID")
LINE_TEST_UID = os.getenv("LINE_TEST_UID")
FLASK_ENV = os.getenv("FLASK_ENV", "development")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
NGROK_BASE_URL = os.getenv("NGROK_BASE_URL", "http://localhost:8080")

ORDER_DETAIL_BASE_URL = os.getenv("ORDER_DETAIL_BASE_URL", "http://localhost:8080")
LIFF_ID = os.getenv("LIFF_ID", "default-liff-id")

from flask import Flask

# produce static/config.js to frontend
try:
    app = Flask(__name__)
    config_path = os.path.join(app.static_folder, 'config.js')
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(f'window.APP_CONFIG = {{\n'
                f'  liffId: "{LIFF_ID}",\n'
                f'  orderDetailBaseUrl: "{ORDER_DETAIL_BASE_URL}"\n'
                f'}};')
    if FLASK_ENV == "development":
        print("✅ static/config.js 已更新")
except Exception as e:
    print("⚠️ 無法寫入 static/config.js：", e)

def get_google_credentials():
    b64 = os.environ.get("GOOGLE_CREDENTIALS_JSON_BASE64")
    if not b64:
        raise ValueError("❌ GOOGLE_CREDENTIALS_JSON_BASE64 未設定")
    try:
        decoded = base64.b64decode(b64).decode("utf-8")
        return json.loads(decoded)
    except Exception as e:
        raise ValueError("❌ 解碼 GOOGLE_CREDENTIALS_JSON_BASE64 失敗: " + str(e))
