# -*- coding: utf-8 -*-
"""导出第5批 (20条)"""
import sqlite3, re
db = r'C:\Users\cc\hermes-sports-bidding\llm_bidding.db'
conn = sqlite3.connect(db)
rows = conn.execute("SELECT id, title, raw_html FROM pages WHERE status='raw' ORDER BY id LIMIT 20").fetchall()

for pid, title, html in rows:
    text = ""
    for p in [r'<div class="noticeArea">(.*?)(?:</div>\s*</div>|</div>\s*<div[^>]class=)', r'<div class="noticeArea">(.*?)</div>',
              r'id="articleCont"[^>]*>(.*?)</div>']:
        m = re.search(p, html, re.DOTALL)
        if m and not text: text = m.group(1)
    if not text: text = html
    clean = re.sub(r'<style>.*?</style>', '', text, flags=re.DOTALL)
    clean = re.sub(r'<[^>]+>', '\n', clean)
    clean = re.sub(r'\n{3,}', '\n\n', clean)
    clean = re.sub(r'&nbsp;', ' ', clean).strip()[:500]
    
    items = re.findall(r'采购(?:内容|项目名?称)[：:]\s*([^<&\n]{3,30})', clean)
    item_str = items[0] if items else (title[45:75] if len(title)>45 else title[-25:])
    print(f"[{pid:>4}] {title[:50]:50s} {item_str[:35]}")

conn.close()
