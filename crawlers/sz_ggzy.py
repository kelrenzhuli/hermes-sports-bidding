"""
深圳公共资源交易中心爬虫
======================
继承 BaseCrawler，抓取 szggzy.com 的体育类招投标信息
"""

import re
import time
import logging
from datetime import datetime
from urllib.parse import urljoin

from config import (
    SPORTS_KEYWORDS, REQUEST_DELAY, PAGE_LOAD_TIMEOUT,
    MAX_PAGES, BROWSER_HEADLESS,
)
from crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)


class SzGgzyCrawler(BaseCrawler):
    """深圳公共资源交易中心爬虫"""

    site_name: str = "深圳公共资源交易中心"
    site_url: str = "https://www.szggzy.com"
    platform_type: str = "government"

    def __init__(self):
        super().__init__()
        self.browser = None
        self.context = None
        self.page = None
        self._pw = None

    # ═══ 浏览器生命周期 ═══

    async def start(self):
        from playwright.async_api import async_playwright
        self._pw = await async_playwright().start()
        self.browser = await self._pw.chromium.launch(headless=BROWSER_HEADLESS)
        self.context = await self.browser.new_context(
            viewport={"width": 1560, "height": 900},
        )
        self.page = await self.context.new_page()
        logger.info("🖥️  深圳站浏览器已启动")

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self._pw:
            await self._pw.stop()

    # ═══ 核心爬取 ═══

    async def crawl(self, keyword: str = "体育赛事", city: str = None) -> int:
        """搜索关键词并抓取所有结果（含详情页）"""
        logger.info(f"\n{'='*50}")
        logger.info(f"🏙️  深圳站: 关键词={keyword}")
        logger.info(f"{'='*50}")

        total_new = 0

        # 1. 访问首页
        await self.page.goto(
            f"{self.site_url}/static/index.html",
            timeout=30000, wait_until="load"
        )
        await self.page.wait_for_timeout(5000)

        # 2. 搜索
        search_box = await self.page.query_selector("input[placeholder*='关键词']")
        if search_box:
            await search_box.fill(keyword)
            await self.page.wait_for_timeout(500)
            search_btn = await self.page.query_selector(
                ".search-box button, button:has-text('搜索')"
            )
            if search_btn:
                await search_btn.click()
            else:
                await search_box.press("Enter")
            await self.page.wait_for_timeout(5000)
            await self.page.wait_for_load_state("networkidle", timeout=30000)

        # 3. 提取详情页链接
        detail_urls = await self._extract_detail_urls()
        logger.info(f"📎 找到 {len(detail_urls)} 条结果")

        # 4. 逐个访问详情页
        for i, url in enumerate(detail_urls[:MAX_PAGES]):
            try:
                record = await self._parse_detail_page(url, keyword)
                if not record:
                    continue
                # 体育关键词过滤
                title = record.get("title", "")
                if not self.has_keyword(title, SPORTS_KEYWORDS):
                    continue
                if self.save(record):
                    total_new += 1
                    logger.info(f"  [{i+1}/{len(detail_urls)}] ✅ {title[:50]}")
                self.delay(REQUEST_DELAY * 0.5)
            except Exception as e:
                logger.warning(f"  [{i+1}] ❌ {url[:60]}... - {e}")

        # 5. 翻页
        page_num = 1
        while page_num < MAX_PAGES:
            has_next = await self._go_next_page()
            if not has_next:
                break
            page_num += 1
            await self.page.wait_for_timeout(3000)

            more_urls = await self._extract_detail_urls()
            for url in more_urls[:MAX_PAGES]:
                try:
                    record = await self._parse_detail_page(url, keyword)
                    if not record:
                        continue
                    if not self.has_keyword(record.get("title", ""), SPORTS_KEYWORDS):
                        continue
                    if self.save(record):
                        total_new += 1
                    self.delay(REQUEST_DELAY * 0.5)
                except Exception as e:
                    logger.warning(f"  ❌ {url[:60]}... - {e}")

        self.log_stats()
        return total_new

    # ═══ 内部方法 ═══

    async def _extract_detail_urls(self) -> list:
        """提取当前页所有详情链接"""
        urls = []
        els = await self.page.query_selector_all(
            "[onclick*='onZfcg'], [onclick*='gsgg'], a[href*='gsgg']"
        )
        seen = set()
        for el in els:
            onclick = await el.get_attribute("onclick") or ""
            href = await el.get_attribute("href") or ""
            for u in re.findall(r"http[s]?://[^'\"]+", onclick + href):
                if "gsgg" in u and u not in seen:
                    seen.add(u)
                    urls.append(u)
            if href.startswith("http") and "gsgg" in href and href not in seen:
                seen.add(href)
                urls.append(href)
        return urls

    async def _parse_detail_page(self, url: str, keyword: str) -> dict:
        """访问详情页提取完整信息"""
        detail_page = await self.context.new_page()
        try:
            await detail_page.goto(url, timeout=PAGE_LOAD_TIMEOUT,
                                   wait_until="domcontentloaded")
            await detail_page.wait_for_timeout(3000)
            body = await detail_page.inner_text("body") or ""
            lines = [l.strip() for l in body.split("\n") if l.strip()]

            # 标题
            title = ""
            for h_tag in ["h1", "h2", "h3", "h4"]:
                h = await detail_page.query_selector(h_tag)
                if h:
                    t = (await h.inner_text()).strip()
                    if "公告" in t and len(t) > 10:
                        title = t
                        break
            if not title:
                longest = ""
                for l in lines:
                    if "公告" in l and len(l) > len(longest) and len(l) < 200:
                        longest = l
                title = longest

            # 日期
            publish_date = self.extract_date("\n".join(lines[:20]))

            # 资质要求
            qualification = ""
            in_qual = False
            qual_lines = []
            qual_kws = ["资格要求", "资质要求", "投标人资格", "资格条件",
                        "供应商资格", "申请人资格", "特定资格"]
            for l in lines:
                if any(kw in l for kw in qual_kws):
                    in_qual = True
                if in_qual:
                    qual_lines.append(l)
                    if len(qual_lines) > 40:
                        break
            if qual_lines:
                qualification = "\n".join(qual_lines[:20])

            # 预算金额
            budget_amount = ""
            amount_kws = ["预算金额", "采购预算", "最高限价", "项目预算",
                          "资金来源", "合同估价"]
            for l in lines:
                for ak in amount_kws:
                    if ak in l:
                        nums = re.findall(r'\d+[\d,]*\.?\d*\s*万元?', l)
                        budget_amount = f"{ak}: {nums[0]}" if nums else l[:100]
                        break
                if budget_amount:
                    break

            # 截止时间
            deadline = ""
            deadline_kws = ["截止时间", "开标时间", "投标截止", "递交截止",
                            "提交截止", "响应文件提交截止"]
            for l in lines:
                for dk in deadline_kws:
                    if dk in l:
                        m = re.search(
                            r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}[\s日]\d{1,2}:\d{2})', l
                        )
                        deadline = m.group(1) if m else l[:80]
                        break
                if deadline:
                    break

            # 地区
            region = "深圳市"
            for l in lines:
                m = re.search(
                    r'(罗湖区|福田区|南山区|宝安区|龙岗区|龙华区|坪山区|光明区|盐田区|大鹏新区)', l
                )
                if m:
                    region = m.group(1)
                    break

            # 采购方式
            procurement_method = ""
            method_kws = ["公开招标", "竞争性磋商", "竞争性谈判", "单一来源",
                          "询价", "邀请招标"]
            for l in lines:
                for mk in method_kws:
                    if mk in l:
                        procurement_method = mk
                        break
                if procurement_method:
                    break

            record = {
                "title": title,
                "url": url,
                "region": region,
                "procurement_method": procurement_method,
                "procuring_entity": "",
                "publish_date": publish_date,
                "deadline": deadline,
                "budget_amount": budget_amount,
                "requirements": "\n".join(lines[:80])[:5000],
                "qualification": qualification,
            }
            return record
        finally:
            await detail_page.close()

    async def _go_next_page(self) -> bool:
        """翻页"""
        for sel in [".js-page-next", "a:has-text('下一页')", "[class*='next']"]:
            btn = await self.page.query_selector(sel)
            if btn:
                disabled = await btn.get_attribute("disabled") or ""
                if "disabled" in disabled:
                    return False
                await btn.click()
                await self.page.wait_for_timeout(3000)
                await self.page.wait_for_load_state("networkidle", timeout=15000)
                return True
        return False
