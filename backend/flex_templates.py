from datetime import datetime
from backend.config import ORDER_DETAIL_BASE_URL

def build_order_flex(order_id, order_items, delivery, total, store_info='', order_time=None):
    max_display = 5
    visible_items = [item for item in order_items if item['product'] != '運費']
    display_items = visible_items[:max_display]

    DELIVERY_DISPLAY = {
        "711-unpaid": "7-11 超商（純取貨）",
        "711-paid": "7-11 超商（取貨付款）",
        "pickup": "面交取貨"
    }

    product_lines = [
        {
            "type": "text",
            "text": f"- {item['product']} x{item['qty']}",
            "size": "sm",
            "wrap": True
        }
        for item in display_items
    ]

    if len(visible_items) > max_display:
        product_lines.append({
            "type": "text",
            "text": f"...還有 {len(visible_items) - max_display} 項商品",
            "size": "xs",
            "color": "#999999",
            "wrap": True
        })

    shipping_fee = int(next((item['price'] for item in order_items if item['product'] == '運費'), 0))
    order_time_str = order_time or datetime.now().strftime("%Y-%m-%d %H:%M")

    uri = f"{ORDER_DETAIL_BASE_URL}?order_id={order_id}".strip()
    print("DEBUG: 組裝後的 URI =", repr(uri))
    uri = uri.replace(";", "").rstrip("/")
    print("DEBUG: 清理分號後的 URI =", repr(uri))
    assert not uri.endswith(";"), f"❌ URI 含有非法分號: {uri}"
    print("⚠️ 最終 uri (build_order_flex return 前):", repr(uri))
    print("DEBUG: final uri 字元列表：", list(uri))
    
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "🧾 老宅私廚 訂單成立", "weight": "bold", "size": "md", "color": "#1DB446"},
                {"type": "text", "text": f"訂單編號：{order_id}", "size": "xs", "color": "#999999"},
                {"type": "text", "text": f"下單時間：{order_time_str}", "size": "xs", "color": "#999999"}
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": list(filter(None, [
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {"type": "text", "text": "商品明細：", "size": "sm", "weight": "bold"},
                        *product_lines
                    ]
                },
                {"type": "text", "text": f"取貨方式：{DELIVERY_DISPLAY.get(delivery, delivery)}", "size": "sm", "wrap": True},
                {"type": "text", "text": f"門市資訊：{store_info}", "size": "sm", "wrap": True} if store_info else None,
                {"type": "separator"},
                {"type": "text", "text": f"商品小計：${total - shipping_fee}", "size": "sm"},
                {"type": "text", "text": f"運費：${shipping_fee}", "size": "sm"},
                {"type": "text", "text": f"💰 總金額：${total}", "size": "md", "weight": "bold", "color": "#007AFF"}
            ]))
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#1DB446",
                    "action": {
                        "type": "uri",
                        "label": "查看訂單明細",
                        "uri": uri
                    }
                },
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#999999",
                    "action": {
                        "type": "postback",
                        "label": "聯絡客服",
                        "data": "action=contact"
                    }
                }
            ]
        }
    }

    return {
        "altText": f"訂單成立通知：{order_id}",
        "contents": bubble
    }