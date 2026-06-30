# -*- coding: utf-8 -*-
"""导出前3条HTML供LLM提取"""
import sqlite3, base64

db = r'C:\Users\cc\hermes-sports-bidding\llm_bidding.db'
conn = sqlite3.connect(db)

rows = conn.execute("SELECT id, title, url, raw_html FROM pages WHERE status='raw' ORDER BY id LIMIT 3").fetchall()

for pid, title, url, html in rows:
    fn = f'llm_batch_1_id{pid}.html'
    with open(fn, 'w', encoding='utf-8') as f:
        f.write(html or "")
    
    # 打印关键摘要
    clean = html[:200].replace('\n', ' ').replace('\r', '')
    print(f"[{pid}] {title}")
    print(f"  URL: {url}")
    print(f"  HTML预览: {clean[:150]}...")
    print(f"  文件大小: {len(html)} bytes")
    print()

conn.close()
