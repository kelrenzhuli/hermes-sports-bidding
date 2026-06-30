# -*- coding: utf-8 -*-
"""写入第7批 (IDs 77-107)"""
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

s(77,{"title":"福建省莆田体育运动学校市皮划赛艇基地临时过渡场所公开租赁项目公开招标招标公告",
      "notice_type":"公开招标","industry":"体育设施","region":"福建省莆田市",
      "submission_deadline":"2026-07-06 08:30:00",
      "scope_of_work":"市皮划赛艇基地临时过渡场所公开租赁","buyer":"福建省莆田体育运动学校",
      "priority_tag":"NO"}) # 场地租赁，非赛事

for pid in [78,79,80]:
    s(pid,{"title":f"三明市体育局2026年度采购意向","notice_type":"采购意向",
           "industry":"其他","region":"福建省三明市","buyer":"三明市体育局","priority_tag":"NO"})

s(81,{"title":"福建省宁德市少年体育运动学校2026年度采购意向","notice_type":"采购意向",
      "industry":"其他","region":"福建省宁德市","buyer":"福建省宁德市少年体育运动学校","priority_tag":"NO"})

s(82,{"title":"福建省体育产业发展服务中心复印纸直接选定采购合同","notice_type":"合同公告",
      "industry":"办公用品","region":"福建省","buyer":"福建省体育产业发展服务中心","priority_tag":"NO"})

s(83,{"title":"南平市体育局2026年度采购意向","notice_type":"采购意向",
      "industry":"其他","region":"福建省南平市","buyer":"南平市体育局","priority_tag":"NO"})

s(84,{"title":"福建省体育局体育产业发展服务政府采购合同公告","notice_type":"合同公告",
      "industry":"体育服务","region":"福建省","buyer":"福建省体育局","priority_tag":"NO"})

s(85,{"title":"晋江市少年儿童业余体育学校2026年食堂食材配送服务采购合同公告","notice_type":"合同公告",
      "industry":"后勤服务","region":"福建省泉州市晋江市","buyer":"晋江市少年儿童业余体育学校","priority_tag":"NO"})

# ⭐ [87] 莆田体校训练比赛器材服装采购公开招标
s(87,{"title":"福建省莆田体育运动学校2026年训练比赛器材、服装采购公开招标招标公告",
      "notice_type":"公开招标","industry":"体育赛事","region":"福建省莆田市",
      "submission_deadline":"2026-07-03 08:30:00",
      "budget_amount":"未公开",
      "eligibility":"满足政府采购法二十二条；专门面向中小企业",
      "scope_of_work":"2026年训练比赛器材、服装采购","buyer":"福建省莆田体育运动学校",
      "priority_tag":"YES","priority_reason":"体育赛事设备-训练比赛器材及服装采购"})

s(89,{"title":"福清市少年儿童业余体育学校食材采购项目合同公告","notice_type":"合同公告",
      "industry":"后勤服务","region":"福建省福州市福清市","buyer":"福清市少年儿童业余体育学校","priority_tag":"NO"})

s(91,{"title":"南平市建阳区文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
      "industry":"其他","region":"福建省南平市建阳区","buyer":"南平市建阳区文化体育和旅游局","priority_tag":"NO"})

s(93,{"title":"北大附中莆田学校体育馆、舞蹈、音乐教室设施设备(二次)竞争性磋商公告",
      "notice_type":"竞争性磋商","industry":"体育设施","region":"福建省莆田市",
      "submission_deadline":"2026-06-24 08:30:00",
      "scope_of_work":"体育馆、舞蹈、音乐教室设施设备采购","buyer":"北大附中莆田学校",
      "priority_tag":"NO"}) # 学校场馆设备，非赛事

s(95,{"title":"福州市体育局复印纸直接选定采购合同","notice_type":"合同公告",
      "industry":"办公用品","region":"福建省福州市","buyer":"福州市体育局","priority_tag":"NO"})

s(98,{"title":"霞浦县老年人体育协会2026年度采购意向","notice_type":"采购意向",
      "industry":"其他","region":"福建省宁德市霞浦县","buyer":"霞浦县老年人体育协会","priority_tag":"NO"})

s(100,{"title":"漳州市重点少年儿童业余体育学校2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省漳州市","buyer":"漳州市重点少年儿童业余体育学校","priority_tag":"NO"})

s(102,{"title":"闽侯县业余少年体育学校2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省福州市闽侯县","buyer":"闽侯县业余少年体育学校","priority_tag":"NO"})

# ⭐ [104] 海峡两岸体育嘉年华开幕式
s(104,{"title":"2026海峡两岸体育嘉年华开幕式政府采购合同公告","notice_type":"合同公告",
       "industry":"体育赛事","region":"福建省厦门市思明区",
       "budget_amount":"189.66万元",
       "scope_of_work":"开幕式舞台搭建、氛围宣传、嘉宾接待、现场协调",
       "buyer":"厦门市体育局","winner":"海西晨报社","winning_price":"1,896,600.00元",
       "contact":"0592-5121277",
       "priority_tag":"YES","priority_reason":"体育赛事运营-海峡两岸体育嘉年华开幕式"})

s(105,{"title":"武夷山市文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省南平市武夷山市","buyer":"武夷山市文化体育和旅游局","priority_tag":"NO"})

s(107,{"title":"晋江市少年儿童业余体育学校后勤保障服务项目合同公告","notice_type":"合同公告",
       "industry":"后勤服务","region":"福建省泉州市晋江市","buyer":"晋江市少年儿童业余体育学校","priority_tag":"NO"})

rem = conn.execute("SELECT COUNT(*) FROM pages WHERE status='raw'").fetchone()[0]
print(f"第7批完成！已处理: 96条  剩余: {rem} 条")
conn.close()
