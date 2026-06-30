# -*- coding: utf-8 -*-
"""导出第9批"""
import sqlite3
db = r'C:\Users\cc\hermes-sports-bidding\llm_bidding.db'
conn = sqlite3.connect(db)
rows = conn.execute("SELECT id, title FROM pages WHERE status='raw' ORDER BY id LIMIT 25").fetchall()
for pid, title in rows:
    t = ""
    for kw in ["省运会","世界杯","比赛","训练","健身","器材","装备","服装","智慧","智能"]:
        if kw in title: t = f"★{kw}"
    print(f"[{pid:>4}] {t:12s} {title[:70]}")
conn.close()
