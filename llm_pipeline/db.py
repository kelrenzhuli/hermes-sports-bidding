"""
数据库连接管理 + projects_v3 合并逻辑
======================================
统一 SQLite 访问层，提供 upsert、查询、状态跃迁功能。
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Optional

# 默认数据库路径（项目根目录下的 llm_bidding_v2.db）
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "llm_bidding_v2.db"
)


# ─── 连接管理 ───────────────────────────────

def get_conn(db_path: Optional[str] = None) -> sqlite3.Connection:
    """获取数据库连接（确保 projects_v3 表已创建）"""
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _ensure_tables(conn)
    return conn


def _ensure_tables(conn: sqlite3.Connection):
    """确保 projects_v3 表存在"""
    from llm_pipeline.schema_v3 import PROJECTS_V3_DDL
    conn.executescript(PROJECTS_V3_DDL)
    conn.commit()


# ─── 公告类型 → 状态映射 ─────────────────────

def _infer_lifecycle_status(notice_type: str) -> Optional[str]:
    """根据公告类型推断生命周期状态"""
    from llm_pipeline.schema_v3 import NOTICE_TYPE_TRANSITIONS
    # 精确匹配
    if notice_type in NOTICE_TYPE_TRANSITIONS:
        return NOTICE_TYPE_TRANSITIONS[notice_type]
    # 部分匹配
    for key, val in NOTICE_TYPE_TRANSITIONS.items():
        if key in notice_type:
            return val
    return None


def _infer_project_status(notice_type: str) -> str:
    """根据公告类型推断项目状态（进行中/预告中/已完结）"""
    status = _infer_lifecycle_status(notice_type)
    if status:
        return status
    # 默认：已完结（兜底）
    return "已完结"


def _infer_timeliness(publish_date: Optional[str]) -> str:
    """根据发布日期推断时效层级"""
    if not publish_date:
        return "市场情报"
    # 取年份
    year = publish_date[:4]
    if year.isdigit() and int(year) >= 2025:
        return "实时线索"
    return "市场情报"


def _extract_project_number_from_text(title: str, notice_type: str) -> Optional[str]:
    """从标题中提取项目编号（回退方案）"""
    import re
    # 模式如 [350001]FM[GK]2025002
    m = re.search(r'(\[[\w]+\][\w\[\]]+)', title)
    if m:
        return m.group(1).strip()
    return None


# ─── 合并核心逻辑 ───────────────────────────

def upsert_project_v3(conn: sqlite3.Connection, record: dict) -> tuple:
    """
    将一条记录合并到 projects_v3 表。

    参数:
        record: 包含以下键的字典：
            - title, project_number, notice_type, publish_date
            - source_url, region (可选)
            - 以及所有 15 个业务字段

    返回:
        (action: str, project_number: str)
        action = 'inserted' / 'updated' / 'skipped'
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pn = record.get("project_number")
    # "原网页未披露该项" 视为无编号
    if pn == "原网页未披露该项":
        pn = None
    title = record.get("title", "")
    notice_type = record.get("notice_type", "")
    publish_date = record.get("publish_date", "")
    page_id = record.get("page_id")

    # 如果没有 project_number，尝试从标题提取
    if not pn:
        pn = _extract_project_number_from_text(title, notice_type)
    if not pn:
        # 无 project_number → 无法合并，跳过
        return ("skipped", None)

    # 查询是否已存在
    existing = conn.execute(
        "SELECT id, lifecycle_history, source_page_ids, project_status, "
        "lifecycle_status, "
        "notice_type, supplier, budget_or_winning, submission_deadline, "
        "buyer, priority_tag, priority_reason, timeliness_stratum, "
        "scope_description, first_crawled "
        "FROM projects_v3 WHERE project_number=?",
        (pn,)
    ).fetchone()

    # 构建新记录
    # project_status: 优先使用传入值，否则从 notice_type 推断
    explicit_project_status = record.get("project_status")
    new_record = {
        "project_number": pn,
        "title": title,
        "timeliness_stratum": _infer_timeliness(publish_date),
        "project_status": explicit_project_status or _infer_project_status(notice_type),
        "priority_tag": record.get("priority_tag", "NO"),
        "priority_reason": record.get("priority_reason"),
        "budget_or_winning": record.get("budget_or_winning"),
        "supplier": record.get("supplier"),
        "submission_deadline": record.get("submission_deadline"),
        "buyer": record.get("buyer"),
        "notice_type": notice_type,
        "publish_date": publish_date,
        "source_url": record.get("source_url"),
        "scope_description": record.get("scope_description"),
        "budget_raw": record.get("budget_raw"),
        "budget_norm": record.get("budget_norm"),
        "winning_price_raw": record.get("winning_price_raw"),
        "winning_price_norm": record.get("winning_price_norm"),
        "agency": record.get("agency"),
        "eligibility": record.get("eligibility"),
        "winner": record.get("winner"),
        "last_updated": now,
    }

    # 生命周期状态：优先使用传入值，否则从 notice_type 推断
    explicit_lifecycle_status = record.get("lifecycle_status")
    new_lifecycle_status = explicit_lifecycle_status or _infer_lifecycle_status(notice_type)

    if existing:
        # ── 更新已有记录 ──
        eid = existing["id"]

        # 反序列化 JSON 字段
        try:
            lifecycle_history = json.loads(existing["lifecycle_history"] or "[]")
        except json.JSONDecodeError:
            lifecycle_history = []
        try:
            source_page_ids = json.loads(existing["source_page_ids"] or "[]")
        except json.JSONDecodeError:
            source_page_ids = []

        # 追加阶段记录到 lifecycle_history
        history_entry = {
            "notice_type": notice_type,
            "date": publish_date,
            "url": record.get("source_url"),
        }
        if page_id:
            history_entry["page_id"] = page_id
        # 避免重复追加完全相同的记录
        if not any(
            h.get("notice_type") == notice_type and h.get("date") == publish_date
            for h in lifecycle_history
        ):
            lifecycle_history.append(history_entry)

        # 追加 page_id
        if page_id and page_id not in source_page_ids:
            source_page_ids.append(page_id)

        new_record["lifecycle_history"] = json.dumps(lifecycle_history, ensure_ascii=False)
        new_record["source_page_ids"] = json.dumps(source_page_ids, ensure_ascii=False)

        # 生命周期跃迁（只允许正向跃迁：预告中→进行中→已完结）
        old_ls = existing["lifecycle_status"] or "进行中"
        ls_order = {"预告中": 0, "进行中": 1, "已完结": 2}
        if new_lifecycle_status and ls_order.get(new_lifecycle_status, -1) > ls_order.get(old_ls, -1):
            new_record["lifecycle_status"] = new_lifecycle_status
        else:
            new_record["lifecycle_status"] = old_ls

        # project_status 同样只允许正向跃迁
        old_ps = existing["project_status"] or "进行中"
        new_ps = new_record.get("project_status") or old_ps
        if ls_order.get(new_ps, -1) > ls_order.get(old_ps, -1):
            new_record["project_status"] = new_ps
        else:
            new_record["project_status"] = old_ps

        # 生命周期无关字段（新值覆盖旧值）
        for field in ["title", "notice_type", "publish_date", "source_url", "buyer"]:
            old_val = existing[field] if field in existing.keys() else None
            new_val = new_record.get(field)
            if new_val and new_val != "原网页未披露该项":
                pass  # 使用新值
            else:
                new_record[field] = old_val

        # 金额/供应商/截止时间/描述：首次有效值保留（合同/中标金额优先于预算金额）
        for field in ["budget_or_winning", "supplier", "submission_deadline", "scope_description"]:
            old_val = existing[field] if field in existing.keys() else None
            if old_val and old_val != "原网页未披露该项":
                # 已有有效值 → 保留（除非新值来自更高优先级的公告类型）
                new_record[field] = old_val
            else:
                new_val = new_record.get(field)
                if new_val and new_val != "原网页未披露该项":
                    pass  # 使用新值填充空位
                else:
                    new_record[field] = old_val

        # 优先级和标记理由保留首次判定
        if existing["priority_tag"] and existing["priority_tag"] == "YES":
            new_record["priority_tag"] = "YES"
            if existing["priority_reason"]:
                new_record["priority_reason"] = existing["priority_reason"]

        if existing["scope_description"]:
            new_record["scope_description"] = existing["scope_description"]

        # 更新 first_crawled
        first_crawled = existing["first_crawled"] if "first_crawled" in existing.keys() else None
        new_record["first_crawled"] = first_crawled or now

        # 执行 UPDATE
        set_clauses = []
        set_values = []
        skip_fields = {"id", "created_at", "first_crawled"}
        for key, val in new_record.items():
            if key not in skip_fields:
                set_clauses.append(f"{key}=?")
                set_values.append(val)
        set_values.append(eid)
        conn.execute(
            f"UPDATE projects_v3 SET {', '.join(set_clauses)}, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            set_values
        )
        conn.commit()
        return ("updated", pn)

    else:
        # ── 插入新记录 ──
        # 构建 lifecycle_history
        lifecycle_history = [{
            "notice_type": notice_type,
            "date": publish_date,
            "url": record.get("source_url"),
        }]
        if page_id:
            lifecycle_history[0]["page_id"] = page_id

        # 构建 source_page_ids
        source_page_ids = [page_id] if page_id else []

        new_record["lifecycle_history"] = json.dumps(lifecycle_history, ensure_ascii=False)
        new_record["source_page_ids"] = json.dumps(source_page_ids, ensure_ascii=False)
        new_record["lifecycle_status"] = new_lifecycle_status or "进行中"
        new_record["first_crawled"] = now
        new_record["raw_html"] = record.get("raw_html")

        fields = [
            "project_number", "title", "timeliness_stratum", "project_status",
            "priority_tag", "priority_reason", "budget_or_winning", "supplier",
            "submission_deadline", "buyer", "notice_type", "publish_date",
            "source_url", "scope_description", "lifecycle_status",
            "lifecycle_history", "source_page_ids",
            "budget_raw", "budget_norm", "winning_price_raw", "winning_price_norm",
            "agency", "eligibility", "winner",
            "first_crawled", "last_updated", "raw_html",
        ]
        placeholders = ", ".join("?" for _ in fields)
        col_names = ", ".join(fields)
        values = [new_record.get(f) for f in fields]
        conn.execute(
            f"INSERT OR IGNORE INTO projects_v3 ({col_names}) VALUES ({placeholders})",
            values
        )
        conn.commit()
        return ("inserted", pn)


