"""
爬虫基类模块
===========
所有平台爬虫继承此基类，获得统一的：
  - 数据入库（raw 状态，供 hermes 消费）
  - 合规延迟
  - 日志记录
  - 结果统计
"""

import re
import time
import hashlib
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from storage import Database

logger = logging.getLogger(__name__)


class BaseCrawler:
    """平台爬虫基类"""

    # 子类需覆盖的属性
    site_name: str = "Unknown"       # 平台名称
    site_url: str = ""               # 平台域名
    platform_type: str = "government"  # government / industry / news

    def __init__(self):
        self.db = Database()
        self._stats = {"total": 0, "new": 0, "errors": 0, "skipped": 0}

    # ── 工具方法 ──

    @staticmethod
    def make_hash(title: str, url: str, date: str) -> str:
        """生成唯一哈希用于去重"""
        key = f"{title}|{url}|{date}"
        return hashlib.md5(key.encode("utf-8")).hexdigest()

    @staticmethod
    def delay(seconds: float = 3.0):
        """合规延迟"""
        time.sleep(seconds)

    @staticmethod
    def build_url(base: str, path: str) -> str:
        """拼接 URL"""
        return urljoin(base, path)

    @staticmethod
    def extract_date(text: str) -> str:
        """从文本中提取日期"""
        m = re.search(r'(\d{4}-\d{2}-\d{2})', text)
        return m.group(1) if m else ""

    @staticmethod
    def has_keyword(text: str, keywords: list) -> bool:
        """检查文本是否包含任一关键词"""
        return any(kw in text for kw in keywords)

    # ── 入库方法 ──

    def save(self, record: dict) -> bool:
        """
        统一入库，设置 status='raw' 供 hermes 消费
        返回 True=新增, False=已存在
        """
        record.setdefault("status", "raw")
        record.setdefault("source", self.site_name)
        record.setdefault("platform_type", self.platform_type)
        record.setdefault("crawl_time", datetime.now().isoformat())

        if not record.get("hash_key"):
            record["hash_key"] = self.make_hash(
                record.get("title", ""),
                record.get("url", ""),
                record.get("publish_date", ""),
            )

        is_new = self.db.save_record(record)
        if is_new:
            self._stats["new"] += 1
        else:
            self._stats["skipped"] += 1
        self._stats["total"] += 1
        return is_new

    # ── 统计 ──

    @property
    def stats(self) -> dict:
        return dict(self._stats)

    def log_stats(self):
        """输出统计摘要"""
        s = self._stats
        logger.info(
            f"📊 [{self.site_name}] 总计={s['total']} "
            f"新增={s['new']} 跳过={s['skipped']} 错误={s['errors']}"
        )

    # ── 子类必须实现 ──

    async def crawl(self, keyword: str, city: str = None) -> int:
        """
        执行爬取，返回新增条数。
        子类必须实现此方法。
        """
        raise NotImplementedError("子类必须实现 crawl() 方法")
