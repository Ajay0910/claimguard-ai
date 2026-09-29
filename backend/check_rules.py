import sqlite3
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect("claimguard.db")
c = conn.cursor()
c.execute("SELECT result_data FROM analysis_runs WHERE claim_id = '92ec9d42-3e4d-40c3-9d02-8bb531543d28' ORDER BY started_at DESC LIMIT 1;")
row = c.fetchone()
if row:
    data = json.loads(row[0])
    print(f"Overall Status: {data.get('overall_status')}")
    print(f"Total Impact: {data.get('total_monetary_impact')}")
    for rule in data['rule_verdicts']:
        print(f"{rule['rule_name']} - {rule['status']} - {rule.get('monetary_impact')}")
        print(f"Finding: {rule.get('finding')}")
        print("----")
else:
    print("No runs found")
