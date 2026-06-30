# -*- coding: utf-8 -*-
"""导出清洗后的公告正文，每条约500字，方便LLM批量读取"""
import sqlite3, re

db = r'C:\Users\cc\hermes-sports-bidding\llm_bidding.db'
conn = sqlite3.connect(db)

rows = conn.execute("""
    SELECT p.id, p.title, p.notice_type, p.url, p.raw_html
    FROM pages p WHERE p.status='raw'
    ORDER BY p.id LIMIT 10
""").fetchall()

for pid, title, nt, url, html in rows:
    # 提取noticeArea内容
    text = ""
    for pattern in [r'<div class="noticeArea">(.*?)(?:</div>\s*</div>|</div>\s*<div[^>]*class=")',
                    r'<div class="noticeArea">(.*?)</div>',
                    r'id="articleCont"[^>]*>(.*?)</div>']:
        m = re.search(pattern, html, re.DOTALL)
        if m:
            text = m.group(1)
            break
    
    if not text:
        text = html
    
    # 清理HTML标签
    clean = re.sub(r'<head>.*?</head>', '', text, flags=re.DOTALL)
    clean = re.sub(r'<style>.*?</style>', '', clean, flags=re.DOTALL)
    clean = re.sub(r'<script>.*?</script>', '', clean, flags=re.DOTALL)
    clean = re.sub(r'<[^>]+>', '\n', clean)
    clean = re.sub(r'\n{3,}', '\n\n', clean)
    clean = re.sub(r'&nbsp;', ' ', clean)
    clean = clean.strip()
    # 截取前800字
    clean = clean[:800]
    
    fn = f'llm_text_{pid}.txt'
    with open(fn, 'w', encoding='utf-8') as f:
        f.write(f"标题: {title}\n类型: {nt}\nURL: {url}\n\n正文:\n{clean}")
    
    print(f"[{pid}] {title[:50]:50s} 正文:{len(clean)}字")

conn.close()
