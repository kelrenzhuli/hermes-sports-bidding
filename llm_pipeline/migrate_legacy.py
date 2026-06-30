# -*- coding: utf-8 -*-
"""
数据迁移脚本 - 将遗留数据导入 projects_v3 表

三步迁移：
1. 从 final_export_full.py 的 extracted 字典导入 40 条 YES 记录（含完整业务字段）
2. 从 cleaned_data.json 导入 153 条记录（通过 page_id 映射 + text 正则提取 project_number）
3. 按 project_number 合并同一项目的多条记录

核心策略：
- extracted 字典有精确的 project_number（40 条 YES），先导入作为基础行
- cleaned_data.json 中 100/153 条记录的 text 字段包含 project_number 模式
- 同一 project_number 的记录通过 upsert 合并（UPDATE 追加 lifecycle_history）
- 无 project_number 的记录跳过（53 条低价值 NO 记录）
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_pipeline.db import get_conn, upsert_project_v3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "cleaned_data.json")
EXTRACTED_PATH = os.path.join(BASE_DIR, "final_export_full.py")
DB_PATH = os.path.join(BASE_DIR, "llm_bidding_v2.db")

PN_REGEX = re.compile(r'(\[[\w]+\][\w\[\]]+)')


def load_cleaned_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_extracted_dict():
    with open(EXTRACTED_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    start = content.find("extracted = {")
    if start == -1:
        print("  [WARN] extracted dict not found")
        return {}
    end_match = re.search(r"^# ---- BUILD EXCEL ----", content[start:], re.MULTILINE)
    if end_match:
        end = start + end_match.start()
    else:
        end = len(content)
    dict_text = content[start:end].strip()
    local_vars = {}
    exec(dict_text, {}, local_vars)
    return local_vars.get("extracted", {})


def extract_pn_from_text(text):
    """从文本中提取项目编号"""
    if not text:
        return None
    m = PN_REGEX.search(text)
    if m:
        return m.group(1).strip()
    return None


def build_project_number_map(cleaned_data, extracted):
    """
    构建 page_id -> project_number 映射
    来源 1: extracted 字典（精确）
    来源 2: cleaned_data text 字段（正则提取）
    """
    pn_map = {}

    # 来源 1: extracted 字典
    for page_id, vals in extracted.items():
        pn_raw = vals[8] if len(vals) > 8 else None
        if pn_raw and pn_raw != "原网页未披露该项":
            pn_raw = pn_raw.strip()
            pn_map[str(page_id)] = pn_raw
            pn_map[int(page_id)] = pn_raw

    # 来源 2: cleaned_data text 字段
    for d in cleaned_data:
        pid = d.get("id")
        if pid is None:
            continue
        if pid in pn_map:
            continue
        text = d.get("text", "") or ""
        pn = extract_pn_from_text(text)
        if pn:
            pn_map[pid] = pn

    return pn_map


def step1_import_extracted(conn, extracted, pn_map):
    """导入 40 条 YES 记录（含完整业务字段）"""
    print(f"\nStep 1: import extracted dict ({len(extracted)} YES records)")

    try:
        all_data = load_cleaned_data()
        data_by_id = {d.get("id"): d for d in all_data}
    except Exception:
        data_by_id = {}

    inserted = 0
    updated = 0
    for page_id, vals in extracted.items():
        # 处理项目编号：无效值时尝试从 pn_map 获取，再不行用 page_id 降级
        pn_val = vals[8] if len(vals) > 8 else None
        if not pn_val or pn_val == "原网页未披露该项":
            pn_val = pn_map.get(page_id)
        if not pn_val:
            pn_val = f"[PLACEHOLDER-{page_id}]"

        record = {
            "page_id": page_id,
            "title": vals[6] if len(vals) > 6 else "",
            "priority_tag": vals[0],
            "priority_reason": vals[1],
            "project_status": vals[2],
            "lifecycle_status": vals[2],
            "budget_or_winning": vals[3],
            "supplier": vals[4],
            "submission_deadline": vals[5],
            "scope_description": vals[6],
            "buyer": vals[7],
            "project_number": pn_val,
            "notice_type": "",
            "publish_date": "",
            "source_url": "原网页未保留",
        }

        if page_id in data_by_id:
            d = data_by_id[page_id]
            record["notice_type"] = d.get("type", "")
            record["publish_date"] = d.get("date", "")
            if not record["title"]:
                record["title"] = d.get("title", "")

        action, pn = upsert_project_v3(conn, record)
        if action == "inserted":
            inserted += 1
        elif action == "updated":
            updated += 1

        if (inserted + updated) % 10 == 0:
            print(f"  progress: {inserted + updated}/{len(extracted)}")

    print(f"  done: {inserted} new, {updated} updated")
    return inserted


def step2_import_cleaned(conn, cleaned_data, pn_map, extracted_ids):
    """导入 cleaned_data.json 记录，利用 pn_map 获取 project_number"""
    print(f"\nStep 2: import cleaned_data.json ({len(cleaned_data)} records)")

    inserted = 0
    updated = 0
    skipped_no_pn = 0
    skipped_already = 0

    for i, item in enumerate(cleaned_data):
        page_id = item.get("id")

        # 跳过已被 Step 1 导入的记录
        if page_id in extracted_ids:
            skipped_already += 1
            continue

        # 获取 project_number
        project_number = pn_map.get(page_id)
        if not project_number:
            skipped_no_pn += 1
            continue

        record = {
            "title": item.get("title", ""),
            "project_number": project_number,
            "notice_type": item.get("type", ""),
            "publish_date": item.get("date", ""),
            "source_url": "原网页未保留",
            "page_id": page_id,
            "raw_html": item.get("text", ""),
        }

        action, pn = upsert_project_v3(conn, record)
        if action == "inserted":
            inserted += 1
        elif action == "updated":
            updated += 1

        if (i + 1) % 30 == 0:
            print(f"  progress: {i + 1}/{len(cleaned_data)}")

    print(f"  done: {inserted} new, {updated} updated, {skipped_already} already in step1, {skipped_no_pn} skipped (no project_number)")


def step3_merge_duplicates(conn):
    """按 project_number 合并重复记录（防呆，通常不会出现）"""
    print("\nStep 3: merge duplicate project_number")

    rows = conn.execute("""
        SELECT project_number, COUNT(*) as cnt
        FROM projects_v3
        WHERE project_number IS NOT NULL AND project_number != ''
        GROUP BY project_number
        HAVING cnt > 1
        ORDER BY cnt DESC
    """).fetchall()

    if not rows:
        print("  no duplicates found")
        return

    print(f"  found {len(rows)} duplicate groups:")
    for r in rows[:10]:
        print(f"    {r['project_number']}: {r['cnt']} records")
    if len(rows) > 10:
        print(f"    ... and {len(rows) - 10} more")

    merged_count = 0
    for row in rows:
        pn = row["project_number"]
        records = conn.execute(
            "SELECT * FROM projects_v3 WHERE project_number=? ORDER BY publish_date ASC, id ASC",
            (pn,)
        ).fetchall()

        if len(records) <= 1:
            continue

        primary = dict(records[0])
        keep_id = primary["id"]

        try:
            history = json.loads(primary.get("lifecycle_history") or "[]")
        except (json.JSONDecodeError, TypeError):
            history = []
        try:
            source_ids = json.loads(primary.get("source_page_ids") or "[]")
        except (json.JSONDecodeError, TypeError):
            source_ids = []

        for rec in records[1:]:
            r = dict(rec)

            # 合并 lifecycle_history
            try:
                rh = json.loads(r.get("lifecycle_history") or "[]")
            except (json.JSONDecodeError, TypeError):
                rh = []
            for entry in rh:
                if entry not in history:
                    history.append(entry)

            # 合并 source_page_ids
            try:
                rs = json.loads(r.get("source_page_ids") or "[]")
            except (json.JSONDecodeError, TypeError):
                rs = []
            for sid in rs:
                if sid not in source_ids:
                    source_ids.append(sid)

            # 填充空字段
            for field in [
                "supplier", "budget_or_winning", "submission_deadline",
                "buyer", "scope_description", "winner",
                "winning_price_raw", "winning_price_norm",
            ]:
                if not primary.get(field) or primary[field] == "原网页未披露该项":
                    if r.get(field) and r[field] != "原网页未披露该项":
                        primary[field] = r[field]

            # 生命周期状态升级（只允许正向：预告中->进行中->已完结）
            ls_order = {"预告中": 0, "进行中": 1, "已完结": 2}
            current_level = ls_order.get(primary.get("lifecycle_status", "进行中"), 1)
            if ls_order.get(r.get("lifecycle_status"), 1) > current_level:
                primary["lifecycle_status"] = r["lifecycle_status"]

            conn.execute("DELETE FROM projects_v3 WHERE id=?", (r["id"],))
            merged_count += 1

        primary["lifecycle_history"] = json.dumps(history, ensure_ascii=False)
        primary["source_page_ids"] = json.dumps(source_ids, ensure_ascii=False)
        conn.execute("""
            UPDATE projects_v3 SET
                lifecycle_status=?,
                lifecycle_history=?,
                source_page_ids=?,
                supplier=?,
                budget_or_winning=?,
                submission_deadline=?,
                buyer=?,
                scope_description=?,
                winner=?,
                winning_price_raw=?,
                winning_price_norm=?,
                last_updated=datetime('now','localtime')
            WHERE id=?
        """, (
            primary.get("lifecycle_status"),
            primary.get("lifecycle_history"),
            primary.get("source_page_ids"),
            primary.get("supplier"),
            primary.get("budget_or_winning"),
            primary.get("submission_deadline"),
            primary.get("buyer"),
            primary.get("scope_description"),
            primary.get("winner"),
            primary.get("winning_price_raw"),
            primary.get("winning_price_norm"),
            keep_id,
        ))
        conn.commit()

    print(f"  merged: removed {merged_count} duplicate records")


def summary(conn):
    total = conn.execute("SELECT COUNT(*) as n FROM projects_v3").fetchone()["n"]
    yes = conn.execute("SELECT COUNT(*) as n FROM projects_v3 WHERE priority_tag='YES'").fetchone()["n"]
    with_pn = conn.execute("SELECT COUNT(*) as n FROM projects_v3 WHERE project_number IS NOT NULL AND project_number != ''").fetchone()["n"]
    lifecycle = conn.execute("""
        SELECT lifecycle_status, COUNT(*) as n FROM projects_v3
        GROUP BY lifecycle_status ORDER BY n DESC
    """).fetchall()

    print(f"\n{'='*50}")
    print("Migration Summary")
    print(f"{'='*50}")
    print(f"  projects_v3 total: {total}")
    print(f"  YES records: {yes}")
    print(f"  With project_number: {with_pn}")
    print(f"  Lifecycle distribution:")
    for r in lifecycle:
        print(f"    {r['lifecycle_status']}: {r['n']}")


def main():
    print("=" * 50)
    print("Legacy Data Migration -> projects_v3")
    print("=" * 50)

    conn = get_conn(DB_PATH)

    # 加载数据
    cleaned_data = load_cleaned_data()
    extracted = load_extracted_dict()
    extracted_ids = set(extracted.keys())

    # 构建 project_number 映射
    pn_map = build_project_number_map(cleaned_data, extracted)
    mapped_count = sum(1 for k, v in pn_map.items() if isinstance(k, int))
    print(f"\nProject number map: {mapped_count} page_ids mapped")

    # 执行迁移
    step1_import_extracted(conn, extracted, pn_map)
    step2_import_cleaned(conn, cleaned_data, pn_map, extracted_ids)
    step3_merge_duplicates(conn)
    summary(conn)

    conn.close()
    print("\nMigration complete")


if __name__ == "__main__":
    main()
