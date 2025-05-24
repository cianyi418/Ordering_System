import os
import pytest
from dotenv import load_dotenv
from Ordering_System.backend.services.line_notify import send_line_message
from Ordering_System.backend.flex_templates import build_order_flex

load_dotenv()

dummy_order = {
    'order_id': 'ORDER-TEST-1234',
    'order_items': [
    {'product': '玉米水餃', 'qty': 3, 'price': 100},
    {'product': '泡菜水餃', 'qty': 2, 'price': 100},
    {'product': '運費', 'qty': 1, 'price': 49}
    ],
    'delivery': '711-unpaid',
    'total': 500,
    'shipping_fee': 49
}

@pytest.mark.skip(reason="這是手動測試項目，會觸發實際推播")
def test_push_flex_message():
    uid = os.getenv("LINE_TEST_UID")
    assert uid, "請確認 .env 中有設定 LINE_TEST_UID"
    
    # ✅ 用 dictionary unpacking 解構傳入參數
    flex_msg = build_order_flex(**dummy_order)
    status, response = send_line_message(uid, message_type='flex', content=flex_msg)

    print("Status:", status)
    print("Response:", response)

    assert status == 200
