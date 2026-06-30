# -*- coding: utf-8 -*-
"""写入第6批 (IDs 57-76)"""
import sqlite3, json

db = r'C:\Users\cc\hermes-sports-bidding\llm_bidding.db'
conn = sqlite3.connect(db)
B = {"source":"福建省政府采购网","publish_date":"2026-06-29"}
E = {"doc_deadline":None,"qa_deadline":None,"submission_deadline":None,"ceiling_price":None,
     "bid_bond":None,"eligibility":None,"agency":None,"contact":None,"amendment":None,
     "winner":None,"winning_price":None,"panelists":None,"priority_reason":None}
def s(pid, d):
    d = {**B,**E,**d}; d['url'] = conn.execute("SELECT url FROM pages WHERE id=?",(pid,)).fetchone()[0]
    conn.execute("INSERT OR REPLACE INTO extracted (page_id, data_json) VALUES (?, ?)",(pid,json.dumps(d,ensure_ascii=False)))
    conn.execute("UPDATE pages SET status = 'extracted' WHERE id = ?",(pid,)); conn.commit()

s(57,{"title":"福州市鼓楼区文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
      "industry":"其他","region":"福建省福州市鼓楼区","buyer":"福州市鼓楼区文化体育和旅游局","priority_tag":"NO"})

s(58,{"title":"诏安县文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
      "industry":"其他","region":"福建省漳州市诏安县","buyer":"诏安县文化体育和旅游局","priority_tag":"NO"})

# ⭐ [59] 省运会参赛器材及比赛专用服
s(59,{"title":"三明市少年儿童业余体育学校省运会参赛器材及比赛专用服经费政府采购合同公告",
      "notice_type":"合同公告","industry":"体育赛事","region":"福建省三明市",
      "budget_amount":"7.86万元",
      "scope_of_work":"省运会参赛器材及比赛专用服经费",
      "buyer":"三明市少年儿童业余体育学校","winner":"三明苏闽体育器材有限公司",
      "winning_price":"78,598.00元",
      "priority_tag":"YES","priority_reason":"体育赛事设备-省运会参赛器材及比赛专用服装"})

# ⭐ [60] 世界杯竞猜达人活动
s(60,{"title":"2026年世界杯竞猜达人活动采购项目政府采购合同公告","notice_type":"合同公告",
      "industry":"体育赛事","region":"福建省福州市",
      "scope_of_work":"2026年世界杯竞猜达人活动组织",
      "buyer":"福建省体育彩票管理中心",
      "priority_tag":"YES","priority_reason":"体育赛事-2026年世界杯竞猜达人活动"})

s(61,{"title":"漳州市长泰区文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
      "industry":"其他","region":"福建省漳州市长泰区","buyer":"漳州市长泰区文化体育和旅游局","priority_tag":"NO"})

s(62,{"title":"福建省泉州体育运动学校食堂委托类服务结果公告","notice_type":"结果公告",
      "industry":"后勤服务","region":"福建省泉州市","buyer":"福建省泉州体育运动学校","priority_tag":"NO"})

# ⭐ [63] 第十八届省运会外办项目
s(63,{"title":"三明市体育局第十八届省运会外办项目(二次)政府采购合同公告","notice_type":"合同公告",
      "industry":"体育赛事","region":"福建省三明市",
      "scope_of_work":"第十八届省运会外办项目",
      "buyer":"三明市体育局",
      "priority_tag":"YES","priority_reason":"体育赛事运营-省级运动会外办项目"})

s(64,{"title":"三明市体育局2026年度采购意向","notice_type":"采购意向",
      "industry":"其他","region":"福建省三明市","buyer":"三明市体育局","priority_tag":"NO"})

s(65,{"title":"泉州市体育局2026年度采购意向","notice_type":"采购意向",
      "industry":"其他","region":"福建省泉州市","buyer":"泉州市体育局","priority_tag":"NO"})

# ⭐ [66] 鼓岭缘棒球赛结果公告
s(66,{"title":"2026年鼓岭缘中美青少年棒球友谊赛暨体育交流周项目结果公告","notice_type":"结果公告",
      "industry":"体育赛事","region":"福建省福州市",
      "budget_amount":"925.23万元",
      "scope_of_work":"中美青少年棒球友谊赛活动执行",
      "buyer":"福州市人民政府外事办公室","winner":"福州广播电视台(联合体)",
      "winning_price":"9,252,344.80元",
      "priority_tag":"YES","priority_reason":"体育赛事运营-中美青少年棒球友谊赛"})

s(67,{"title":"福建省泉州体育运动学校A4黑白打印机直接订购采购合同","notice_type":"合同公告",
      "industry":"办公设备","region":"福建省泉州市","buyer":"福建省泉州体育运动学校","priority_tag":"NO"})

s(68,{"title":"双十中学枋湖校区多功能学术交流厅、教学楼及体育馆部分修缮采购更正公告","notice_type":"更正公告",
      "industry":"建筑","region":"福建省厦门市湖里区","buyer":"福建省厦门双十中学",
      "amendment":"采购更正","priority_tag":"NO"})

s(69,{"title":"福州市体育运动学校2026-2027年度食堂食材配送服务政府采购合同公告","notice_type":"合同公告",
      "industry":"后勤服务","region":"福建省福州市","buyer":"福州市体育运动学校","priority_tag":"NO"})

# ⭐ [70] 厦门体校训练比赛器材
s(70,{"title":"厦门市体育运动学校运动队训练比赛器材政府采购合同公告","notice_type":"合同公告",
      "industry":"体育赛事","region":"福建省厦门市",
      "scope_of_work":"运动队训练比赛器材采购",
      "buyer":"厦门市体育运动学校",
      "priority_tag":"YES","priority_reason":"体育赛事设备-训练比赛器材采购"})

s(71,{"title":"仙游县体育运动学校2026年度采购意向","notice_type":"采购意向",
      "industry":"其他","region":"福建省莆田市仙游县","buyer":"仙游县体育运动学校","priority_tag":"NO"})

s(72,{"title":"三明市体育局省运会和省老健会市筹委会集中驻会办公设施及办公家具采购合同公告","notice_type":"合同公告",
      "industry":"办公家具","region":"福建省三明市","buyer":"三明市体育局","priority_tag":"NO"})

# ⭐ [73, 74, 75] 厦门体校训练比赛器材（多批次）
for pid in [73,74,75]:
    s(pid,{"title":"厦门市体育运动学校运动队训练比赛器材政府采购合同公告","notice_type":"合同公告",
           "industry":"体育赛事","region":"福建省厦门市",
           "scope_of_work":"运动队训练比赛器材采购",
           "buyer":"厦门市体育运动学校",
           "priority_tag":"YES","priority_reason":"体育赛事设备-训练比赛器材采购"})

s(76,{"title":"龙岩市永定区少年儿童体育学校2026年度采购意向","notice_type":"采购意向",
      "industry":"其他","region":"福建省龙岩市永定区","buyer":"龙岩市永定区少年儿童体育学校","priority_tag":"NO"})

rem = conn.execute("SELECT COUNT(*) FROM pages WHERE status='raw'").fetchone()[0]
print(f"第6批完成！已处理: 76条  剩余: {rem} 条")
conn.close()
