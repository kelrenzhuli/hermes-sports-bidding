"""
数据存储模块
=======
使用 SQLite 存储爬取结果，支持去重、导出。
新增 status 字段供 hermes 消费：raw → processed → notified
"""

import sqlite3
import hashlib
from datetime import datetime
from typing import Optional
import pandas as pd
from config import DB_PATH, EXCEL_PATH


class Database:
    """SQLite 数据库管理器"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表结构"""
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bidding_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT,
                    source TEXT,
                    platform_type TEXT DEFAULT 'government',
                    category TEXT DEFAULT '体育类',
                    region TEXT,
                    procurement_method TEXT,
                    procuring_entity TEXT,
                    publish_date TEXT,
                    deadline TEXT,
                    budget_amount TEXT,
                    requirements TEXT,
                    qualification TEXT,
                    detail_html TEXT,
                    status TEXT DEFAULT 'raw',
                    crawl_time TEXT,
                    hash_key TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_hash ON bidding_records(hash_key)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_region ON bidding_records(region)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON bidding_records(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_publish_date ON bidding_records(publish_date)
            """)

            # 迁移：给旧表加 status 列（如果不存在）
            try:
                conn.execute("ALTER TABLE bidding_records ADD COLUMN status TEXT DEFAULT 'raw'")
            except sqlite3.OperationalError:
                pass  # 列已存在
            try:
                conn.execute("ALTER TABLE bidding_records ADD COLUMN platform_type TEXT DEFAULT 'government'")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE bidding_records ADD COLUMN budget_amount TEXT DEFAULT ''")
            except sqlite3.OperationalError:
                pass

    def _connect(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    def record_exists(self, hash_key: str) -> bool:
        """检查记录是否已存在（去重）"""
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT 1 FROM bidding_records WHERE hash_key = ?", (hash_key,)
            )
            return cur.fetchone() is not None

    def save_record(self, record: dict) -> bool:
        """
        保存一条记录，返回是否新增（True=新增, False=已存在）
        """
        hash_key = record.get("hash_key") or self._make_hash(record)
        if self.record_exists(hash_key):
            return False

        with self._connect() as conn:
            conn.execute("""
                INSERT INTO bidding_records
                    (title, url, source, platform_type, category, region,
                     procurement_method, procuring_entity, publish_date,
                     deadline, budget_amount, requirements, qualification,
                     detail_html, status, crawl_time, hash_key)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.get("title", ""),
                record.get("url", ""),
                record.get("source", ""),
                record.get("platform_type", "government"),
                record.get("category", "体育类"),
                record.get("region", ""),
                record.get("procurement_method", ""),
                record.get("procuring_entity", ""),
                record.get("publish_date", ""),
                record.get("deadline", ""),
                record.get("budget_amount", ""),
                record.get("requirements", ""),
                record.get("qualification", ""),
                record.get("detail_html", ""),
                record.get("status", "raw"),
                record.get("crawl_time", datetime.now().isoformat()),
                hash_key,
            ))
        return True

    def save_records_batch(self, records: list) -> int:
        """批量保存，返回新增数量"""
        added = 0
        for record in records:
            if self.save_record(record):
                added += 1
        return added

    def _make_hash(self, record: dict) -> str:
        """生成唯一哈希用于去重"""
        key = f"{record.get('title', '')}|{record.get('url', '')}|{record.get('publish_date', '')}"
        return hashlib.md5(key.encode("utf-8")).hexdigest()

    def get_raw_records(self, limit: int = 100) -> list:
        """获取待 hermes 处理的 raw 记录"""
        with self._connect() as conn:
            cur = conn.execute(
                """SELECT id, title, url, source, region, publish_date,
                          requirements, qualification, budget_amount
                   FROM bidding_records WHERE status = 'raw'
                   ORDER BY publish_date DESC LIMIT ?""",
                (limit,),
            )
            return cur.fetchall()

    def mark_processed(self, record_id: int, status: str = "processed"):
        """标记记录处理状态"""
        with self._connect() as conn:
            conn.execute(
                "UPDATE bidding_records SET status = ? WHERE id = ?",
                (status, record_id),
            )

    def get_statistics(self) -> dict:
        """获取统计信息"""
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM bidding_records").fetchone()[0]
            by_region = conn.execute(
                "SELECT region, COUNT(*) FROM bidding_records GROUP BY region ORDER BY COUNT(*) DESC"
            ).fetchall()
            by_status = conn.execute(
                "SELECT status, COUNT(*) FROM bidding_records GROUP BY status"
            ).fetchall()
            by_source = conn.execute(
                "SELECT source, COUNT(*) FROM bidding_records GROUP BY source ORDER BY COUNT(*) DESC"
            ).fetchall()
            latest = conn.execute(
                "SELECT title, region, source, publish_date, status FROM bidding_records ORDER BY crawl_time DESC LIMIT 5"
            ).fetchall()
        return {
            "total": total,
            "by_region": dict(by_region),
            "by_status": dict(by_status),
            "by_source": dict(by_source),
            "latest": latest,
        }

    def export_to_excel(self, path: str = None):
        """导出为 Excel"""
        path = path or EXCEL_PATH
        with self._connect() as conn:
            df = pd.read_sql_query(
                """SELECT title, url, source, platform_type, category, region,
                          procurement_method, procuring_entity, publish_date,
                          deadline, budget_amount, requirements,
                          qualification, status, crawl_time
                   FROM bidding_records
                   ORDER BY publish_date DESC, crawl_time DESC""",
                conn,
            )
        df.to_excel(path, index=False, engine="openpyxl")
        return path

    def get_new_records_since(self, since_hours: int = 24) -> list:
        """获取指定小时内的新记录"""
        with self._connect() as conn:
            cur = conn.execute("""
                SELECT title, url, region, publish_date, requirements, qualification
                FROM bidding_records
                WHERE crawl_time >= datetime('now', ?)
                ORDER BY publish_date DESC
            """, (f"-{since_hours} hours",))
            return cur.fetchall()
