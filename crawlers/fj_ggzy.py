"""
福建省公共资源交易平台爬虫 (ggzyfw.fujian.gov.cn)
================================================
覆盖福建省全省的公共资源交易（工程建设+政府采购+矿产土地）
使用 Playwright 处理 Vue SPA
"""

import re
import logging
from urllib.parse import urljoin

from config import (
    SPORTS_KEYWORDS, REQUEST_DELAY, PAGE_LOAD_TIMEOUT,
    MAX_PAGES, BROWSER_HEADLESS, FUJIAN_CITIES,
)
from crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)


class FjGgzyCrawler(BaseCrawler):
    """福建省公共资源交易平台爬虫"""

    site_name: str = "福建省公共资源交易平台"
    site_url: str = "https://ggzyfw.fujian.gov.cn"
    platform_type: str = "government"

    # 公告类型导航（首页分类菜单）
    ANNOUNCE_TYPES = [
        "工程建设", "政府采购", "土地使用权", "矿业权",
        "国有产权", "其他交易",
    ]

    def __init__(self):
        super().__init__()
        self.browser = None
        self.context = None
        self.page = None
        self._pw = None

    async def start(self):
        from playwright.async_api import async_playwright
        self._pw = await async_playwright().start()
        self.browser = await self._pw.chromium.launch(
            headless=BROWSER_HEADLESS,
            args=["--ignore-certificate-errors"]
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1560, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
        )
        self.page = await self.context.new_page()
        logger.info(f"🖥️  {self.site_name} 浏览器已启动")

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self._pw:
            await self._pw.stop()

    async def crawl(self, keyword: str = "体育", city: str = None) -> int:
        """搜索并提取结果"""
        logger.info(f"\n{'='*50}")
        logger.info(f"🏙️  {self.site_name}: 关键词={keyword}")
        logger.info(f"{'='*50}")

        total_new = 0

        # 1. 访问首页
        await self.page.goto(self.site_url, timeout=PAGE_LOAD_TIMEOUT,
                            wait_until="domcontentloaded")
        await self.page.wait_for_timeout(5000)

        # 2. 找搜索框
        search_input = await self._find_search_input()
        if not search_input:
            logger.error("找不到搜索框，尝试从公告列表直接扫描")
            return await self._crawl_from_homepage(keyword)

        await search_input.fill(keyword)
        await self.page.wait_for_timeout(500)
        await search_input.press("Enter")
        await self.page.wait_for_timeout(5000)
        await self.page.wait_for_load_state("networkidle", timeout=20000)

        # 3. 逐页提取
        for page_num in range(1, min(MAX_PAGES, 20)):
            logger.info(f"📄 第 {page_num} 页")
            new_count = await self._extract_page(keyword)
            total_new += new_count

            has_next = await self._go_next_page()
            if not has_next or new_count == 0:
                break
            self.delay(REQUEST_DELAY)

        self.log_stats()
        return total_new

    async def _crawl_from_homepage(self, keyword: str) -> int:
        """兜底：从首页扫描公告标题"""
        logger.info("使用首页扫描模式...")
        total = 0
        try:
            body = await self.page.inner_text("body") or ""
            lines = [l.strip() for l in body.split("\n") if l.strip() and len(l.strip()) > 10]

            # 找所有链接
            links = await self.page.query_selector_all("a[href*='bulletin'], a[href*='announce'], a[href*='detail']")
            for link in links:
                try:
                    text = (await link.inner_text()).strip()
                    href = await link.get_attribute("href") or ""
                    if not self.has_keyword(text, SPORTS_KEYWORDS):
                        continue
                    if not any(p in text for p in ["福建"] + FUJIAN_CITIES):
                        continue

                    url = urljoin(self.site_url, href)
                    date = self.extract_date(text)
                    record = {
                        "title": text[:200],
                        "url": url,
                        "region": self._extract_fj_city(text),
                        "publish_date": date,
                    }
                    if self.save(record):
                        total += 1
                        logger.info(f"  ✅ {text[:60]}")
                except:
                    continue
        except Exception as e:
            logger.error(f"首页扫描异常: {e}")

        self.log_stats()
        return total

    async def _find_search_input(self):
        """找搜索框"""
        for sel in [
            "input[placeholder*='搜索']",
            "input[placeholder*='标题']",
            "input[type='text']",
            ".search-input",
        ]:
            el = await self.page.query_selector(sel)
            if el and await el.is_visible():
                return el
        return None

    async def _extract_page(self, keyword: str) -> int:
        """提取一页"""
        new_count = 0
        try:
            await self.page.wait_for_timeout(2000)
            items = await self.page.query_selector_all(
                ".list-item, [class*='list'] li, table tbody tr, .result-item"
            )
            for item in items:
                try:
                    text = (await item.inner_text()).strip()
                    if not self.has_keyword(text, SPORTS_KEYWORDS):
                        continue
                    if len(text) < 10:
                        continue

                    link = await item.query_selector("a[href]")
                    url = ""
                    if link:
                        href = await link.get_attribute("href") or ""
                        url = urljoin(self.site_url, href)

                    record = {
                        "title": text[:200],
                        "url": url,
                        "region": self._extract_fj_city(text),
                        "procurement_method": self._detect_method(text),
                        "publish_date": self.extract_date(text),
                    }

                    if url:
                        qual, req = await self._fetch_detail(url)
                        record["qualification"] = qual
                        record["requirements"] = req

                    if self.save(record):
                        new_count += 1
                except:
                    continue

            logger.info(f"✅ 本页新增 {new_count} 条")
        except Exception as e:
            logger.error(f"页面提取异常: {e}")
        return new_count

    async def _fetch_detail(self, url: str) -> tuple:
        """获取详情"""
        try:
            dp = await self.context.new_page()
            await dp.goto(url, timeout=PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")
            await dp.wait_for_timeout(2000)
            body = await dp.inner_text("body") or ""
            lines = [l.strip() for l in body.split("\n") if len(l.strip()) > 3]

            qual = ""
            for i, line in enumerate(lines):
                if any(kw in line for kw in ["资格要求", "资质要求", "投标人资格"]):
                    qual = "\n".join(lines[i:min(i + 20, len(lines))])
                    break

            req = "\n".join(lines[:60])[:5000]
            await dp.close()
            self.delay(REQUEST_DELAY * 0.5)
            return (qual[:3000], req)
        except:
            return ("", "")

    async def _go_next_page(self) -> bool:
        """翻页"""
        for sel in [
            "button:has-text('下一页')",
            ".pagination .next",
            ".el-pagination .btn-next",
        ]:
            btn = await self.page.query_selector(sel)
            if btn:
                disabled = await btn.get_attribute("disabled")
                if disabled:
                    continue
                await btn.click()
                await self.page.wait_for_timeout(3000)
                await self.page.wait_for_load_state("networkidle", timeout=15000)
                return True
        return False

    def _extract_fj_city(self, text: str) -> str:
        """提取福建城市"""
        for c in FUJIAN_CITIES:
            if c in text:
                return c
        return "福建省"

    def _detect_method(self, text: str) -> str:
        for m in ["公开招标", "竞争性磋商", "竞争性谈判", "单一来源", "询价"]:
            if m in text:
                return m
        return ""
