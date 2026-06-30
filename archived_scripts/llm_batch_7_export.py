# -*- coding: utf-8 -*-
"""导出第7批"""
import sqlite3, re
db = r'C:\Users\cc\hermes-sports-bidding\llm_bidding.db'
conn = sqlite3.connect(db)
rows = conn.execute("SELECT id, title FROM pages WHERE status='raw' ORDER BY id LIMIT 20").fetchall()
for pid, title in rows:
    print(f"[{pid:>4}] {title[:70]}")
conn.close()
