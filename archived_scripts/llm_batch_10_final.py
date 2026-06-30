# -*- coding: utf-8 -*-
"""写入最后一批 (IDs 209-255)"""
import sqlite3, json
db = r'C:\Users\cc\hermes-sports-bidding\llm_bidding.db'
conn = sqlite3.connect(db)
B = {"source":"福建省政府采购网","publish_date":"2026-06-29"}
E = {"doc_deadline":None,"qa_deadline":None,"submission_deadline":None,"ceiling_price":None,
     "bid_bond":None,"eligibility":None,"agency":None,"contact":None,"amendment":None,
     "winner":None,"winning_price":None,"panelists":None,"priority_reason":None}
def s(pid, d):
    d = {**B,**E,**d}; d['url']=conn.execute("SELECT url FROM pages WHERE id=?",(pid,)).fetchone()[0]
    conn.execute("INSERT OR REPLACE INTO extracted (page_id, data_json) VALUES (?, ?)",(pid,json.dumps(d,ensure_ascii=False)))
    conn.execute("UPDATE pages SET status='extracted' WHERE id=?",(pid,)); conn.commit()

s(209,{"title":"福建省泉州体育运动学校2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省泉州市","buyer":"福建省泉州体育运动学校","priority_tag":"NO"})

# ⭐ [211] 智慧健身角和五人制足球场 - AI体育！
s(211,{"title":"惠安县文化体育和旅游局智慧健身角和五人制足球场采购项目合同公告",
       "notice_type":"合同公告","industry":"体育赛事","region":"福建省泉州市惠安县",
       "budget_amount":"未公开",
       "scope_of_work":"智慧健身角和五人制足球场采购",
       "buyer":"惠安县文化体育和旅游局",
       "priority_tag":"YES","priority_reason":"AI体育-智慧健身角+五人制足球场"})

s(213,{"title":"长汀县文化体育和旅游局便携式计算机直接订购采购合同","notice_type":"合同公告",
       "industry":"办公设备","region":"福建省龙岩市长汀县","buyer":"长汀县文化体育和旅游局","priority_tag":"NO"})

s(215,{"title":"福建省泉州体育运动学校2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省泉州市","buyer":"福建省泉州体育运动学校","priority_tag":"NO"})

# ⭐ [218] 省运会训练参赛器材
s(218,{"title":"漳州市重点少年儿童业余体育学校十八届省运会各项目训练参赛器材设施设备采购合同公告",
       "notice_type":"合同公告","industry":"体育赛事","region":"福建省漳州市",
       "scope_of_work":"省运会各项目训练、参赛器材设施设备采购",
       "buyer":"漳州市重点少年儿童业余体育学校",
       "priority_tag":"YES","priority_reason":"体育赛事设备-省运会训练参赛器材采购"})

s(220,{"title":"福建省龙岩体育运动学校2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省龙岩市","buyer":"福建省龙岩体育运动学校","priority_tag":"NO"})

s(222,{"title":"长汀县文化体育和旅游局多功能一体机直接订购采购合同","notice_type":"合同公告",
       "industry":"办公设备","region":"福建省龙岩市长汀县","buyer":"长汀县文化体育和旅游局","priority_tag":"NO"})

s(224,{"title":"长汀县文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省龙岩市长汀县","buyer":"长汀县文化体育和旅游局","priority_tag":"NO"})

s(225,{"title":"福州市马尾区文化体育和旅游局车辆维修保养服务直接选定采购合同","notice_type":"合同公告",
       "industry":"后勤服务","region":"福建省福州市马尾区","buyer":"福州市马尾区文化体育和旅游局","priority_tag":"NO"})

s(227,{"title":"南平市建阳区文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省南平市建阳区","buyer":"南平市建阳区文化体育和旅游局","priority_tag":"NO"})

s(229,{"title":"泉州五中体育一条龙与体育课程引进高水平教育团队服务采购结果公告","notice_type":"结果公告",
       "industry":"体育教育","region":"福建省泉州市","buyer":"福建省泉州第五中学","priority_tag":"NO"})

