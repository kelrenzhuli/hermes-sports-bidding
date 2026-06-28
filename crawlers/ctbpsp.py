"""
中国招标投标公共服务平台爬虫 (ctbpsp.com) — 已暂停
====================================================
状态: ❌ 暂时无法使用

原因:
  1. API 响应全部加密 (JwdsCjMM05e4... 格式)
  2. 使用网易易盾 (NECaptcha) 商业验证码
  3. 需要逆向工程 app.xxx.js 中的解密逻辑

发现的 API 端点 (供后续参考):
  - /cutominfoapi/labelRelationQuery/uid/0/keyword/{kw}/start/{offset}/offset/20
  - /cutominfoapi/labelCompletionQuery/uid/0/keyword/{kw}
  - /cutominfoapi/queryCategory/tag/{kw}
  - /cutominfoapi/getSearchCount
  - /cutominfoapi/categoryTreeQuery/categoryId/{id}
  - /cutominfoapi/platformInfo

平台价值: ⭐⭐⭐⭐⭐ 国家级, 覆盖全国所有省份
破解难度: ⭐⭐⭐⭐⭐ 需要 JS 逆向 + 绕过网易易盾

建议: 等有 JS 逆向能力时再攻克
"""

import re
import time
import logging
from datetime import datetime
from urllib.parse import urljoin

from config import (
    SPORTS_KEYWORDS, REQUEST_DELAY, PAGE_LOAD_TIMEOUT,
    MAX_PAGES, BROWSER_HEADLESS,
    GUANGDONG_CITIES, FUJIAN_CITIES,
)
from crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)

# 目标省份（用于结果过滤）
TARGET_PROVINCES = ["广东", "福建"]


