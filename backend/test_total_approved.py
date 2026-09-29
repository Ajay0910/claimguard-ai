import json
with open('../REJECTION_LETTER.json') as f:
    data = json.load(f)
    print("Total Claimed:", data.get('total_claimed', {}).get('value'))
    print("Total Approved:", data.get('total_approved', {}).get('value'))
    print("Total Deducted:", data.get('total_deducted', {}).get('value'))
