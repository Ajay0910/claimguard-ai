import sqlite3, json
conn = sqlite3.connect("claimguard.db")
c = conn.cursor()
c.execute("SELECT extracted_data FROM documents WHERE claim_id = '3dc5cee5-554e-4702-beb5-a96016fe0b3d' AND document_type = 'REJECTION_LETTER';")
data = json.loads(c.fetchone()[0])
print(f"Total deducted: {data.get('total_deducted')}")
