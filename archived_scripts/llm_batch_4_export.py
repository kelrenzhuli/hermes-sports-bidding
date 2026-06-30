# -*- coding: utf-8 -*-
"""导出第4批清洗文本 (20条)"""
import sqlite3, re
db = r'C:\Users\cc\hermes-sports-bidding\llm_bidding.db'
conn = sqlite3.connect(db)
rows = conn.execute("SELECT id, title, raw_html FROM pages WHERE status='raw' ORDER BY id LIMIT 20").fetchall()

data = []
for pid, title, html in rows:
    text = ""
    for p in [r'<div class="noticeArea">(.*?)(?:</div>\s*</div>|</div>\s*<div)', r'<div class="noticeArea">(.*?)</div>',
              r'id="articleCont"[^>]*>(.*?)</div>', r'<div class="u-content[^>]*>(.*?)</div>']:
        m = re.search(p, html, re.DOTALL) if not text else None
        if m: text = m.group(1)
    if not text: text = html
    clean = re.sub(r'<style>.*?</style>', '', text, flags=re.DOTALL)
    clean = re.sub(r'<[^>]+>', '\n', clean)
    clean = re.sub(r'\n{3,}', '\n\n', clean)
    clean = re.sub(r'&nbsp;', ' ', clean).strip()[:600]
    data.append((pid, title, clean))
    fn = f'llm_t{pid}.txt'
    with open(fn, 'w', encoding='utf-8') as f:
        f.write(f"标题: {title}\n\n{clean}")
    
    # 快速打印摘要
    typ = "意" if "意向" in title else ("合" if "合同" in title else ("结" if "结果" in title else ("招" if any(x in title for x in ["招标","磋商","谈判"]) else "其")))
    items = "、".join(re.findall(r'采购内容[：:]\s*([^<&\n]{3,20})', clean)[:2])
    if not items:
        items = title[40:70] if len(title) > 40 else title[-20:]
    print(f"[{pid:>4}] [{typ}] {title[:50]:50s} {items[:35]}")

conn.close()
