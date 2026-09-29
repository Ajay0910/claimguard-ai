import sqlite3
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect("claimguard.db")
c = conn.cursor()
c.execute("SELECT claim_id, result_data FROM analysis_runs ORDER BY started_at DESC LIMIT 5;")
for row in c.fetchall():
    if row[0].startswith('3dc5cee5'):
        data = json.loads(row[1])
        print(f"Overall Status: {data.get('overall_status')}")
        print(f"Summary: {data.get('summary')}")
        for rule in data['rule_verdicts']:
            print(f"{rule['rule_name']} - {rule['status']}")
            print(f"Finding: {rule.get('finding')}")
            print("----")
