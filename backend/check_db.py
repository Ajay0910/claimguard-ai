import sqlite3
import json
conn = sqlite3.connect("claimguard.db")
c = conn.cursor()
c.execute("SELECT document_type, extracted_data FROM documents WHERE claim_id = '92ec9d42-3e4d-40c3-9d02-8bb531543d28';")
for r in c.fetchall():
    if r[0] == 'REJECTION_LETTER':
        data = json.loads(r[1])
        print(f"Total Deducted: {data.get('total_deducted')}")
        print(f"Total Approved: {data.get('total_approved')}")
