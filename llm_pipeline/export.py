"""
导出 extracted 表为 Excel 表格
用法: python llm_pipeline/export.py
"""

import sqlite3, json, sys, os

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "llm_bidding.db")


def export():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT p.title, p.url, p.notice_type, p.region, p.publish_date,
               p.source, e.data_json
        FROM extracted e
        JOIN pages p ON e.page_id = p.id
        ORDER BY p.crawled_at DESC
    """).fetchall()

    if not rows:
        print("没有已提取的数据。先跑 llm_pipeline/extract.py")
        return

    # 扁平化 JSON → 表格行
    table = []
    for r in rows:
        data = json.loads(r["data_json"]) if r["data_json"] else {}
        table.append({
            "标题": data.get("title") or r["title"],
            "公告类型": data.get("notice_type") or r["notice_type"],
            "地区": data.get("region") or r["region"],
            "行业": data.get("industry", ""),
            "发布时间": data.get("publish_date") or r["publish_date"],
            "预算": data.get("budget_amount", ""),
            "投标截止": data.get("submission_deadline", ""),
            "业主单位": data.get("buyer", ""),
            "代理机构": data.get("agency", ""),
            "资质要求": "\n".join(data.get("eligibility") or []) if isinstance(data.get("eligibility"), list) else data.get("eligibility", ""),
            "招标范围": data.get("scope_of_work", ""),
            "中标供应商": data.get("winner", ""),
            "中标金额": data.get("winning_price", ""),
            "原文链接": r["url"],
        })

    import pandas as pd
    df = pd.DataFrame(table)
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bidding_extracted.xlsx")
    df.to_excel(path, index=False, engine="openpyxl")

    print(f"导出: {path}")
    print(f"行数: {len(table)}, 列数: {len(table[0]) if table else 0}")

    conn.close()


if __name__ == "__main__":
    export()
