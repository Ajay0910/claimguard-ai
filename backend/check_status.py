import sqlite3
import json

conn = sqlite3.connect("claimguard.db")
c = conn.cursor()
c.execute("SELECT status, overall_status, total_monetary_impact FROM analysis_runs WHERE claim_id = '3e69b8c5-3d14-42f2-98f6-777d043ab7a3' ORDER BY started_at DESC LIMIT 1;")
row = c.fetchone()
if row:
    print(f"Run Status: {row[0]}")
    print(f"Overall Status: {row[1]}")
    print(f"Total Impact: {row[2]}")
else:
    print("No runs found")