s(231,{"title":"福建省奥林匹克体育中心食堂食材配送服务采购更正公告","notice_type":"更正公告",
       "industry":"后勤服务","region":"福建省福州市鼓楼区","buyer":"福建省奥林匹克体育中心","priority_tag":"NO"})

s(233,{"title":"2026福清市少年儿童业余体育学校食材采购项目结果公告","notice_type":"结果公告",
       "industry":"后勤服务","region":"福建省福州市福清市","buyer":"福清市少年儿童业余体育学校","priority_tag":"NO"})

s(235,{"title":"福建省龙岩体育运动学校2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省龙岩市","buyer":"福建省龙岩体育运动学校","priority_tag":"NO"})

s(238,{"title":"福州市体育局2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省福州市","buyer":"福州市体育局","priority_tag":"NO"})

s(240,{"title":"闽清县文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省福州市闽清县","buyer":"闽清县文化体育和旅游局","priority_tag":"NO"})

s(242,{"title":"邵武市文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省南平市邵武市","buyer":"邵武市文化体育和旅游局","priority_tag":"NO"})

s(244,{"title":"厦门市海沧区北附学校体育中心分校物业服务合同公告","notice_type":"合同公告",
       "industry":"物业管理","region":"福建省厦门市海沧区","buyer":"厦门市海沧区北附学校体育中心分校","priority_tag":"NO"})

s(245,{"title":"厦门市海沧区北附学校体育中心分校保安服务合同公告","notice_type":"合同公告",
       "industry":"保安服务","region":"福建省厦门市海沧区","buyer":"厦门市海沧区北附学校体育中心分校","priority_tag":"NO"})

s(247,{"title":"福建省泉州体育运动学校2025年12月-2026年1月采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省泉州市","buyer":"福建省泉州体育运动学校","priority_tag":"NO"})

s(249,{"title":"福建省泉州体育运动学校2026年5月-6月采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省泉州市","buyer":"福建省泉州体育运动学校","priority_tag":"NO"})

s(251,{"title":"长汀县文化体育和旅游局2026年5月-7月采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省龙岩市长汀县","buyer":"长汀县文化体育和旅游局","priority_tag":"NO"})

s(253,{"title":"莆田市体育局2026年5月-7月采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省莆田市","buyer":"莆田市体育局","priority_tag":"NO"})

# ⭐ [255] 海峡两岸体育嘉年华开幕式磋商
s(255,{"title":"2026海峡两岸体育嘉年华开幕式竞争性磋商公告","notice_type":"竞争性磋商",
       "industry":"体育赛事","region":"福建省厦门市",
       "budget_amount":"189.66万元",
       "submission_deadline":"2026-06-09 13:00:00",
       "eligibility":"满足政府采购法二十二条；信用查询要求；财务报告要求",
       "scope_of_work":"开幕式舞台搭建、氛围宣传、嘉宾接待、现场协调",
       "buyer":"厦门市体育局",
       "priority_tag":"YES","priority_reason":"体育赛事运营-海峡两岸体育嘉年华开幕式"})

total = conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
extracted = conn.execute("SELECT COUNT(*) FROM extracted").fetchone()[0]
priority = conn.execute("SELECT COUNT(*) FROM extracted WHERE json_extract(data_json, '$.priority_tag') = 'YES'").fetchone()[0]
print(f"\n{'='*50}")
print(f"🎉 全部提取完成！")
print(f"{'='*50}")
print(f"  总记录数: {total}")
print(f"  已提取:   {extracted}")
print(f"  重点项目: {priority}")
print(f"\n📋 所有重点项目:")
rows = conn.execute("""SELECT p.id, p.title, json_extract(e.data_json, '$.priority_reason'),
    json_extract(e.data_json, '$.budget_amount') FROM pages p JOIN extracted e ON p.id=e.page_id
    WHERE json_extract(e.data_json, '$.priority_tag')='YES' ORDER BY p.id""").fetchall()
for pid, title, reason, budget in rows:
    budget_s = budget or "未公开"
    print(f"  ★ [{pid:>3}] {title[:55]:55s} {budget_s:12s} {reason}")
conn.close()
