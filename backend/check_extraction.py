import sqlite3
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect("claimguard.db")
c = conn.cursor()
c.execute("SELECT document_type, extracted_data FROM documents WHERE claim_id = '3e69b8c5-3d14-42f2-98f6-777d043ab7a3';")
for r in c.fetchall():
    print(f"--- {r[0]} ---")
    data = json.loads(r[1])
    if r[0] == "REJECTION_LETTER":
        print(f"Total Deducted: {data.get('total_deducted')}")
        print(f"Total Approved: {data.get('total_approved')}")
    if r[0] == "HOSPITAL_BILL":
        print("Line items:")
        for item in data.get('line_items', []):
            print(f"- {item.get('description')}: {item.get('amount')} (cat: {item.get('category')})")
