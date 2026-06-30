# -*- coding: utf-8 -*-
"""导出第2批HTML (IDs 4-7)"""
import sqlite3
db = r'C:\Users\cc\hermes-sports-bidding\llm_bidding.db'
conn = sqlite3.connect(db)
rows = conn.execute("SELECT id, title, raw_html FROM pages WHERE status='raw' ORDER BY id LIMIT 4").fetchall()
for pid, title, html in rows:
    fn = f'llm_batch_2_id{pid}.html'
    with open(fn, 'w', encoding='utf-8') as f:
        f.write(html or "")
    print(f"[{pid}] {title[:60]} ({len(html)} bytes)")
conn.close()
