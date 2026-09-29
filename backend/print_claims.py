import sqlite3
conn = sqlite3.connect("claimguard.db")
c = conn.cursor()
c.execute("SELECT claim_id FROM analysis_runs ORDER BY started_at DESC LIMIT 5;")
for r in c.fetchall():
    print(r[0])
