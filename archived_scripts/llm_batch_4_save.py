# -*- coding: utf-8 -*-
"""写入第4批 (IDs 10,18-36)"""
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

B = {"source":"福建省政府采购网","publish_date":"2026-06-29"}
E = {"doc_deadline":None,"qa_deadline":None,"submission_deadline":None,"ceiling_price":None,
     "bid_bond":None,"eligibility":None,"agency":None,"contact":None,"amendment":None,
     "winner":None,"winning_price":None,"panelists":None,"priority_reason":None}

save(10, {**B,**E,"title":"福建省冠军大使及体育精神展公益品牌体彩宣传项目结果公告","notice_type":"结果公告",
          "industry":"文化宣传","region":"福建省","budget_amount":"未公开",
          "scope_of_work":"冠军大使及体育精神展公益品牌体彩宣传","buyer":"福建省体育彩票管理中心",
          "priority_tag":"NO"})

save(18, {**B,**E,"title":"福建省奥林匹克体育中心2026年度（第11批）采购意向","notice_type":"采购意向",
          "industry":"办公设备","region":"福建省福州市鼓楼区","budget_amount":"未公开",
          "scope_of_work":"吸顶空调采购","buyer":"福建省奥林匹克体育中心","priority_tag":"NO"})

save(19, {**B,**E,"title":"福州市台江区文化体育和旅游局2026年度（第4批）采购意向","notice_type":"采购意向",
          "industry":"体育设施","region":"福建省福州市台江区","budget_amount":"未公开",
          "scope_of_work":"2026年台江区全民健身工程健身设施（网球场）采购",
          "buyer":"福州市台江区文化体育和旅游局","priority_tag":"NO"})

save(20, {**B,**E,"title":"福建省泉州体育运动学校物业管理服务及准军事化管理服务(二次)竞争性磋商公告",
          "notice_type":"竞争性磋商","industry":"物业管理","region":"福建省泉州市",
          "budget_amount":"未公开","submission_deadline":"2026-07-06 09:00:00",
          "eligibility":"满足政府采购法二十二条；专门面向中小企业",
          "scope_of_work":"物业管理及准军事化管理服务","buyer":"福建省泉州体育运动学校",
          "bid_bond":"0元","priority_tag":"NO"})

save(21, {**B,**E,"title":"罗源县文化体育和旅游局空调机直接选定采购合同","notice_type":"合同公告",
          "industry":"办公设备","region":"福建省福州市罗源县","budget_amount":"未公开",
          "scope_of_work":"空调机采购","buyer":"罗源县文化体育和旅游局","priority_tag":"NO"})

save(22, {**B,**E,"title":"北大附中莆田学校体育馆、舞蹈、音乐教室设施设备(二次)结果公告",
          "notice_type":"结果公告","industry":"体育设施","region":"福建省莆田市",
          "budget_amount":"未公开","scope_of_work":"体育馆、舞蹈、音乐教室设施设备采购",
          "buyer":"北大附中莆田学校","priority_tag":"NO"})

save(23, {**B,**E,"title":"莆田市体育训练基地小型体育公园（棒球体育公园）项目工程(二次)合同公告",
          "notice_type":"合同公告","industry":"体育设施","region":"福建省莆田市",
          "budget_amount":"160.80万元",
          "scope_of_work":"小型体育公园（棒球体育公园）项目工程","buyer":"莆田市体育训练基地",
          "winner":"江苏力帆建设有限公司","winning_price":"1,608,000.00元",
          "priority_tag":"NO"})

save(24, {**B,**E,"title":"惠安县青少年业余体育学校食堂食材配送服务采购结果公告","notice_type":"结果公告",
          "industry":"后勤服务","region":"福建省泉州市惠安县","budget_amount":"未公开",
          "scope_of_work":"食堂食材配送服务","buyer":"惠安县青少年业余体育学校",
          "priority_tag":"NO"})

save(25, {**B,**E,"title":"建瓯市文化体育和旅游局多功能一体机直接订购采购合同","notice_type":"合同公告",
          "industry":"办公设备","region":"福建省南平市建瓯市","budget_amount":"未公开",
          "scope_of_work":"多功能一体机采购","buyer":"建瓯市文化体育和旅游局","priority_tag":"NO"})

save(26, {**B,**E,"title":"邵武市樵川体育公园（二期）-铁路文化提升项目竞争性磋商公告",
          "notice_type":"竞争性磋商","industry":"市政工程","region":"福建省南平市邵武市",
          "budget_amount":"未公开","submission_deadline":"2026-07-07 08:30:00",
          "bid_bond":"11,000.00元",
          "eligibility":"满足政府采购法二十二条；专门面向中小企业",
          "scope_of_work":"樵川体育公园（二期）铁路文化提升","buyer":"邵武市文化体育和旅游局",
          "priority_tag":"NO"})

