import sqlite3
import json
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect("claimguard.db")
c = conn.cursor()
c.execute("SELECT extracted_data FROM documents WHERE claim_id = '3dc5cee5-554e-4702-beb5-a96016fe0b3d' AND document_type = 'HOSPITAL_BILL';")
row = c.fetchone()
if row:
    data = json.loads(row[0])
    for item in data.get('line_items', []):
        print(f"{item.get('description')} | amt: {item.get('amount')} | is_room_linked: {item.get('is_room_linked')} | cat: {item.get('category')}")
