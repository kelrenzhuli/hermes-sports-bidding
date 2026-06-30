# -*- coding: utf-8 -*-
"""写入第8批 (25条)"""
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

s(109,{"title":"平潭综合实验区旅游与文化体育局2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福州市平潭综合实验区","buyer":"平潭综合实验区旅游与文化体育局","priority_tag":"NO"})

s(111,{"title":"惠安县青少年业余体育学校食堂食材配送服务采购竞争性磋商公告","notice_type":"竞争性磋商",
       "industry":"后勤服务","region":"福建省泉州市惠安县",
       "submission_deadline":"2026-06-23 09:30:00",
       "buyer":"惠安县青少年业余体育学校","priority_tag":"NO"})

s(113,{"title":"北大附中莆田学校体育馆、舞蹈、音乐教室设施设备结果公告","notice_type":"结果公告",
       "industry":"体育设施","region":"福建省莆田市","buyer":"北大附中莆田学校","priority_tag":"NO"})

s(115,{"title":"三明市体育局复印纸直接选定采购合同","notice_type":"合同公告",
       "industry":"办公用品","region":"福建省三明市","buyer":"三明市体育局","priority_tag":"NO"})

s(118,{"title":"福建省奥林匹克体育中心车辆维修保养服务直接选定采购合同","notice_type":"合同公告",
       "industry":"后勤服务","region":"福建省福州市鼓楼区","buyer":"福建省奥林匹克体育中心","priority_tag":"NO"})

s(120,{"title":"福建省龙岩体育运动学校复印纸直接选定采购合同","notice_type":"合同公告",
       "industry":"办公用品","region":"福建省龙岩市","buyer":"福建省龙岩体育运动学校","priority_tag":"NO"})

s(122,{"title":"福建省龙岩体育运动学校台式计算机直接选定采购合同","notice_type":"合同公告",
       "industry":"办公设备","region":"福建省龙岩市","buyer":"福建省龙岩体育运动学校","priority_tag":"NO"})

s(124,{"title":"福建省奥林匹克体育中心2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省福州市鼓楼区","buyer":"福建省奥林匹克体育中心","priority_tag":"NO"})

# ⭐ [125] 海峡两岸体育嘉年华开幕式结果公告
s(125,{"title":"2026海峡两岸体育嘉年华开幕式结果公告","notice_type":"结果公告",
       "industry":"体育赛事","region":"福建省厦门市",
       "budget_amount":"189.66万元",
       "buyer":"厦门市体育局","winner":"海西晨报社","winning_price":"1,896,600.00元",
       "priority_tag":"YES","priority_reason":"体育赛事运营-海峡两岸体育嘉年华开幕式"})

s(127,{"title":"双十中学枋湖校区多功能学术交流厅、教学楼及体育馆部分修缮竞争性磋商公告",
       "notice_type":"竞争性磋商","industry":"建筑","region":"福建省厦门市湖里区",
       "submission_deadline":"2026-06-22 13:30:00","bid_bond":"0元",
       "buyer":"福建省厦门双十中学","priority_tag":"NO"})

s(129,{"title":"平潭综合实验区旅游与文化体育局2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福州市平潭综合实验区","buyer":"平潭综合实验区旅游与文化体育局","priority_tag":"NO"})

s(131,{"title":"福建省宁德市少年体育运动学校2026年食堂食材采购及配送服务项目合同公告","notice_type":"合同公告",
       "industry":"后勤服务","region":"福建省宁德市","buyer":"福建省宁德市少年体育运动学校","priority_tag":"NO"})

s(133,{"title":"龙岩市永定区文化体育和旅游局空调机直接选定采购合同","notice_type":"合同公告",
       "industry":"办公设备","region":"福建省龙岩市永定区","buyer":"龙岩市永定区文化体育和旅游局","priority_tag":"NO"})

s(135,{"title":"漳州市芗城区文化体育和旅游局复印纸直接选定采购合同","notice_type":"合同公告",
       "industry":"办公用品","region":"福建省漳州市芗城区","buyer":"漳州市芗城区文化体育和旅游局","priority_tag":"NO"})

s(138,{"title":"南平市建阳区文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省南平市建阳区","buyer":"南平市建阳区文化体育和旅游局","priority_tag":"NO"})

s(140,{"title":"南靖县文化体育和旅游局空调机直接选定采购合同","notice_type":"合同公告",
       "industry":"办公设备","region":"福建省漳州市南靖县","buyer":"南靖县文化体育和旅游局","priority_tag":"NO"})

s(142,{"title":"南平市建阳区文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省南平市建阳区","buyer":"南平市建阳区文化体育和旅游局","priority_tag":"NO"})

# ⭐ [144] 省运会奖牌奖状奖杯采购
s(144,{"title":"三明市体育局第十八届省运会和第十二届省老健会奖牌奖状奖杯牌匾秩序册成绩册采购合同公告",
       "notice_type":"合同公告","industry":"体育赛事","region":"福建省三明市",
       "scope_of_work":"省运会奖牌、奖状、奖杯、牌匾、秩序册、成绩册采购",
       "buyer":"三明市体育局",
       "priority_tag":"YES","priority_reason":"体育赛事设备-省运会奖牌奖杯等赛事物资"})

s(145,{"title":"建瓯市文化体育和旅游局建瓯市文旅小红书宣传推广项目合同公告","notice_type":"合同公告",
       "industry":"文化媒体","region":"福建省南平市建瓯市","buyer":"建瓯市文化体育和旅游局","priority_tag":"NO"})

s(147,{"title":"福建省泉州体育运动学校运动员公寓及校园配套修缮采购更正公告","notice_type":"更正公告",
       "industry":"建筑","region":"福建省泉州市","buyer":"福建省泉州体育运动学校","priority_tag":"NO"})

s(149,{"title":"惠安县文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省泉州市惠安县","buyer":"惠安县文化体育和旅游局","priority_tag":"NO"})

s(151,{"title":"福建省体育科学研究所财产保险服务直接选定采购合同","notice_type":"合同公告",
       "industry":"保险服务","region":"福建省","buyer":"福建省体育科学研究所","priority_tag":"NO"})

s(153,{"title":"福建省泉州体育运动学校运动员公寓及校园配套修缮竞争性磋商公告","notice_type":"竞争性磋商",
       "industry":"建筑","region":"福建省泉州市",
       "submission_deadline":"2026-06-18 09:00:00","bid_bond":"0元",
       "buyer":"福建省泉州体育运动学校","priority_tag":"NO"})

s(155,{"title":"福建省泉州体育运动学校物业管理服务及准军事化管理服务竞争性磋商公告","notice_type":"竞争性磋商",
       "industry":"物业管理","region":"福建省泉州市",
       "submission_deadline":"2026-06-22 09:00:00","bid_bond":"0元",
       "buyer":"福建省泉州体育运动学校","priority_tag":"NO"})

s(158,{"title":"福建省泉州体育运动学校食堂委托类服务竞争性磋商公告","notice_type":"竞争性磋商",
       "industry":"后勤服务","region":"福建省泉州市",
       "submission_deadline":"2026-06-17 09:30:00","bid_bond":"0元",
       "buyer":"福建省泉州体育运动学校","priority_tag":"NO"})

rem = conn.execute("SELECT COUNT(*) FROM pages WHERE status='raw'").fetchone()[0]
print(f"第8批完成！已处理: 121条  剩余: {rem} 条")
conn.close()