save(27, {**B,**E,"title":"双十中学枋湖校区多功能学术交流厅、教学楼及体育馆部分修缮结果公告",
          "notice_type":"结果公告","industry":"建筑","region":"福建省厦门市湖里区",
          "budget_amount":"未公开","scope_of_work":"学术交流厅、教学楼及体育馆修缮",
          "buyer":"福建省厦门双十中学","priority_tag":"NO"})

save(28, {**B,**E,"title":"南平市延平区文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
          "industry":"文化活动","region":"福建省南平市延平区","budget_amount":"未公开",
          "scope_of_work":"第十八届海峡论坛·两岸延平王郑成功文化活动",
          "buyer":"南平市延平区文化体育和旅游局","priority_tag":"NO"})

save(29, {**B,**E,"title":"平潭综合实验区旅游与文化体育局南岛语族文化学术论坛服务项目合同公告",
          "notice_type":"合同公告","industry":"文化学术","region":"福州市平潭综合实验区",
          "budget_amount":"未公开","scope_of_work":"南岛语族文化学术论坛服务",
          "buyer":"平潭综合实验区旅游与文化体育局","priority_tag":"NO"})

save(30, {**B,**E,"title":"泉州市体育局2026年度（第4批）采购意向","notice_type":"采购意向",
          "industry":"体育设施","region":"福建省泉州市","budget_amount":"未公开",
          "scope_of_work":"2026年市级全民健身场地设施建设，6座多功能足球运动场",
          "buyer":"泉州市体育局","priority_tag":"NO"})

# ⭐ [31] 平潭国际自行车赛 - 重大体育赛事！
save(31, {**B,**E,"title":"平潭综合实验区旅游与文化体育局2026年度（第6批）采购意向",
          "notice_type":"采购意向","industry":"体育赛事","region":"福州市平潭综合实验区",
          "budget_amount":"未公开",
          "scope_of_work":"2026年海洋杯中国平潭国际自行车公开赛执行、开闭幕式、宣传、后勤保障",
          "buyer":"平潭综合实验区旅游与文化体育局",
          "priority_tag":"YES","priority_reason":"体育赛事运营-国际公路自行车赛"})

save(32, {**B,**E,"title":"罗源县文化体育和旅游局2026年度采购意向","notice_type":"采购意向",
          "industry":"办公设备","region":"福建省福州市罗源县","budget_amount":"未公开",
          "scope_of_work":"空调机采购","buyer":"罗源县文化体育和旅游局","priority_tag":"NO"})

save(33, {**B,**E,"title":"福建省龙岩体育运动学校2026年度采购意向","notice_type":"采购意向",
          "industry":"后勤服务","region":"福建省龙岩市","budget_amount":"未公开",
          "scope_of_work":"车辆维修保养服务","buyer":"福建省龙岩体育运动学校","priority_tag":"NO"})

save(34, {**B,**E,"title":"福建省老年人体育工作中心财产保险服务直接选定采购合同","notice_type":"合同公告",
          "industry":"保险服务","region":"福建省","budget_amount":"未公开",
          "scope_of_work":"财产保险服务","buyer":"福建省老年人体育工作中心","priority_tag":"NO"})

save(35, {**B,**E,"title":"福建省泉州体育运动学校运动员公寓及校园配套修缮(二次)竞争性磋商公告",
          "notice_type":"竞争性磋商","industry":"建筑","region":"福建省泉州市",
          "budget_amount":"未公开","submission_deadline":"2026-07-03 09:00:00",
          "eligibility":"满足政府采购法二十二条；专门面向中小企业",
          "scope_of_work":"运动员公寓及校园配套修缮","buyer":"福建省泉州体育运动学校",
          "bid_bond":"0元","priority_tag":"NO"})

save(36, {**B,**E,"title":"不锈钢特色小镇体育中心及科教用地土壤污染状况调查服务采购竞争性磋商公告",
          "notice_type":"竞争性磋商","industry":"环保服务","region":"福建省",
          "budget_amount":"未公开","submission_deadline":"2026-07-03 08:30:00",
          "eligibility":"满足政府采购法二十二条；专门面向中小企业",
          "scope_of_work":"体育中心及科教用地土壤污染状况第二阶段调查","buyer":"采购人",
          "bid_bond":"0元","priority_tag":"NO"})

remaining = conn.execute("SELECT COUNT(*) FROM pages WHERE status='raw'").fetchone()[0]
print(f"第4批完成！已处理: 36条")
print(f"剩余: {remaining} 条")
conn.close()
