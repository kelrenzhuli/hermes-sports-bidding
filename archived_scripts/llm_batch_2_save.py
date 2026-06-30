# -*- coding: utf-8 -*-
"""写入第2批LLM提取结果 (IDs 4-7)"""
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
    print(f"[{pid}] ✅ {data['title'][:55]:55s} tag={data['priority_tag']}")

# ID 4: 漳州市龙海区文体旅游局采购意向（第1批）- 多功能一体机
save(4, {
    "title": "漳州市龙海区文化体育和旅游局2026年度（第1批）采购意向",
    "project_number": None,
    "notice_type": "采购意向",
    "industry": "办公设备",
    "region": "福建省漳州市龙海区",
    "source": "福建省政府采购网",
    "publish_date": "2026-06-29",
    "doc_deadline": None, "qa_deadline": None, "submission_deadline": None,
    "budget_amount": "0.19万元",
    "ceiling_price": None, "bid_bond": None, "eligibility": None,
    "scope_of_work": "多功能一体机1台，功能：多功能打印、复印",
    "buyer": "漳州市龙海区文化体育和旅游局",
    "agency": None, "contact": None, "amendment": None,
    "winner": None, "winning_price": None, "panelists": None,
    "priority_tag": "NO", "priority_reason": None
})

# ID 5: 鼓岭缘中美青少年棒球友谊赛合同公告 - ★体育赛事
save(5, {
    "title": "2026年鼓岭缘中美青少年棒球友谊赛暨体育交流周项目政府采购合同公告",
    "project_number": "[350101]ZZXM[GK]2026001",
    "notice_type": "合同公告",
    "industry": "体育赛事",
    "region": "福建省福州市仓山区",
    "source": "福建省政府采购网",
    "publish_date": "2026-06-29",
    "doc_deadline": None, "qa_deadline": None, "submission_deadline": None,
    "budget_amount": "925.23万元",
    "ceiling_price": None, "bid_bond": None, "eligibility": None,
    "scope_of_work": "2026年鼓岭缘中美青少年棒球友谊赛活动执行，含赛事组织、舞台搭建、宣传等",
    "buyer": "福州市人民政府外事办公室",
    "agency": None,
    "contact": "0591-87622096",
    "amendment": None,
    "winner": "福州广播电视台",
    "winning_price": "9,252,344.80元",
    "panelists": None,
    "priority_tag": "YES",
    "priority_reason": "体育赛事运营-中美青少年棒球友谊赛活动执行"
})

# ID 6: 省运会群众项目龙舟比赛合同公告 - ★体育赛事
save(6, {
    "title": "福建省第十八届运动会群众项目龙舟比赛暨2026年福建省全民健身运动会龙舟总决赛政府采购合同公告",
    "project_number": "[350104]GYG[CS]2026001",
    "notice_type": "合同公告",
    "industry": "体育赛事",
    "region": "福建省福州市仓山区",
    "source": "福建省政府采购网",
    "publish_date": "2026-06-26",
    "doc_deadline": None, "qa_deadline": None, "submission_deadline": None,
    "budget_amount": "79.80万元",
    "ceiling_price": None, "bid_bond": None, "eligibility": None,
    "scope_of_work": "赛事服务（含场地布置、氛围布置、竞赛器材、裁判器材、裁判员及工作人员酬劳、服装费、食宿费等）",
    "buyer": "福州市仓山区文化体育和旅游局",
    "agency": None,
    "contact": "0591-83588725",
    "amendment": None,
    "winner": "福州市仓山区文化旅游投资集团有限公司",
    "winning_price": "798,000.00元",
    "panelists": None,
    "priority_tag": "YES",
    "priority_reason": "体育赛事运营-省级运动会龙舟比赛"
})

# ID 7: 福建省奥林匹克体育中心田径场跑道改造项目合同公告
save(7, {
    "title": "福建省奥林匹克体育中心田径场跑道改造项目政府采购合同公告",
    "project_number": "[350001]DHZB[GK]2026001",
    "notice_type": "合同公告",
    "industry": "体育设施",
    "region": "福建省福州市鼓楼区",
    "source": "福建省政府采购网",
    "publish_date": "2026-06-26",
    "doc_deadline": None, "qa_deadline": None, "submission_deadline": None,
    "budget_amount": "367.98万元",
    "ceiling_price": None, "bid_bond": None, "eligibility": None,
    "scope_of_work": "奥体中心田径场跑道改造",
    "buyer": "福建省奥林匹克体育中心",
    "agency": None,
    "contact": "0591-87829304",
    "amendment": None,
    "winner": "广州同欣体育股份有限公司",
    "winning_price": "3,679,762.04元",
    "panelists": None,
    "priority_tag": "NO",
    "priority_reason": None
})

remaining = conn.execute("SELECT COUNT(*) FROM pages WHERE status='raw'").fetchone()[0]
print(f"\n=== 第2批完成！剩余: {remaining} 条 ===")
conn.close()
