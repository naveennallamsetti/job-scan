import sqlite3

conn = sqlite3.connect('backend/jobs.db')
cursor = conn.cursor()
cursor.execute("SELECT id, portal, title, url FROM jobs WHERE portal IN ('LinkedIn Jobs', 'Naukri.com')")
rows = cursor.fetchall()
conn.close()

for r in rows:
    print(f"[{r[1]}] {r[2]}: {r[3]}")
