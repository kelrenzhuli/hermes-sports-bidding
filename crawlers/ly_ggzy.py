"""
龙岩市公共资源交易中心爬虫 (v3 - 全覆盖)
=======================================
从首页多分类抓取体育类公告，含详情提取
"""

import re
import logging
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from config import SPORTS_KEYWORDS, REQUEST_DELAY
from crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)


class LyGgzyCrawler(BaseCrawler):
    """龙岩市公共资源交易中心爬虫"""

    site_name: str = "龙岩市公共资源交易中心"
    site_url: str = "https://ggzy.longyan.gov.cn"
    platform_type: str = "government"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    # 只关注这些分类（工程建设招标 + 政府采购 + 中标结果）
    CATEGORY_FILTER = ["gcjs", "zqcg"]

    def __init__(self):
        super().__init__()
        import requests
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self._seen_urls = set()

    def crawl(self, keyword: str = "体育", city: str = None) -> int:
        """主入口"""
        logger.info(f"\n{'='*50}")
        logger.info(f"🏙️  {self.site_name}: 关键词={keyword}")
        logger.info(f"{'='*50}")

        # 1. 获取首页
        try:
            import urllib3
            urllib3.disable_warnings()
            r = self.session.get(self.site_url, timeout=30, verify=False)
            r.encoding = r.apparent_encoding or "utf-8"
            if r.status_code != 200:
                logger.error(f"首页访问失败: HTTP {r.status_code}")
                return 0
            soup = BeautifulSoup(r.text, "lxml")
        except Exception as e:
            logger.error(f"首页访问异常: {e}")
            return 0

        # 2. 收集所有公告链接（按分类过滤）
        all_items = self._collect_announce_items(soup)
        logger.info(f"📎 发现 {len(all_items)} 个公告链接（已过滤分类）")

        # 3. 逐个检查 + 提取详情
        sports_found = 0
        for i, item in enumerate(all_items):
            title = item["title"]
            if not self.has_keyword(title, SPORTS_KEYWORDS):
                continue

            sports_found += 1
            url = item["url"]
            logger.info(f"  [{sports_found}] {title[:80]}")

            # 获取详情
            detail = self._fetch_detail(url)
            self.delay(REQUEST_DELAY * 0.7)

            proc_method = self._detect_method(title + detail.get("body", ""))
            budget = self._extract_budget(detail.get("body", ""))
            region = self._extract_region(detail.get("body", ""))
            deadline = self._extract_deadline(detail.get("body", ""))
            proc_entity = self._extract_entity(detail.get("body", ""))

            record = {
                "title": title[:200],
                "url": url,
                "source": self.site_name,
                "category": item.get("category", "体育类"),
                "region": region or "龙岩市",
                "procurement_method": proc_method,
                "procuring_entity": proc_entity,
                "publish_date": item.get("date", ""),
                "deadline": deadline,
                "budget_amount": budget,
                "qualification": detail.get("qualification", ""),
                "requirements": detail.get("requirements", ""),
            }

            self.save(record)

        self.log_stats()
        logger.info(f"\n✅ 龙岩站: 共扫描 {len(all_items)} 条，命中 {sports_found} 条体育类")
        return sports_found

    def _collect_announce_items(self, soup) -> list:
        """从首页收集公告项（含标题、URL、分类、日期）"""
        items = []
        for a in soup.find_all("a", href=True):
            href = a.get("href", "").strip()
            text = a.get_text(strip=True)

            # 只保留公告详情链接 (/lyztb/xxx/...html)
            if not href.endswith(".html") or not href.startswith("/lyztb/"):
                continue
            if len(text) < 8:
                continue
            if href in self._seen_urls:
                continue
            self._seen_urls.add(href)

            # 分类过滤：只看 gcjs（工程建设）和 zqcg（政府采购）
            path_parts = href.split("/")
            if not any(f in path_parts for f in self.CATEGORY_FILTER):
                continue

            # 提取日期（从 URL 路径中：/20260627/...）
            date_match = re.search(r"/(\d{8})/", href)
            item_date = ""
            if date_match:
                date_str = date_match.group(1)
                try:
                    item_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                except:
                    pass

            # 推断分类名
            category = "体育类/工程建设"
            if "zqcg" in href:
                if "001" in href.split("/")[-3] if len(href.split("/")) >= 3 else "":
                    category = "体育类/政府采购-预公告"
                elif "002" in href:
                    category = "体育类/政府采购-招标"
                elif "003" in href:
                    category = "体育类/政府采购-中标"
                else:
                    category = "体育类/政府采购"

            if "001" in path_parts:
                category = "体育类/招标公告"
            elif "002" in path_parts:
                category = "体育类/澄清答疑"
            elif "004" in path_parts:
                category = "体育类/中标公示"

            items.append({
                "title": text,
                "url": urljoin(self.site_url, href),
                "date": item_date,
                "category": category,
                "path": href,
            })

        return items

    def _fetch_detail(self, url: str) -> dict:
        """获取详情页"""
        result = {"body": "", "qualification": "", "requirements": ""}
        try:
            import urllib3
            urllib3.disable_warnings()
            r = self.session.get(url, timeout=30, verify=False)
            r.encoding = r.apparent_encoding or "utf-8"
            if r.status_code != 200:
                return result

            soup = BeautifulSoup(r.text, "lxml")

            # 正文区域（包含龙岩特有的 .substance.ewb-article-info）
            for sel in [".substance", ".ewb-article-info", ".article-content",
                        ".content", "#content", ".info-content", ".detail-content"]:
                content = soup.select_one(sel)
                if content:
                    break
            if not content:
                content = soup.find("body")

            text = content.get_text(separator="\n", strip=True) if content else r.text
            result["body"] = text

            lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 3]

            # 资质要求：先按段落标签精确提取，再按文本行兜底
            qual_parts = []
            # 方法1：从 .substance 中找含"资格"的 <p> 标签
            if content:
                for p_tag in content.find_all("p"):
                    p_text = p_tag.get_text(strip=True)
                    if any(kw in p_text for kw in ["资格要求", "资质要求", "投标人资格",
                                                     "资格条件", "供应商资格", "申请人资格",
                                                     "特定资格", "资格审查"]):
                        # 收集该段落及后续相关段落
                        qual_parts.append(p_text)
                        # 找下一个兄弟节点（可能是连续的 p 标签）
                        for sibling in p_tag.find_next_siblings("p", limit=10):
                            s_text = sibling.get_text(strip=True)
                            if s_text and len(s_text) > 10:
                                qual_parts.append(s_text)
                        break

            # 方法2：兜底——按文本行匹配
            if not qual_parts:
                qual_kws = ["资格要求", "资质要求", "投标人资格", "资格条件",
                            "供应商资格", "申请人资格", "特定资格要求"]
                for i, line in enumerate(lines):
                    if any(kw in line for kw in qual_kws):
                        qual_parts = lines[i:min(i + 20, len(lines))]
                        break

            if qual_parts:
                result["qualification"] = "\n".join(qual_parts)[:3000]

            result["requirements"] = "\n".join(lines[:60])[:5000]

        except Exception as e:
            logger.debug(f"详情获取失败: {url[:80]} - {e}")

        return result

    def _extract_region(self, text: str) -> str:
        """提取区县"""
        districts = ["新罗区", "永定区", "长汀县", "上杭县", "武平县",
                     "连城县", "漳平市"]
        for d in districts:
            if d in text:
                return d
        return "龙岩市"

    def _extract_budget(self, text: str) -> str:
        for line in text.split("\n"):
            if any(kw in line for kw in ["预算金额", "采购预算", "最高限价",
                                          "项目预算", "预算总价"]):
                nums = re.findall(r'\d+[\d,]*\.?\d*\s*万元?', line)
                return nums[0] if nums else line.strip()[:100]
        return ""

    def _detect_method(self, text: str) -> str:
        for m in ["公开招标", "竞争性磋商", "竞争性谈判", "单一来源", "询价", "邀请招标"]:
            if m in text:
                return m
        return ""

    def _extract_deadline(self, text: str) -> str:
        for line in text.split("\n"):
            if any(kw in line for kw in ["截止时间", "开标时间", "投标截止",
                                          "递交截止", "提交截止"]):
                m = re.search(r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日\s]?\d{1,2}:\d{2})', line)
                return m.group(1) if m else line.strip()[:80]
        return ""

    def _extract_entity(self, text: str) -> str:
        for line in text.split("\n"):
            for kw in ["采购人", "采购单位", "招标人", "招标单位", "业主单位", "采购人名称"]:
                if kw in line:
                    val = line.split("：")[-1].split(":")[-1].strip()
                    return val[:80] if val else line.strip()[:80]
        return ""
