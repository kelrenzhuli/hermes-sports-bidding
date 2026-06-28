"""
全网监控版 — 导出 Excel
======================
从 projects 表导出，23字段按优先顺序排列，金额标准化。
"""

import sqlite3, json, os

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "llm_bidding.db")

COLUMNS = [
    ("项目编号",     "project_number"),
    ("标题",         "title"),
    ("项目状态",     "project_status"),
    ("公告类型",     "notice_type"),
    ("省",           "province"),
    ("市",           "city"),
    ("区县",         "district"),
    ("行业",         "industry"),
    ("发布时间",     "publish_date"),
    ("采集时间",     "first_crawled"),
    ("预算原文",     "budget_raw"),
    ("预算(万元)",   "budget_norm"),
    ("投标截止",     "submission_deadline"),
    ("业主单位",     "buyer"),
    ("代理机构",     "agency"),
    ("资质要求",     "eligibility"),
    ("招标范围",     "scope_of_work"),
    ("中标供应商",   "winner"),
    ("中标金额原文", "winning_price_raw"),
    ("中标金额(万元)", "winning_price_norm"),
    ("原文链接",     "url"),
    ("附件",         "attachment_urls"),
    ("来源",         "source"),
]


def export(db_path=DB):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # 检查表是否存在
    has_projects = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"
    ).fetchone()

    if not has_projects:
        # 兼容旧版：从 pages+extracted 读取
        rows = _export_v1(conn)
    else:
        rows = conn.execute(
            "SELECT * FROM projects ORDER BY project_status, publish_date DESC"
        ).fetchall()

    if not rows:
        print("没有数据")
        conn.close()
        return

    import pandas as pd
    table = []
    for r in rows:
        row_dict = {}
        for col_name, col_key in COLUMNS:
            val = r[col_key] if col_key in r.keys() else None
            # JSON list → 多行文本
            if isinstance(val, list):
                val = "\n".join(str(v) for v in val)
            # float → 保留两位
            if isinstance(val, float):
                val = round(val, 2)
            row_dict[col_name] = val if val is not None else ""

        # 动态字段：项目状态格式化
        status = row_dict.get("项目状态", "")
        status_emoji = {
            "招标中": "🟡 招标中",
            "已开标": "🔵 已开标",
            "已中标": "🟢 已中标",
            "已废标": "🔴 已废标",
            "已变更": "🟠 已变更",
            "已结束": "⚫ 已结束",
        }
        if status in status_emoji:
            row_dict["项目状态"] = status_emoji[status]

        table.append(row_dict)

    df = pd.DataFrame(table)
    path = os.path.join(os.path.dirname(DB), "bidding_extracted.xlsx")
    df.to_excel(path, index=False, engine="openpyxl")

    # 统计
    by_status = df["项目状态"].value_counts().to_dict() if "项目状态" in df.columns else {}
    by_province = df["省"].value_counts().to_dict() if "省" in df.columns else {}

    print(f"导出: {path}")
    print(f"行数: {len(table)}, 列数: {len(COLUMNS)}")
    print(f"\n状态分布:")
    for s, c in sorted(by_status.items()):
        print(f"  {s}: {c}条")
    print(f"\n省份分布:")
    for p, c in sorted(by_province.items(), key=lambda x: -x[1]):
        print(f"  {p}: {c}条")

    conn.close()
    return path


def _export_v1(conn):
    """兼容旧版 pages+extracted 表"""
    return conn.execute("""
        SELECT p.title, p.url, p.notice_type, p.region,
               p.publish_date, p.source, e.data_json
        FROM extracted e
        JOIN pages p ON e.page_id = p.id
        ORDER BY p.crawled_at DESC
    """).fetchall()


if __name__ == "__main__":
    export()
