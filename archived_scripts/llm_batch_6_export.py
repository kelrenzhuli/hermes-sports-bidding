# -*- coding: utf-8 -*-
"""导出第6批 (20条)"""
import sqlite3, re
db = r'C:\Users\cc\hermes-sports-bidding\llm_bidding.db'
conn = sqlite3.connect(db)
rows = conn.execute("SELECT id, title, raw_html FROM pages WHERE status='raw' ORDER BY id LIMIT 20").fetchall()
for pid, title, html in rows:
    text = ""
    for p in [r'<div class="noticeArea">(.*?)(?:</div>\s*</div>|</div>\s*<div[^>]class=)', r'<div class="noticeArea">(.*?)</div>']:
        m = re.search(p, html, re.DOTALL) if not text else None
        if m: text = m.group(1)
    if not text: text = html
    clean = re.sub(r'<style>.*?</style>', '', text, flags=re.DOTALL)
    clean = re.sub(r'<[^>]+>', '\n', clean)
    clean = re.sub(r'\n{3,}', '\n\n', clean)
    clean = re.sub(r'&nbsp;', ' ', clean).strip()[:400]
    items = re.findall(r'采购(?:内容|项目名称)[：:]\s*([^<&\n]{3,30})', clean)
    item = items[0][:35] if items else (title[50:75] if len(title)>50 else title[-25:])
    print(f"[{pid:>4}] {title[:48]:48s} {item}")
conn.close()
