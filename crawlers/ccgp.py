"""
中国政府采购网爬虫 (ccgp.gov.cn)
================================
国家级政府采购平台，有公开搜索 API
"""

import json
import logging
import re
from datetime import datetime
from urllib.parse import urlencode

import requests

from config import SPORTS_KEYWORDS, REQUEST_DELAY, GUANGDONG_CITIES, FUJIAN_CITIES
from crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)


class CcgpCrawler(BaseCrawler):
    """中国政府采购网爬虫"""

    site_name: str = "中国政府采购网"
    site_url: str = "https://www.ccgp.gov.cn"
    platform_type: str = "government"

    SEARCH_API = "https://search.ccgp.gov.cn/bxsearch"

    # ccgp 地区编码
    ZONE_IDS = {
        "广东省": 440000,
        "深圳市": 440300,
        "广州市": 440100,
        "东莞市": 441900,
        "佛山市": 440600,
        "福建省": 350000,
        "龙岩市": 350800,
        "福州市": 350100,
        "厦门市": 350200,
        "泉州市": 350500,
    }

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.ccgp.gov.cn/",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def crawl(self, keyword: str = "体育", city: str = None) -> int:
        """通过 ccgp 搜索 API 获取数据"""
        logger.info(f"\n{'='*50}")
        logger.info(f"🏙️  中国政府采购网: 关键词={keyword}")
        logger.info(f"{'='*50}")

        total_new = 0

        # 按目标城市逐个搜索
        target_zones = {
            k: v for k, v in self.ZONE_IDS.items()
            if k in GUANGDONG_CITIES or k in FUJIAN_CITIES or k in ("广东省", "福建省")
        }

        for zone_name, zone_id in target_zones.items():
            logger.info(f"\n📍 地区: {zone_name} ({zone_id})")
            new_count = self._search_zone(keyword, zone_id, zone_name)
            total_new += new_count
            self.delay(REQUEST_DELAY)

        self.log_stats()
        return total_new

    def _search_zone(self, keyword: str, zone_id: int, zone_name: str) -> int:
        """搜索指定地区"""
        new_count = 0

        for page in range(1, 10):  # 最多 10 页
            try:
                params = {
                    "searchtype": 1,
                    "page_index": page,
                    "bidSort": 0,
                    "buyerName": "",
                    "projectId": "",
                    "pinMu": 0,
                    "bidType": 0,
                    "dbselect": "bidx",
                    "kw": keyword,
                    "start_time": "2025:06:27",
                    "end_time": "2026:06:27",
                    "timeType": 6,
                    "displayZone": zone_id,
                    "zoneId": zone_id,
                    "pppStatus": 0,
                    "agentName": "",
                }

                url = f"{self.SEARCH_API}?{urlencode(params)}"
                resp = self.session.get(url, timeout=30, verify=False)

                if resp.status_code != 200:
                    logger.warning(f"  HTTP {resp.status_code} (page {page})")
                    break

                text = resp.text.strip()
                if not text:
                    break

                data = json.loads(text)

                records = data.get("records", [])
                if not records:
                    break

                logger.info(f"  📄 第 {page} 页: {len(records)} 条")

                for r in records:
                    title = r.get("title", r.get("recordName", ""))
                    if not any(kw in title for kw in SPORTS_KEYWORDS):
                        continue

                    info_url = r.get("url", "")
                    if not info_url:
                        infoid = r.get("infoid", "")
                        info_url = f"{self.site_url}/cggg/dfgg/{infoid}.htm"

                    record = {
                        "title": title,
                        "url": info_url,
                        "region": r.get("zoneName", zone_name),
                        "procurement_method": r.get("purchaseMethod", ""),
                        "procuring_entity": r.get("buyerName", ""),
                        "publish_date": r.get("publishDate", r.get("createTime", "")),
                        "budget_amount": f"{r.get('budget', '')} 万元" if r.get("budget") else "",
                        "category": "体育类",
                    }

                    # 获取详情
                    if info_url:
                        qual, req = self._fetch_detail(info_url)
                        record["qualification"] = qual
                        record["requirements"] = req

                    if self.save(record):
                        new_count += 1

                self.delay(REQUEST_DELAY)

                # 检查是否有更多页
                total = data.get("total", 0)
                if page * 20 >= total:
                    break

            except json.JSONDecodeError:
                logger.debug(f"  JSON 解析失败 (page {page})")
                break
            except Exception as e:
                logger.warning(f"  搜索异常 (page {page}): {e}")
                break

        return new_count

    def _fetch_detail(self, url: str) -> tuple:
        """获取公告详情"""
        try:
            resp = self.session.get(url, timeout=30, verify=False)
            resp.encoding = resp.apparent_encoding or "utf-8"
            # 简单提取文本
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "lxml")
            body = soup.get_text(separator="\n", strip=True)

            lines = [l.strip() for l in body.split("\n") if len(l.strip()) > 3]

            # 资质要求
            qualification = ""
            qual_kws = ["资格要求", "资质要求", "投标人资格", "资格条件"]
            for i, line in enumerate(lines):
                if any(kw in line for kw in qual_kws):
                    qualification = "\n".join(lines[i:min(i + 20, len(lines))])
                    break

            requirements = "\n".join(lines[:60])[:5000]
            self.delay(REQUEST_DELAY * 0.5)
            return (qualification[:3000], requirements)
        except Exception as e:
            logger.debug(f"详情获取失败: {url[:80]} - {e}")
            return ("", "")
