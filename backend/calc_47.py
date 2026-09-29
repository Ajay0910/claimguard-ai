import json
with open('../HOSPITAL_BILL.json') as f:
    bill = json.load(f)

amounts = []
for item in bill['line_items']:
    amt = item['amount'].get('value', 0) if isinstance(item['amount'], dict) else item['amount']
    amounts.append(amt)

target = 47954.60
eligible_before_copay = target / 0.9 # 53282.88...

import itertools
print("Target Eligible before copay:", eligible_before_copay)

