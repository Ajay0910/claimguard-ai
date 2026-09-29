import sqlite3
import json

conn = sqlite3.connect("claimguard.db")
c = conn.cursor()
c.execute("SELECT claim_id FROM analysis_runs ORDER BY started_at DESC LIMIT 5;")
for row in c.fetchall():
    print(f"Claim: {row[0]}")
    
c.execute("SELECT extracted_data FROM documents WHERE claim_id = (SELECT claim_id FROM analysis_runs ORDER BY started_at DESC LIMIT 1) LIMIT 1;")
row = c.fetchone()
if row:
    print(row[0][:100])