class CtbpspCrawler(BaseCrawler):
    """中国招标投标公共服务平台爬虫"""

    site_name: str = "中国招标投标公共服务平台"
    site_url: str = "https://www.ctbpsp.com"
    platform_type: str = "industry"

    def __init__(self):
        super().__init__()
        self.browser = None
        self.context = None
        self.page = None
        self._pw = None

    async def start(self):
        """启动浏览器"""
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
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
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
        """搜索关键词并提取结果"""
        logger.info(f"\n{'='*50}")
        logger.info(f"🏙️  {self.site_name}: 关键词={keyword}")
        logger.info(f"{'='*50}")

        total_new = 0

        # 1. 访问首页
        await self.page.goto(self.site_url, timeout=PAGE_LOAD_TIMEOUT,
                            wait_until="domcontentloaded")
        await self.page.wait_for_timeout(5000)  # 等 Vue 渲染

        # 2. 搜索
        search_input = await self._find_search_input()
        if not search_input:
            logger.error("找不到搜索框")
            return 0

        await search_input.fill(keyword)
        await self.page.wait_for_timeout(500)
        await search_input.press("Enter")
        await self.page.wait_for_timeout(5000)
        await self.page.wait_for_load_state("networkidle", timeout=20000)

        # 3. 处理可能出现的验证码
        await self._handle_captcha()

        # 4. 逐页提取
        for page_num in range(1, MAX_PAGES + 1):
            logger.info(f"📄 第 {page_num} 页")

            new_count = await self._extract_current_page(keyword)
            if new_count == 0 and page_num >= 3:
                logger.info("连续无结果，停止翻页")
                break
            total_new += new_count

            has_next = await self._go_next_page()
            if not has_next:
                logger.info("已无更多页面")
                break

            self.delay(REQUEST_DELAY)
            await self._handle_captcha()

        self.log_stats()
        return total_new

    async def _find_search_input(self):
        """找到搜索框"""
        selectors = [
            "input[placeholder*='搜索']",
            "input[placeholder*='关键词']",
            "input.search-input",
            ".search-box input[type='text']",
            "input[type='text']",
        ]
        for sel in selectors:
            el = await self.page.query_selector(sel)
            if el and await el.is_visible():
                logger.info(f"✅ 找到搜索框: {sel}")
                return el
        return None

    async def _handle_captcha(self):
        """处理验证码（如果有）"""
        try:
            captcha_img = await self.page.query_selector(
                "img[src*='captcha'], img[src*='verify'], .captcha img"
            )
            if captcha_img and await captcha_img.is_visible():
                logger.warning("⚠️ 需要验证码，尝试 OCR...")
                from captcha_solver import solve_captcha_async
                code = await solve_captcha_async(self.page, retries=2)
                if code:
                    captcha_input = await self.page.query_selector(
                        "input[placeholder*='验证码'], input.captcha-input"
                    )
                    if captcha_input:
                        await captcha_input.fill(code)
                        submit_btn = await self.page.query_selector(
                            "button:has-text('确定'), button:has-text('提交')"
                        )
                        if submit_btn:
                            await submit_btn.click()
                            await self.page.wait_for_timeout(3000)
                            logger.info("✅ 验证码已提交")
                        return True
                logger.warning("⚠️ 验证码处理失败，继续尝试")
        except Exception as e:
            logger.debug(f"验证码处理异常: {e}")
        return False

    async def _extract_current_page(self, keyword: str) -> int:
        """提取当前页面所有结果"""
        new_count = 0
        try:
            await self.page.wait_for_timeout(3000)

            # 查找结果列表项
            items = await self.page.query_selector_all(
                ".result-item, .search-result li, .list-item, "
                "table tbody tr, .el-table__body tr, "
                "[class*='result'] div[class*='item'], .bulletin-item"
            )

            if not items:
                # 尝试从页面文本判断
                body = await self.page.inner_text("body") or ""
                if "暂无数据" in body or "未找到" in body:
                    logger.info("📭 无结果")
                    return 0
                # 降级：找所有含链接的行
                items = await self.page.query_selector_all("a[href*='bulletin'], a[href*='detail']")

            logger.info(f"📊 当前页 {len(items)} 条")

            for item in items:
                record = await self._parse_item(item, keyword)
                if not record:
                    continue

                # 地区过滤
                region = record.get("region", "")
                if region and not any(p in region for p in TARGET_PROVINCES):
                    continue

                # 关键词二次过滤
                title = record.get("title", "")
                if not self.has_keyword(title, SPORTS_KEYWORDS):
                    continue

                # 获取详情
                if record.get("url"):
                    try:
                        qual, req, amount, deadline = await self._fetch_detail(record["url"])
                        record["qualification"] = qual
                        record["requirements"] = req
                        record["budget_amount"] = amount or record.get("budget_amount", "")
                        record["deadline"] = deadline or record.get("deadline", "")
                    except Exception as e:
                        logger.debug(f"详情获取异常: {e}")

                if self.save(record):
                    new_count += 1

            logger.info(f"✅ 本页新增 {new_count} 条 (广东/福建)")
            return new_count

        except Exception as e:
            logger.error(f"页面提取异常: {e}")
            return 0

    async def _parse_item(self, item, keyword: str) -> dict:
        """解析单个结果项"""
        try:
            inner_text = await item.inner_text()
            text = inner_text.strip()

            if len(text) < 10:
                return None

            # 提取标题链接
            link = await item.query_selector("a[href]")
            url = ""
            title = text[:200]
            if link:
                href = await link.get_attribute("href") or ""
                url = urljoin(self.site_url, href)
                link_text = (await link.inner_text()).strip()
                if len(link_text) > 5:
                    title = link_text[:200]

            # 提取日期
            publish_date = self.extract_date(text)

            # 提取地区
            region = ""
            for prov in ["广东", "福建"]:
                if prov in text:
                    region = prov
                    # 尝试提取城市
                    for city in GUANGDONG_CITIES + FUJIAN_CITIES:
                        if city in text:
                            region = city
                            break
                    break

            # 提取采购方式
            proc_method = ""
            for m in ["公开招标", "竞争性磋商", "竞争性谈判", "单一来源", "询价"]:
                if m in text:
                    proc_method = m
                    break

            return {
                "title": title,
                "url": url,
                "region": region,
                "procurement_method": proc_method,
                "publish_date": publish_date,
            }

        except Exception as e:
            logger.debug(f"项解析异常: {e}")
            return None

    async def _fetch_detail(self, url: str) -> tuple:
        """获取详情页"""
        try:
            detail_page = await self.context.new_page()
            await detail_page.goto(url, timeout=PAGE_LOAD_TIMEOUT,
                                   wait_until="domcontentloaded")
            await detail_page.wait_for_timeout(3000)

            body = await detail_page.inner_text("body") or ""
            lines = [l.strip() for l in body.split("\n") if len(l.strip()) > 3]

            # 资质要求
            qualification = ""
            qual_kws = ["资格要求", "资质要求", "投标人资格", "资格条件",
                        "供应商资格", "申请人资格", "特定资格"]
            for i, line in enumerate(lines):
                if any(kw in line for kw in qual_kws):
                    qualification = "\n".join(lines[i:min(i + 20, len(lines))])
                    break

            # 预算金额
            amount = ""
            for line in lines:
                if any(kw in line for kw in ["预算金额", "采购预算", "最高限价"]):
                    nums = re.findall(r'\d+[\d,]*\.?\d*\s*万元?', line)
                    amount = nums[0] if nums else line[:100]
                    break

            # 截止时间
            deadline = ""
            for line in lines:
                if any(kw in line for kw in ["截止时间", "开标时间", "投标截止"]):
                    m = re.search(r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日\s]?\d{1,2}:\d{2})', line)
                    deadline = m.group(1) if m else line[:80]
                    break

            requirements = "\n".join(lines[:60])[:5000]
            await detail_page.close()
            self.delay(REQUEST_DELAY * 0.5)
            return (qualification[:3000], requirements, amount, deadline)

        except Exception as e:
            logger.debug(f"详情获取失败: {url[:80]} - {e}")
            return ("", "", "", "")

    async def _go_next_page(self) -> bool:
        """翻页"""
        for sel in [
            "button:has-text('下一页')",
            "a:has-text('>')",
            ".pagination .next",
            ".el-pagination .btn-next",
            "[class*='pagination'] li:last-child",
        ]:
            btn = await self.page.query_selector(sel)
            if btn:
                disabled = await btn.get_attribute("disabled")
                classes = await btn.get_attribute("class") or ""
                if disabled or "disabled" in classes or "active" in classes:
                    continue
                await btn.click()
                await self.page.wait_for_timeout(3000)
                await self.page.wait_for_load_state("networkidle", timeout=15000)
                return True
        return False
