from flask import Flask, request, jsonify
import json
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

RULES_FILE = 'shipping_rules.json'

# Default freight rules (if not present at first startup)
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

# Make sure the file exists
if not os.path.exists(RULES_FILE):
    with open(RULES_FILE, 'w', encoding='utf-8') as f:
        json.dump(default_rules(), f, ensure_ascii=False)

@app.route('/shipping-rules', methods=['GET'])
def get_shipping_rules():
    with open(RULES_FILE, 'r', encoding='utf-8') as f:
        rules = json.load(f)
    return jsonify(rules)

@app.route('/shipping-rules', methods=['POST'])
def update_shipping_rules():
    try:
        rules = request.get_json()
        with open(RULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False)
        return jsonify({'status': 'success', 'message': '運費規則已更新'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@app.route('/calculate-shipping', methods=['POST'])
def calculate_shipping():
    try:
        data = request.get_json()
        delivery = data.get('delivery')  # For example, 'face-to-face delivery', '711 supermarket pickup (no payment)', '711 supermarket pickup + payment'
        total_amount = data.get('total_amount', 0)
        item_count = data.get('item_count', 0)
        district = data.get('district', '')

        with open(RULES_FILE, 'r', encoding='utf-8') as f:
            rules = json.load(f)

        if '面交' in delivery:
            for rule in rules['face_to_face']:
                if district in rule['regions'] and total_amount >= rule['free_shipping_min']:
                    return jsonify({'shipping_fee': 0})
            return jsonify({'shipping_fee': 0})  # Free delivery by default (if not specified, it will be fixed at 0 dollars)

        elif '711 超商取貨' in delivery:
            fee = rules['711']['base_fee']
            if '付款' in delivery:
                fee += rules['711'].get('cod_extra', 0)
            if item_count >= rules['711']['free_shipping_item_count']:
                fee = 0
            return jsonify({'shipping_fee': fee})

        return jsonify({'shipping_fee': 0})  # Default other methods for free shipping
    except Exception as e:
        return jsonify({'error': str(e)}), 500

'''
if __name__ == '__main__':
    app.run(port=8081)
'''