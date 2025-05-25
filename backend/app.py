from flask import Flask, request, send_from_directory, jsonify, make_response, abort
from flask_cors import CORS
from backend.config import GOOGLE_SHEET_ID, FLASK_ENV, LINE_UID, LINE_TEST_UID, ADMIN_PASSWORD, ORDER_DETAIL_BASE_URL, LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN
from backend.services.google_sheet import get_sheet 
import json
import os
from flask_cors import CORS
from datetime import datetime
from backend.utils import append_by_header
import logging
from backend.flex_templates import build_order_flex
from backend.services.line_notify import send_line_message # Import the function to send LINE messages
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, PostbackEvent


# Load environment variables
#FLASK_ENV = os.getenv('FLASK_ENV', 'production')


# Set up logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')

# Initialize the LINE Bot API
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = Flask(__name__, static_folder='static')
CORS(app, resources={r"/*": {"origins": [
    "http://localhost:5500", 
    "http://127.0.0.1:5500",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://your-custom-domain.com", # replace with your custom domain
    "https://orderingsystem-production.up.railway.app"
]}}) 

'''
# Backend API to get the test UID
# This is used for local testing only
@app.route('/test-uid')
def get_test_uid():
    try:
        print("DEBUG FLASK_ENV (app.py):", FLASK_ENV)
        print("DEBUG LINE_TEST_UID (app.py):", LINE_TEST_UID)
        print("DEBUG type FLASK_ENV:", type(FLASK_ENV))
        print("DEBUG type LINE_TEST_UID:", type(LINE_TEST_UID))
        return jsonify({
            "uid": LINE_TEST_UID if FLASK_ENV == "development" else ""
        })
    except Exception as e:
        print("❗ /test-uid error:", e)
        return jsonify({"error": str(e)}), 500
'''

# Backend API to serve the menu
# Provide the menu data from a JSON file
@app.route('/menu')
def get_menu():
    menu_path = os.path.join(os.path.dirname(__file__), 'menu.json')
    with open(menu_path, encoding='utf-8') as f:
        return jsonify(json.load(f))
    

# Backend API to handle order submission
# Handle the order submission from the frontend
# Ordaer submission page
@app.route('/order', methods=['POST'])
def order():
    try:
        data = request.json
        logging.info("[DEBUG] Received order data: %s", data)

        order_id = data.get('order_id')
        user = data.get('user', '')
        user_id = data.get('user_id', '')
        order_items = data.get('order_items', [])
        note = data.get('note', '')[:100]
        delivery = data.get('delivery', '')
        store_info = data.get('store_info', '').strip()
        payment_status = "貨到付款" if delivery == "711-paid" else "未付款"
        order_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        shipping_status = '未出貨'

        if not order_id or not isinstance(order_items, list) or not order_items:
            return jsonify({'status': 'error', 'message': '缺少 order_id 或 order_items'}), 400
        if not user_id:
            return jsonify({'status': 'error', 'message': '缺少 user_id'}), 400

        sheet = get_sheet("Orders")
        error_items, total, shipping_fee = [], 0, 0

        for item in order_items:
            product = item.get('product', '')
            qty = int(item.get('qty') or 0)
            price = int(item.get('price') or 0)
            line_total = qty * price

            if not product or qty == 0:
                continue

            try:
                append_by_header(sheet, {
                    "訂購時間": order_time,
                    "訂單編號": order_id,
                    "LINE ID": user,
                    "商品名稱": product,
                    "數量": qty,
                    "單價": price,
                    "小計金額": line_total,
                    "付款狀態": payment_status,
                    "狀態修改時間": '',
                    "取貨方式": delivery,
                    "備註": note,
                    "門市資訊": store_info,
                    "出貨狀態": shipping_status,
                    "出貨時間": ''
                })

                if product == '運費':
                    shipping_fee = line_total
                else:
                    total += line_total

            except Exception as err:
                logging.exception("❌ 寫入失敗：商品 %s", product)
                error_items.append({'product': product, 'error': repr(err)})

        if error_items:
            return jsonify({'status': 'partial_success', 'message': '部分商品寫入失敗', 'order_id': order_id, 'errors': error_items}), 207

        final_total = int(total + shipping_fee)

        try:
            flex_content = build_order_flex(
                order_id = order_id,
                order_items = order_items,
                delivery = delivery,
                total = final_total,
                store_info = store_info,
                order_time = order_time
            )
            send_line_message(user_id, message_type='flex', content=flex_content)
            logging.info("✅ 訂單記錄成功：%s (%s)", order_id, user_id)

        except Exception as push_err:
            logging.warning("❗ 推播失敗：%s", repr(push_err))

        logging.info("✅ 訂單記錄成功：%s", order_id)
        logging.info("📤 傳送 Flex 推播內容: %s", flex_content)
        return jsonify({'status': 'success', 'message': '訂單已記錄', 'order_id': order_id})

    except Exception as e:
        logging.exception("❗ 發生未知錯誤")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Backend API to get all orders from Google Sheets
