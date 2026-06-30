# -*- coding: utf-8 -*-
"""写入第9批 (IDs 160-207)"""
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

s(160,{"title":"泉州市妇幼保健院物理治疗、康复及体育治疗仪器设备一批公开招标招标公告",
       "notice_type":"公开招标","industry":"医疗设备","region":"福建省泉州市",
       "submission_deadline":"2026-07-01 09:00:00",
       "scope_of_work":"物理治疗、康复及体育治疗仪器设备一批","buyer":"泉州市妇幼保健院","priority_tag":"NO"})

s(162,{"title":"福建省体育产业发展服务中心2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省","buyer":"福建省体育产业发展服务中心","priority_tag":"NO"})

s(164,{"title":"福建省体育彩票管理中心热敏纸采购项目合同公告","notice_type":"合同公告",
       "industry":"办公用品","region":"福建省福州市","buyer":"福建省体育彩票管理中心","priority_tag":"NO"})

s(165,{"title":"龙岩市永定区文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省龙岩市永定区","buyer":"龙岩市永定区文化体育和旅游局","priority_tag":"NO"})

s(167,{"title":"龙岩市体育局2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省龙岩市","buyer":"龙岩市体育局","priority_tag":"NO"})

s(169,{"title":"安溪县少年业余体育学校2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省泉州市安溪县","buyer":"安溪县少年业余体育学校","priority_tag":"NO"})

s(171,{"title":"邵武市樵川体育公园-滨河景观改造提升项目合同公告","notice_type":"合同公告",
       "industry":"市政工程","region":"福建省南平市邵武市","buyer":"邵武市住房和城乡建设局","priority_tag":"NO"})

s(173,{"title":"安溪县少年业余体育学校2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省泉州市安溪县","buyer":"安溪县少年业余体育学校","priority_tag":"NO"})

s(175,{"title":"海峡两岸（龙岩）体育交流基地管理中心2026年度采购意向","notice_type":"采购意向",
       "industry":"体育服务","region":"福建省龙岩市","buyer":"海峡两岸（龙岩）体育交流基地管理中心",
       "priority_tag":"NO"})

# ⭐ [178] 省运会代表团服装
s(178,{"title":"厦门市体育局2026年省运会代表团服装政府采购合同公告","notice_type":"合同公告",
       "industry":"体育赛事","region":"福建省厦门市思明区",
       "budget_amount":"172.98万元",
       "scope_of_work":"2026年省运会代表团服装采购",
       "buyer":"厦门市体育局","winner":"广州胜威体育产业有限公司",
       "winning_price":"1,729,750.00元",
       "priority_tag":"YES","priority_reason":"体育赛事设备-省运会代表团服装采购"})

s(180,{"title":"龙岩市永定区文化体育和旅游局复印纸直接选定采购合同","notice_type":"合同公告",
       "industry":"办公用品","region":"福建省龙岩市永定区","buyer":"龙岩市永定区文化体育和旅游局","priority_tag":"NO"})

s(182,{"title":"龙岩市永定区少年儿童体育学校2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省龙岩市永定区","buyer":"龙岩市永定区少年儿童体育学校","priority_tag":"NO"})

s(184,{"title":"惠安县青少年业余体育学校2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省泉州市惠安县","buyer":"惠安县青少年业余体育学校","priority_tag":"NO"})

# ⭐ [185] 射击比赛及训练器材
s(185,{"title":"三明市少年儿童业余体育学校各项目组采购比赛及训练器材-射击设备合同公告",
       "notice_type":"合同公告","industry":"体育赛事","region":"福建省三明市",
       "scope_of_work":"比赛及训练器材-射击设备采购",
       "buyer":"三明市少年儿童业余体育学校",
       "priority_tag":"YES","priority_reason":"体育赛事设备-射击比赛训练器材采购"})

for pid in [187,189]:
    s(pid,{"title":f"惠安县青少年业余体育学校2026年度采购意向","notice_type":"采购意向",
           "industry":"其他","region":"福建省泉州市惠安县","buyer":"惠安县青少年业余体育学校","priority_tag":"NO"})

s(191,{"title":"龙岩市体育局2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省龙岩市","buyer":"龙岩市体育局","priority_tag":"NO"})

s(193,{"title":"南平市少年儿童重点业余体育学校2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省南平市","buyer":"南平市少年儿童重点业余体育学校","priority_tag":"NO"})

s(195,{"title":"福州市体育局便携式计算机直接订购采购合同","notice_type":"合同公告",
       "industry":"办公设备","region":"福建省福州市","buyer":"福州市体育局","priority_tag":"NO"})

s(198,{"title":"龙岩市永定区文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省龙岩市永定区","buyer":"龙岩市永定区文化体育和旅游局","priority_tag":"NO"})

s(200,{"title":"漳浦县文化体育和旅游局复印纸直接选定采购合同","notice_type":"合同公告",
       "industry":"办公用品","region":"福建省漳州市漳浦县","buyer":"漳浦县文化体育和旅游局","priority_tag":"NO"})

s(202,{"title":"福州市体育局台式计算机直接选定采购合同","notice_type":"合同公告",
       "industry":"办公设备","region":"福建省福州市","buyer":"福州市体育局","priority_tag":"NO"})

s(204,{"title":"顺昌县文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省南平市顺昌县","buyer":"顺昌县文化体育和旅游局","priority_tag":"NO"})

s(205,{"title":"建瓯市文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省南平市建瓯市","buyer":"建瓯市文化体育和旅游局","priority_tag":"NO"})

s(207,{"title":"福建省龙岩体育运动学校2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省龙岩市","buyer":"福建省龙岩体育运动学校","priority_tag":"NO"})

rem = conn.execute("SELECT COUNT(*) FROM pages WHERE status='raw'").fetchone()[0]
print(f"第9批完成！已处理: 146条  剩余: {rem} 条")
conn.close()
