import sqlite3
import json
import pprint

conn = sqlite3.connect('backend/claimguard.db')
cursor = conn.cursor()
cursor.execute('SELECT analysis_run_id FROM rule_verdicts WHERE monetary_impact = 277450.0 LIMIT 1')
aid = cursor.fetchone()[0]

cursor.execute(f"SELECT claim_id FROM analysis_runs WHERE id = '{aid}'")
cid = cursor.fetchone()[0]

for dtype in ['HOSPITAL_BILL', 'INSURANCE_POLICY', 'REJECTION_LETTER']:
    cursor.execute(f"SELECT extracted_data FROM documents WHERE claim_id = '{cid}' AND document_type = '{dtype}'")
    with open(f"{dtype}.json", "w") as f:
        f.write(cursor.fetchone()[0])
