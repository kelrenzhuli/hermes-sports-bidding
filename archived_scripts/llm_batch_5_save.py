# -*- coding: utf-8 -*-
"""写入第5批 (IDs 37-56)"""
import sqlite3, json

db = r'C:\Users\cc\hermes-sports-bidding\llm_bidding.db'
conn = sqlite3.connect(db)
B = {"source":"福建省政府采购网","publish_date":"2026-06-29"}
E = {"doc_deadline":None,"qa_deadline":None,"submission_deadline":None,"ceiling_price":None,
     "bid_bond":None,"eligibility":None,"agency":None,"contact":None,"amendment":None,
     "winner":None,"winning_price":None,"panelists":None,"priority_reason":None}
def s(pid, d):
    d = {**B,**E,**d}
    d['url'] = conn.execute("SELECT url FROM pages WHERE id=?", (pid,)).fetchone()[0]
    conn.execute("INSERT OR REPLACE INTO extracted (page_id, data_json) VALUES (?, ?)",
                 (pid, json.dumps(d, ensure_ascii=False)))
    conn.execute("UPDATE pages SET status = 'extracted' WHERE id = ?", (pid,))
    conn.commit()

s(37, {"title":"福建省泉州体育运动学校物业管理服务及准军事化管理服务结果公告",
       "notice_type":"结果公告","industry":"物业管理","region":"福建省泉州市",
       "buyer":"福建省泉州体育运动学校","priority_tag":"NO"})

s(38, {"title":"福州市仓山区文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
       "industry":"体育设施","region":"福建省福州市仓山区",
       "scope_of_work":"2026年仓山区全民健身工程器材及球场提升改造项目",
       "buyer":"福州市仓山区文化体育和旅游局","priority_tag":"NO"})

s(39, {"title":"云霄县文化体育和旅游局何以云霄系列图书3本政府采购合同公告","notice_type":"合同公告",
       "industry":"文化出版","region":"福建省漳州市云霄县",
       "scope_of_work":"何以云霄系列图书3本","buyer":"云霄县文化体育和旅游局","priority_tag":"NO"})

s(40, {"title":"2026年福建省体育场地统计调查服务结果公告","notice_type":"结果公告",
       "industry":"体育服务","region":"福建省",
       "scope_of_work":"2026年福建省体育场地统计调查服务",
       "buyer":"福建省体育局","priority_tag":"NO"})

s(41, {"title":"诏安县文化体育和旅游局多功能一体机直接选定采购合同","notice_type":"合同公告",
       "industry":"办公设备","region":"福建省漳州市诏安县",
       "buyer":"诏安县文化体育和旅游局","priority_tag":"NO"})

s(42, {"title":"福建省泉州体育运动学校食堂委托类服务(二次)竞争性磋商公告","notice_type":"竞争性磋商",
       "industry":"后勤服务","region":"福建省泉州市",
       "submission_deadline":"2026-06-29 09:30:00",
       "eligibility":"满足政府采购法二十二条；专门面向中小企业",
       "scope_of_work":"食堂委托类服务","buyer":"福建省泉州体育运动学校","bid_bond":"0元","priority_tag":"NO"})

s(43, {"title":"福建省社会体育指导中心2026年度采购意向（公务用车保险）","notice_type":"采购意向",
       "industry":"保险服务","region":"福建省",
       "scope_of_work":"2026年社体中心公务用车保险",
       "buyer":"福建省社会体育指导中心","priority_tag":"NO"})

s(44, {"title":"福建省社会体育指导中心2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省",
       "buyer":"福建省社会体育指导中心","priority_tag":"NO"})

s(45, {"title":"竹寺文化体育公园建设项目竞争性磋商公告","notice_type":"竞争性磋商",
       "industry":"市政工程","region":"福建省",
       "submission_deadline":"2026-06-29 09:00:00","bid_bond":"0元",
       "eligibility":"满足政府采购法二十二条；专门面向中小企业",
       "scope_of_work":"竹寺文化体育公园建设项目","priority_tag":"NO"})

