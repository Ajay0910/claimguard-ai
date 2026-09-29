import json
with open('../HOSPITAL_BILL.json') as f:
    bill = json.load(f)

for item in bill['line_items']:
    desc = item['description'].get('value', '') if isinstance(item['description'], dict) else item['description']
    cat = item['category'].get('value', '') if isinstance(item['category'], dict) else item['category']
    amt = item['amount'].get('value', 0) if isinstance(item['amount'], dict) else item['amount']
    linked = item.get('is_room_linked', False)
    print(f"{desc}: {amt} | Cat: {cat} | Linked: {linked}")
