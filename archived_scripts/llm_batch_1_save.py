# -*- coding: utf-8 -*-
"""写入第一批3条LLM提取结果"""
import sqlite3, json

db = r'C:\Users\cc\hermes-sports-bidding\llm_bidding.db'
conn = sqlite3.connect(db)

def save(pid, data, url):
    data['url'] = url
    conn.execute("INSERT OR REPLACE INTO extracted (page_id, data_json) VALUES (?, ?)",
                 (pid, json.dumps(data, ensure_ascii=False)))
    conn.execute("UPDATE pages SET status = 'extracted' WHERE id = ?", (pid,))
    conn.commit()
    print(f"[{pid}] ✅ {data['title'][:50]}... priority={data['priority_tag']}")

# === ID 1: 福清市农村公益电影合同公告 ===
url1 = conn.execute("SELECT url FROM pages WHERE id=1").fetchone()[0]
save(1, {
    "title": "福清市农村公益电影社会化购买服务采购项目政府采购合同公告",
    "project_number": "[350181]FJSJLCZB[GK]2026001",
    "notice_type": "合同公告",
    "industry": "文化体育",
    "region": "福建省福州市福清市",
    "source": "福建省政府采购网",
    "publish_date": "2026-06-29",
    "doc_deadline": None,
    "qa_deadline": None,
    "submission_deadline": None,
    "budget_amount": "316.94万元",
    "ceiling_price": None,
    "bid_bond": None,
    "eligibility": None,
    "scope_of_work": "开展农村公益电影放映，2026年4320场，2027年5280场，2028年5280场，合计14880场",
    "buyer": "福清市文化体育和旅游局",
    "agency": None,
    "contact": "13960731070",
    "amendment": None,
    "winner": "福州遍地开文化传媒有限公司",
    "winning_price": "3,169,440.00元",
    "panelists": None,
    "priority_tag": "NO",
    "priority_reason": None
}, url1)

# === ID 2: 政和县第一中学体育馆修缮竞争性谈判公告 ===
url2 = conn.execute("SELECT url FROM pages WHERE id=2").fetchone()[0]
save(2, {
    "title": "政和县第一中学体育馆修缮项目竞争性谈判公告",
    "project_number": "[350725]FJHS[TP]2026001",
    "notice_type": "竞争性谈判",
    "industry": "建筑",
    "region": "福建省南平市政和县",
    "source": "福建省政府采购网",
    "publish_date": "2026-06-29",
    "doc_deadline": None,
    "qa_deadline": None,
    "submission_deadline": "2026-07-03 09:00:00",
    "budget_amount": "146.00万元",
    "ceiling_price": "1,459,772.00元",
    "bid_bond": "0元",
    "eligibility": "1.满足《中华人民共和国政府采购法》第二十二条规定；2.本采购包为专门面向小微企业采购，供应商须提供中小企业声明函；监狱企业、残疾人福利性单位视同小型、微型企业",
    "scope_of_work": "一中体育馆改造工程，装修面积约1800㎡，工程承包范围：土建、安装",
    "buyer": "政和县第一中学",
    "agency": "福建恒顺工程咨询有限公司",
    "contact": None,
    "amendment": None,
    "winner": None,
    "winning_price": None,
    "panelists": None,
    "priority_tag": "NO",
    "priority_reason": None
}, url2)

# === ID 3: 漳州市龙海区文体旅游局采购意向（多功能一体机）===
url3 = conn.execute("SELECT url FROM pages WHERE id=3").fetchone()[0]
save(3, {
    "title": "漳州市龙海区文化体育和旅游局2026年度（第2批）采购意向",
    "project_number": None,
    "notice_type": "采购意向",
    "industry": "办公设备",
    "region": "福建省漳州市龙海区",
    "source": "福建省政府采购网",
    "publish_date": "2026-06-29",
    "doc_deadline": None,
    "qa_deadline": None,
    "submission_deadline": None,
    "budget_amount": "0.19万元",
    "ceiling_price": None,
    "bid_bond": None,
    "eligibility": None,
    "scope_of_work": "多功能一体机1台，主要功能：多功能打印、复印",
    "buyer": "漳州市龙海区文化体育和旅游局",
    "agency": None,
    "contact": None,
    "amendment": None,
    "winner": None,
    "winning_price": None,
    "panelists": None,
    "priority_tag": "NO",
    "priority_reason": None
}, url3)

print("\n=== 第一批完成！剩余待提取:", conn.execute("SELECT COUNT(*) FROM pages WHERE status='raw'").fetchone()[0], "条 ===")
conn.close()