# Provide the order data from Google Sheets
@app.route('/get-orders', methods=['GET'])
def get_orders():
    # Reading all values from the Google Sheets
    rows = get_sheet("Orders").get_all_values()
    headers, data_rows = rows[0], rows[1:] # The fist row is the header
    orders = [dict(zip(headers, row)) for row in data_rows if len(row) >= len(headers)]  # Convert each piece of data into dict (key: field name) and prevent incomplete data
    return jsonify(orders)

# Backend API to update payment status
# Update the payment status in Google Sheets
@app.route('/update-payment', methods=['POST'])
def update_payment():
    try:
        data = request.get_json()
        worksheet = get_sheet("Orders")
        updated = False
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for idx, row in enumerate(worksheet.get_all_records(), start=2):
            if row.get('訂單編號') == data['order_id']:
                worksheet.update_cell(idx, 8, data['new_status'])  # Payment status
                worksheet.update_cell(idx, 9, now)  # Status modification time
                updated = True

        if updated:
            return jsonify({'status': 'success', 'message': '付款狀態已更新'})
        else:
            return jsonify({'status': 'error', 'message': '找不到該筆訂單'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Backend API to save user information
# Save user information to Google Sheets
@app.route('/user-info', methods=['POST'])
def save_user_info():
    try:
        data = request.get_json()
        logging.info("[INFO] Saving user info: %s", data)

        user_id = str(data.get('user_id', '')).strip()
        name = str(data.get('name', '')).strip()
        raw_phone = str(data.get('phone', '')).strip()

        # Phone format check and format to Google Sheets friendly format
        if raw_phone.startswith('+886') and len(raw_phone) == 13:
            phone = raw_phone  # Direct storage in international formats
        elif raw_phone.startswith('09') and len(raw_phone) == 10:
            phone = "'" + raw_phone  # Add single quotes in Taiwanese local format to prevent Sheets from automatically converting to numbers.
        else:
            return jsonify({'status': 'error', 'message': '電話格式錯誤，請輸入正確格式（09xxxxxxxx 或 +886xxxxxxxx）'}), 400

        address = str(data.get('address', '')).strip()
        note = str(data.get('note', '')).strip()
        store_info = str(data.get('store_info', '')).strip()

        # check required fields
        if not user_id:
            return jsonify({'status': 'error', 'message': '缺少 user_id'}), 400
        if not name:
            return jsonify({'status': 'error', 'message': '請填寫姓名'}), 400
        if not address:
            return jsonify({'status': 'error', 'message': '請填寫地址'}), 400

        worksheet = get_sheet("Users")
        headers = worksheet.row_values(1)

        for idx, row in enumerate(worksheet.get_all_records(), start=2):
            if row.get("user_id") == user_id:
                for col_name, value in {
                    "name": name,
                    "phone": phone,
                    "address": address,
                    "note": note,
                    "store_info": store_info
                }.items():
                    if col_name in headers:
                        col_index = headers.index(col_name) + 1
                        worksheet.update_cell(idx, col_index, value)
                logging.info("[OK] User info updated: %s", user_id)
                return jsonify({'status': 'success', 'message': '使用者資料已更新'})

        # append new user info if not found
        append_by_header(worksheet, {
            "user_id": user_id,
            "name": name,
            "phone": phone,
            "address": address,
            "note": note,
            "store_info": store_info
        })
        logging.info("[OK] User info added: %s", user_id)
        return jsonify({'status': 'success', 'message': '使用者資料已新增'})

    except Exception as e:
        logging.exception("❗ Error in saving user info")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    

 # Backend API to get user information   
@app.route('/get-user', methods=['GET'])
def get_user():
    try:
        uid = request.args.get('uid')
        if not uid:
            return jsonify({'status': 'error', 'message': '缺少 UID'}), 400

        for row in get_sheet("Users").get_all_records():
            row["phone"] = str(row.get("phone", ""))
            if row.get("user_id") == uid:
                return jsonify({'status': 'success', 'data': row})
        return jsonify({'status': 'not_found', 'message': '找不到使用者資料'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Backend API to add a new menu item
# Add a new menu item to the JSON file
# update the menu.json file
@app.route('/add-menu-item', methods=['POST'])
def add_menu_item():
    data = request.get_json()
    if not data.get('name') or data.get('price') is None:
        return jsonify({'status': 'error', 'message': '缺少 name 或 price'}), 400

    menu_path = os.path.join(os.path.dirname(__file__), 'menu.json')
    with open(menu_path, 'r+', encoding='utf-8') as f:
        menu = json.load(f)
        if any(item['name'] == data['name'] for item in menu):
            return jsonify({'status': 'error', 'message': '商品已存在'}), 409
        menu.append({'name': data['name'], 'price': data['price']})
        f.seek(0)
        json.dump(menu, f, ensure_ascii=False, indent=2)
        f.truncate()
    return jsonify({'status': 'success', 'message': f"{data['name']} 已上架"})


# Backend API to remove a menu item
# Remove a menu item from the JSON file
@app.route('/remove-menu-item', methods=['POST'])
def remove_menu_item():
    data = request.get_json()
    if not data.get('name'):
        return jsonify({'status': 'error', 'message': '缺少 name'}), 400

    menu_path = os.path.join(os.path.dirname(__file__), 'menu.json')
    with open(menu_path, 'r+', encoding='utf-8') as f:
        menu = json.load(f)
        updated = [item for item in menu if item['name'] != data['name']]
        if len(updated) == len(menu):
            return jsonify({'status': 'error', 'message': '商品不存在'}), 404
        f.seek(0)
        json.dump(updated, f, ensure_ascii=False, indent=2)
        f.truncate()
    return jsonify({'status': 'success', 'message': f"{data['name']} 已下架"})


# shipping rules
RULES_FILE = os.path.join(os.path.dirname(__file__), 'shipping_rules.json')

def default_rules():
    return {
        "711": {
            "base_fee": 129,
            "cod_extra": 5,
            "free_shipping_item_count": 10
        },
        "face_to_face": [
            {
                "regions": ["屏東市", "長治", "麟洛", "西勢", "海豐", "繁華"],
                "free_shipping_min": 1000
            },
            {
                "regions": ["鹽埔", "內埔", "萬丹", "九如", "潮州"],
                "free_shipping_min": 1500
            }
        ]
    }

def load_shipping_rules():
    if not os.path.exists(RULES_FILE):
        with open(RULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_rules(), f, ensure_ascii=False, indent=2)
    with open(RULES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_shipping(delivery, total_amount, item_count, district):
    rules = load_shipping_rules()
    if delivery.startswith("711"):
        base_fee = rules["711"]["base_fee"]
        if "付款" in delivery:
            base_fee += rules["711"]["cod_extra"]
        if item_count >= rules["711"]["free_shipping_item_count"]:
            return 0
        return base_fee
    elif delivery.startswith("面交"):
        for region_rule in rules["face_to_face"]:
            if district in region_rule["regions"] and total_amount >= region_rule["free_shipping_min"]:
                return 0
        return 0  # Delivery in person is scheduled to be free of charge, but if the conditions are not met, additional charges may apply in the future.
    return 0

@app.route('/shipping-rules', methods=['GET'])
def get_shipping_rules():
    return jsonify(load_shipping_rules())

@app.route('/shipping-rules', methods=['POST'])
def update_shipping_rules():
    try:
        new_rules = request.get_json()
        with open(RULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_rules, f, ensure_ascii=False, indent=2)
        return jsonify({'status': 'success', 'message': '運費設定已更新'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/calculate-shipping', methods=['POST'])
def calc_shipping_api():
    data = request.get_json()
    fee = calculate_shipping(
        data.get("delivery", ""),
        float(data.get("total_amount", 0)),
        int(data.get("item_count", 0)),
        data.get("district", "")
    )
    return jsonify({"shipping_fee": fee})

@app.route('/update-shipping', methods=['POST'])
def update_shipping():
    try:
        data = request.get_json()
        worksheet = get_sheet("Orders")
        updated = False
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for idx, row in enumerate(worksheet.get_all_records(), start=2):
            if row.get('訂單編號') == data['order_id']:
                worksheet.update_cell(idx, 13, data['new_status'])  # Shipping status field
                worksheet.update_cell(idx, 14, now)  # Shipping time
                updated = True

        if updated:
            return jsonify({'status': 'success', 'message': '出貨狀態已更新'})
        else:
            return jsonify({'status': 'error', 'message': '找不到該筆訂單'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/check-admin-password', methods=['POST'])
def check_admin_password():
    data = request.get_json()
    password = data.get('password', '')
    if password == ADMIN_PASSWORD:
        return jsonify({'status': 'success'})
    return jsonify({'status': 'fail'}), 401

@app.route('/order/<order_id>')
def order_detail(order_id):
    return send_from_directory('static', 'order_detail.html')

# order status page
@app.route('/order-status')
def order_status_page():
    return send_from_directory('static', 'order_status.html')

# LINE webhook
@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# Set the secret key for session management
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_vue_app(path):
    if path == "" or path == "/":
        return send_from_directory(app.static_folder, 'index.html')
    file_path = os.path.join(app.static_folder, path)
    if os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@handler.add(PostbackEvent)
def handle_postback(event):
    if event.postback.data == "action=contact":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請稍候，客服會盡快與您聯繫：）")
        )
        admin_uid = LINE_UID
        user_uid = event.source.user_id
        line_bot_api.push_message(
            admin_uid,
            TextSendMessage(text=f"📩 使用者 {user_uid} 已點擊「聯絡客服」按鈕，請儘快回覆！")
        )

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    if event.message.text.strip() == "聯絡客服":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請稍候，客服會盡快與您聯繫：）")
        )


# for local testing
'''
@app.route('/admin')
def admin_page():
    return send_from_directory('static', 'admin.html')
'''

@app.after_request
def add_csp_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self' https://* http://localhost:8080 http://127.0.0.1:8080; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdn.tailwindcss.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdn.tailwindcss.com; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdn.tailwindcss.com https://static.line-scdn.net; "
        "connect-src 'self' https://api.line.me https://notify-api.line.me https://static.line-scdn.net https://liffsdk.line-scdn.net https://lineapporderingsystem-production.up.railway.app http://localhost:8080 http://127.0.0.1:8080; "
        "img-src * data:;"
    )
    return response


if __name__ == '__main__':
    # Enable Flask application to run on a specific port
    # Set the port to 8080 or the port specified in the environment variable
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=(FLASK_ENV == "development")) # Enable debug mode only in development environment
