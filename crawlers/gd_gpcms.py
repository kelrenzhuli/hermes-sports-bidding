"""
GPCMS 政府采购平台爬虫（广东 + 福建通用）
=====================================
继承 BaseCrawler，使用 Playwright 处理 SPA + 验证码
"""

import re
import time
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from config import (
    SPORTS_KEYWORDS, REQUEST_DELAY, PAGE_LOAD_TIMEOUT,
    MAX_PAGES, BROWSER_HEADLESS,
)
from crawlers.base import BaseCrawler
from captcha_solver import trigger_captcha_and_solve

logger = logging.getLogger(__name__)


class GpcmCrawler(BaseCrawler):
    """
    GPCMS 政府采购平台爬虫

    适用站点：
        - 广东：https://gdgpo.czt.gd.gov.cn
        - 福建：https://zfcg.czt.fujian.gov.cn
    """

    site_name: str = "GPCMS"
    site_url: str = ""
    platform_type: str = "government"

    def __init__(self, base_url: str, site_name: str):
        super().__init__()
        self.base_url = base_url
        self.site_name = site_name
        self.site_url = base_url
        self.browser = None
        self.context = None
        self.page = None
        self._pw = None
        self._current_keyword = "体育"

    # ═══ 浏览器生命周期 ═══

    async def start(self):
        """启动浏览器"""
        from playwright.async_api import async_playwright
        self._pw = await async_playwright().start()
        self.browser = await self._pw.chromium.launch(headless=BROWSER_HEADLESS)
        self.context = await self.browser.new_context(
            viewport={"width": 1560, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
        )
        self.page = await self.context.new_page()
        logger.info(f"🖥️  浏览器已启动: {self.site_name}")

    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self._pw:
            await self._pw.stop()
        logger.info(f"🖥️  浏览器已关闭: {self.site_name}")

    # ═══ 核心爬取逻辑 ═══

    async def crawl(self, keyword: str = "体育", city: str = None) -> int:
        """
        爬取指定城市 + 关键词的招标公告
        返回新增记录数
        """
        city = city or "省本级"
        logger.info(f"\n{'='*50}")
        logger.info(f"🏙️  {self.site_name} → 区划={city}, 关键词={keyword}")
        logger.info(f"{'='*50}")

        self._current_keyword = keyword

        # 1. 导航到公告信息页
        search_url = f"{self.base_url}/maincms-web/xmgg"
        await self._safe_goto(search_url)
        await self.page.wait_for_timeout(5000)

        # 2. 填写搜索表单
        await self._fill_search_form(keyword, city)
        self.delay(REQUEST_DELAY)

        # 3. 验证码 + 提交
        captcha_ok = await trigger_captcha_and_solve(self.page, keyword)
        if not captcha_ok:
            logger.error(f"❌ {city}: 验证码无法通过")
            return 0

        # 4. 逐页提取
        total_new = 0
        for page_num in range(1, MAX_PAGES + 1):
            logger.info(f"📄 第 {page_num} 页: {city}")
            new_count = await self._extract_current_page(city, keyword)
            total_new += new_count

            has_next = await self._go_next_page()
            if not has_next:
                logger.info(f"✅ {city}: 已无更多页面")
                break
            self.delay(REQUEST_DELAY)

        logger.info(f"📊 {city}: 共爬取 {page_num} 页, 新增 {total_new} 条")
        return total_new

    async def crawl_all_cities(self, cities: list, keyword: str = "体育") -> int:
        """爬取多个城市"""
        total = 0
        await self.start()
        try:
            for city in cities:
                n = await self.crawl(keyword, city)
                total += n
                self.delay(REQUEST_DELAY * 2)
        finally:
            await self.close()
        self.log_stats()
        return total

    # ═══ 内部方法 ═══

    async def _safe_goto(self, url: str):
        try:
            await self.page.goto(url, timeout=PAGE_LOAD_TIMEOUT, wait_until="load")
            logger.info(f"🌐 {url}")
        except Exception as e:
            logger.warning(f"导航超时: {url} - {e}")

    async def _fill_search_form(self, keyword: str, city: str):
        """填写搜索表单"""
        try:
            title_input = await self.page.query_selector(
                "input[placeholder*='标题'], input[placeholder*='查询内容']"
            )
            if title_input:
                await title_input.fill(keyword)
                logger.info(f"✅ 已填写关键词: {keyword}")

            if city and city != "省本级":
                await self._select_city(city)
        except Exception as e:
            logger.warning(f"填写表单异常: {e}")

    async def _select_city(self, city: str):
        """在下拉菜单中选择城市"""
        try:
            region_trigger = await self.page.query_selector(
                "[class*='el-select'] input, [class*='select'] input"
            )
            if not region_trigger:
                region_trigger = await self.page.query_selector(
                    "input[value*='省本级']"
                )
            if region_trigger:
                await region_trigger.click()
                await self.page.wait_for_timeout(800)
                city_option = await self.page.query_selector(
                    f"[class*='option']:has-text('{city}'), "
                    f".el-select-dropdown li:has-text('{city}')"
                )
                if city_option:
                    await city_option.click()
                    await self.page.wait_for_timeout(500)
                    # 关闭下拉框，防止遮挡查询按钮
                    await self.page.keyboard.press("Escape")
                    await self.page.wait_for_timeout(300)
                    logger.info(f"✅ 已选择区划: {city}")
                else:
                    logger.warning(f"⚠️ 未找到区划选项: {city}")
        except Exception as e:
            logger.warning(f"选择城市异常: {e}")

    async def _extract_current_page(self, city: str, keyword: str) -> int:
        """提取当前页所有行 — Element UI 表格：点击行导航，提取详情后返回"""
        new_count = 0
        try:
            await self.page.wait_for_timeout(2000)
            rows = await self.page.query_selector_all(
                ".el-table__body-wrapper tbody tr, table tbody tr"
            )
            if not rows:
                no_data = await self.page.query_selector("text=暂无数据")
                if no_data:
                    logger.info(f"📭 {city}: 暂无数据")
                return 0

            logger.info(f"📊 当前页 {len(rows)} 条记录")
            list_url = self.page.url  # 保存列表页 URL 用于返回

            for row_idx, row in enumerate(rows):
                # 解析行文本
                cells = await row.query_selector_all("td")
                titles = []
                for cell in cells:
                    t = (await cell.inner_text()).strip()
                    titles.append(t)

                if len(titles) < 3:
                    continue

                title = titles[3] if len(titles) >= 4 else titles[0]
                if not any(kw in title for kw in SPORTS_KEYWORDS):
                    continue

                record = {
                    "title": title[:200],
                    "region": titles[0] if len(titles) >= 1 else "",
                    "procurement_method": titles[1] if len(titles) >= 2 else "",
                    "procuring_entity": titles[2] if len(titles) >= 3 else "",
                    "publish_date": titles[4] if len(titles) >= 5 else titles[-1],
                    "source": self.site_name,
                    "category": "体育类",
                }

                # 点击行 → 获取详情 URL
                try:
                    # 监听新页面
                    async with self.context.expect_page(timeout=10000) as new_page_info:
                        await row.click()
                        # 可能打开新标签页或原地导航
                        try:
                            detail_page = await new_page_info.value
                            detail_url = detail_page.url
                            await detail_page.wait_for_timeout(2000)
                            detail = await self._extract_from_page(detail_page)
                            await detail_page.close()
                        except:
                            await self.page.wait_for_timeout(2000)
                            detail_url = self.page.url
                            detail = await self._extract_from_page(self.page)
                            await self.page.goto(list_url, timeout=20000,
                                                wait_until="domcontentloaded")
                            await self.page.wait_for_timeout(1000)

                    record["url"] = detail_url
                    record["qualification"] = detail.get("qualification", "")
                    record["requirements"] = detail.get("requirements", "")
                    record["budget_amount"] = detail.get("budget_amount", "")
                    record["deadline"] = detail.get("deadline", "")
                except Exception as e:
                    logger.debug(f"  行{row_idx} 详情提取失败: {e}")
                    record["url"] = ""  # 至少保存基本信息

                self.save(record)
                new_count += 1
                self.delay(REQUEST_DELAY * 0.5)

            logger.info(f"✅ 本页新增 {new_count} 条体育类")
            return new_count
        except Exception as e:
            logger.error(f"页面提取异常: {e}")
            return 0

    async def _extract_from_page(self, page) -> dict:
        """从已打开的详情页提取所有字段"""
        result = {"qualification": "", "requirements": "", "budget_amount": "", "deadline": ""}
        try:
            page_text = await page.inner_text("body") or ""
            lines = [l.strip() for l in page_text.split("\n") if len(l.strip()) > 3]

            # 资质
            qual_kws = ["申请人的资格要求", "投标人资格要求", "供应商资格要求",
                       "投标人的资格要求", "资质要求", "资格条件"]
            qual_parts = []
            for i, line in enumerate(lines):
                if any(kw in line for kw in qual_kws):
                    qual_parts = lines[i:min(i + 30, len(lines))]
                    break
            if qual_parts:
                result["qualification"] = "\n".join(qual_parts)[:3000]

            # 正文（全量，不再截断50行）
            result["requirements"] = "\n".join(lines[:200])[:8000]

            # 预算金额：找"预算金额(万元)"表格行
            import re
            for i, line in enumerate(lines):
                if "预算金额" in line and ("万元" in line or "采购需求" in line):
                    # 下一行通常是数据行
                    for j in range(i + 1, min(i + 10, len(lines))):
                        next_line = lines[j]
                        nums = re.findall(r'(\d+[\d,]*\.?\d*)', next_line)
                        if nums and len(next_line) > 10:
                            result["budget_amount"] = f"{nums[0]}万元"
                            break
                    if result["budget_amount"]:
                        break
            # 兜底：搜索"预算"+"万元"模式
            if not result["budget_amount"]:
                for line in lines:
                    m = re.search(r'预算[金额]*[：:]\s*(\d+[\d,]*\.?\d*)\s*万元?', line)
                    if m:
                        result["budget_amount"] = f"{m.group(1)}万元"
                        break

            # 截止日期：多模式匹配
            deadline_patterns = [
                r'(?:截止时间|开标时间|投标截止|响应文件.*?截止)[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})',
                r'(?:截止时间|开标时间)[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日\s*\d{1,2}:\d{2})',
                r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}).*(?:截止|开标)',
            ]
            for pat in deadline_patterns:
                for line in lines:
                    m = re.search(pat, line)
                    if m:
                        result["deadline"] = m.group(1)
                        break
                if result["deadline"]:
                    break

        except Exception as e:
            logger.debug(f"提取详情异常: {e}")
        return result
    async def _go_next_page(self) -> bool:
        """翻页"""
        try:
            selectors = [
                "button:has-text('下一页')",
                ".el-pagination .btn-next",
                "li:has-text('下一页')",
            ]
            for sel in selectors:
                btn = await self.page.query_selector(sel)
                if btn:
                    disabled = await btn.get_attribute("disabled")
                    classes = await btn.get_attribute("class") or ""
                    if disabled or "disabled" in classes:
                        return False
                    await btn.click()
                    await self.page.wait_for_timeout(3000)
                    await self.page.wait_for_load_state("networkidle", timeout=15000)
                    return True
            return False
        except Exception as e:
            logger.warning(f"翻页异常: {e}")
            return False
