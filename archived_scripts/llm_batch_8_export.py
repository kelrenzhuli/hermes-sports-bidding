# -*- coding: utf-8 -*-
"""导出第8批"""
import sqlite3
db = r'C:\Users\cc\hermes-sports-bidding\llm_bidding.db'
conn = sqlite3.connect(db)
rows = conn.execute("SELECT id, title FROM pages WHERE status='raw' ORDER BY id LIMIT 25").fetchall()
for pid, title in rows:
    tags = []
    for kw in ["省运会","世界杯","赛事","比赛","龙舟","棒球","足球","训练","健身",
               "体育嘉年华","运动队","体育交流","智慧","智能","器材","比赛服","装备","运动服"]:
        if kw in title: tags.append(kw)
    tag_str = "★" + ",".join(tags) if tags else "  "
    print(f"[{pid:>4}] {tag_str} {title[:70]}")
conn.close()