s(46, {"title":"福建省奥林匹克体育中心食堂食材配送服务结果公告","notice_type":"结果公告",
       "industry":"后勤服务","region":"福建省福州市鼓楼区",
       "buyer":"福建省奥林匹克体育中心","priority_tag":"NO"})

s(47, {"title":"鼓楼区青少年校外体育活动中心2026年度采购意向","notice_type":"采购意向",
       "industry":"办公设备","region":"福建省福州市鼓楼区",
       "scope_of_work":"2台5P柜机（空调）","buyer":"鼓楼区青少年校外体育活动中心","priority_tag":"NO"})

s(48, {"title":"莆田市体育局2026年度采购意向","notice_type":"采购意向",
       "industry":"办公用品","region":"福建省莆田市",
       "scope_of_work":"复印纸采购","buyer":"莆田市体育局","priority_tag":"NO"})

# ⭐ [49] 世界杯线下观赛
s(49, {"title":"2026年世界杯福建体彩线下观赛及品牌宣传推广项目政府采购合同公告","notice_type":"合同公告",
       "industry":"体育赛事","region":"福建省福州市鼓楼区",
       "budget_amount":"187.00万元",
       "scope_of_work":"2026年世界杯福建体彩线下观赛活动组织及品牌宣传推广",
       "buyer":"福建省体育彩票管理中心","winner":"福建嘉应文化传播有限公司",
       "winning_price":"1,870,000.00元","contact":"0591-87713401",
       "priority_tag":"YES","priority_reason":"体育赛事-2026年世界杯线下观赛及品牌推广"})

s(50, {"title":"泉州五中体育一条龙与体育课程引进高水平教育团队服务采购合同公告","notice_type":"合同公告",
       "industry":"体育教育","region":"福建省泉州市",
       "scope_of_work":"体育一条龙与体育课程引进高水平教育团队服务",
       "buyer":"福建省泉州第五中学","priority_tag":"NO"})

s(51, {"title":"福建省泉州体育运动学校运动员公寓及校园配套修缮终止公告","notice_type":"终止公告",
       "industry":"建筑","region":"福建省泉州市",
       "buyer":"福建省泉州体育运动学校","amendment":"采购终止","priority_tag":"NO"})

s(52, {"title":"福建省奥林匹克体育中心台式计算机直接选定采购合同","notice_type":"合同公告",
       "industry":"办公设备","region":"福建省福州市鼓楼区",
       "buyer":"福建省奥林匹克体育中心","priority_tag":"NO"})

s(53, {"title":"福建省奥林匹克体育中心空调机直接选定采购合同","notice_type":"合同公告",
       "industry":"办公设备","region":"福建省福州市鼓楼区",
       "buyer":"福建省奥林匹克体育中心","priority_tag":"NO"})

s(54, {"title":"福建省奥林匹克体育中心2026年度采购意向","notice_type":"采购意向",
       "industry":"其他","region":"福建省福州市鼓楼区",
       "buyer":"福建省奥林匹克体育中心","priority_tag":"NO"})

s(55, {"title":"福建体育职业技术学院2026年度采购意向","notice_type":"采购意向",
       "industry":"办公设备","region":"福建省",
       "scope_of_work":"多功能一体机采购",
       "buyer":"福建体育职业技术学院","priority_tag":"NO"})

s(56, {"title":"福建省南安市体育学校2026年度采购意向","notice_type":"采购意向",
       "industry":"办公设备","region":"福建省泉州市南安市",
       "scope_of_work":"空调机采购",
       "buyer":"福建省南安市体育学校","priority_tag":"NO"})

rem = conn.execute("SELECT COUNT(*) FROM pages WHERE status='raw'").fetchone()[0]
print(f"第5批完成！已处理: 56条  剩余: {rem} 条")
conn.close()