# ─── 查询接口 ───────────────────────────────

def get_pending_pages(conn: sqlite3.Connection, limit: int = 50) -> list:
    """获取待提取的页面（status='raw' 且有 raw_html）"""
    rows = conn.execute("""
        SELECT id, title, notice_type, publish_date, url, raw_html, project_number
        FROM pages
        WHERE status='raw' AND raw_html IS NOT NULL
        ORDER BY id
        LIMIT ?
    """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def get_all_projects(conn: sqlite3.Connection) -> list:
    """获取所有 projects_v3 记录，按发布时间降序"""
    rows = conn.execute("""
        SELECT * FROM projects_v3
        ORDER BY publish_date DESC, id DESC
    """).fetchall()
    return [dict(r) for r in rows]


def get_yes_projects(conn: sqlite3.Connection) -> list:
    """获取 priority_tag='YES' 的记录"""
    rows = conn.execute("""
        SELECT * FROM projects_v3
        WHERE priority_tag='YES'
        ORDER BY publish_date DESC, id DESC
    """).fetchall()
    return [dict(r) for r in rows]


def init_db(db_path: Optional[str] = None):
    """初始化数据库（建表）"""
    conn = get_conn(db_path)
    conn.close()
    print(f"✅ projects_v3 表已就绪: {db_path or DEFAULT_DB_PATH}")


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成")
