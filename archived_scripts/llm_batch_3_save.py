# -*- coding: utf-8 -*-
"""写入第3批LLM提取结果 (IDs 8-17, 不含10)"""
import sqlite3, json

db = r'C:\Users\cc\hermes-sports-bidding\llm_bidding.db'
conn = sqlite3.connect(db)

def save(pid, data):
    url = conn.execute("SELECT url FROM pages WHERE id=?", (pid,)).fetchone()[0]
    data['url'] = url
    conn.execute("INSERT OR REPLACE INTO extracted (page_id, data_json) VALUES (?, ?)",
                 (pid, json.dumps(data, ensure_ascii=False)))
    conn.execute("UPDATE pages SET status = 'extracted' WHERE id = ?", (pid,))
    conn.commit()
    print(f"[{pid}] ✅ {data['title'][:50]:50s} tag={data['priority_tag']}")

e = lambda: None  # standard empty value helper
def empty():
    return {"doc_deadline":None,"qa_deadline":None,"submission_deadline":None,"ceiling_price":None,
            "bid_bond":None,"eligibility":None,"agency":None,"contact":None,"amendment":None,
            "winner":None,"winning_price":None,"panelists":None,"priority_reason":None}

base = {"source":"福建省政府采购网","publish_date":"2026-06-29"}

# [8] 连城县文体旅游局 - 采购意向: 空调机
d = {**base, **empty()}
d.update({"title":"连城县文化体育和旅游局2026年度（第1批）采购意向","notice_type":"采购意向","industry":"办公设备",
          "region":"福建省龙岩市连城县","budget_amount":"未公开","scope_of_work":"空调机采购3台，办公需要",
          "buyer":"连城县文化体育和旅游局","priority_tag":"NO"})
save(8, d)

# [9] 双十中学体育馆修缮合同
d = {**base, **empty()}
d.update({"title":"双十中学枋湖校区多功能学术交流厅、教学楼及体育馆部分修缮政府采购合同公告","notice_type":"合同公告",
          "industry":"建筑","region":"福建省厦门市湖里区","budget_amount":"292.36万元",
          "scope_of_work":"双十中学枋湖校区多功能学术交流厅、教学楼及体育馆部分修缮",
          "buyer":"福建省厦门双十中学","contact":"0592-5766199","winner":"厦门市泉艺建设集团有限公司",
          "winning_price":"2,923,600.00元","priority_tag":"NO"})
save(9, d)

# [11] 诏安县A4彩色打印机直接订购合同
d = {**base, **empty()}
d.update({"title":"诏安县文化体育和旅游局A4彩色打印机直接订购采购合同","notice_type":"合同公告",
          "industry":"办公设备","region":"福建省漳州市诏安县","budget_amount":"未公开",
          "scope_of_work":"A4彩色打印机采购","buyer":"诏安县文化体育和旅游局","priority_tag":"NO"})
save(11, d)

# [12] 武夷山市文体旅游局采购意向: 征兵启动仪式（非体育赛事）
d = {**base, **empty()}
d.update({"title":"武夷山市文化体育和旅游局2026年度（第6批）采购意向","notice_type":"采购意向",
          "industry":"公共活动","region":"福建省南平市武夷山市","budget_amount":"未公开",
          "scope_of_work":"2026年下半年福建省征兵启动仪式",
          "buyer":"武夷山市文化体育和旅游局","priority_tag":"NO"})
save(12, d)

# [13] 漳州体育训练基地采购意向: 便携式计算机
d = {**base, **empty()}
d.update({"title":"福建省漳州体育训练基地2026年度（第2批）采购意向","notice_type":"采购意向",
          "industry":"办公设备","region":"福建省漳州市","budget_amount":"未公开",
          "scope_of_work":"便携式计算机1台，办公使用",
          "buyer":"福建省漳州体育训练基地","priority_tag":"NO"})
save(13, d)

# [14] 漳州体育训练基地采购意向: 复印纸
d = {**base, **empty()}
d.update({"title":"福建省漳州体育训练基地2026年度（第1批）采购意向","notice_type":"采购意向",
          "industry":"办公用品","region":"福建省漳州市","budget_amount":"未公开",
          "scope_of_work":"复印纸采购480包，办公使用",
          "buyer":"福建省漳州体育训练基地","priority_tag":"NO"})
save(14, d)

# [15] 奥体中心空调直接选定合同
d = {**base, **empty()}
d.update({"title":"福建省奥林匹克体育中心空调机直接选定采购合同","notice_type":"合同公告",
          "industry":"办公设备","region":"福建省福州市鼓楼区","budget_amount":"未公开",
          "scope_of_work":"空调机采购","buyer":"福建省奥林匹克体育中心","priority_tag":"NO"})
save(15, d)

# [16] 奥体中心采购意向: 空调机
d = {**base, **empty()}
d.update({"title":"福建省奥林匹克体育中心2026年度（第10批）采购意向","notice_type":"采购意向",
          "industry":"办公设备","region":"福建省福州市鼓楼区","budget_amount":"未公开",
          "scope_of_work":"2026年框架协议采购空调机1台",
          "buyer":"福建省奥林匹克体育中心","priority_tag":"NO"})
save(16, d)

# [17] 东山县文体旅游局采购意向: 旅游宣传片
d = {**base, **empty()}
d.update({"title":"东山县文化体育和旅游局2026年度（第2批）采购意向","notice_type":"采购意向",
          "industry":"文化媒体","region":"福建省漳州市东山县","budget_amount":"未公开",
          "scope_of_work":"2026年在福建新闻联播等栏目中投放旅游形象宣传片",
          "buyer":"东山县文化体育和旅游局","priority_tag":"NO"})
save(17, d)

remaining = conn.execute("SELECT COUNT(*) FROM pages WHERE status='raw'").fetchone()[0]
print(f"\n=== 第3批完成！剩余: {remaining} 条 ===")
conn.close()
