"""
LLM 管道 — 爬取阶段
==================
只做一件事：Playwright 渲染详情页 → 拿完整 HTML → 入库。
不解析、不提取、不用正则。
"""

import asyncio, logging, sys, hashlib
from datetime import datetime
from urllib.parse import urljoin

# 添加父目录到路径（引入 captcha_solver）
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S', stream=sys.stdout
)
logger = logging.getLogger(__name__)

# ─── 配置 ───────────────────────────────────────────
BASE_URL = "https://zfcg.czt.fujian.gov.cn"
SEARCH_URL = f"{BASE_URL}/maincms-web/xmgg"
MAX_PAGES = 50
SPORTS_KW = "体育"


# ─── 浏览器 ──────────────────────────────────────────
class Crawler:
    def __init__(self):
        self._pw = None
        self.browser = None
        self.context = None
        self.page = None
        self.db = None

    async def start(self):
        from playwright.async_api import async_playwright
        import sqlite3
        self._pw = await async_playwright().start()
        self.browser = await self._pw.chromium.launch(headless=False)
        self.context = await self.browser.new_context(
            viewport={"width": 1560, "height": 900},
            user_agent="Mozilla/5.0 Chrome/125.0.0.0",
            locale="zh-CN",
        )
        self.page = await self.context.new_page()
        self._init_db()
        logger.info("浏览器已启动")

    async def close(self):
        if self.browser: await self.browser.close()
        if self._pw: await self._pw.stop()

    def _init_db(self):
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "llm_bidding.db")
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                url TEXT UNIQUE,
                source TEXT DEFAULT '福建省政府采购网',
                notice_type TEXT,
                region TEXT,
                publish_date TEXT,
                raw_html TEXT,
                status TEXT DEFAULT 'raw',
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS extracted (
                page_id INTEGER PRIMARY KEY,
                data_json TEXT,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (page_id) REFERENCES pages(id)
            )
        """)
        self.conn.commit()

    async def crawl(self, keyword=SPORTS_KW):
        saved = 0
        await self.page.goto(SEARCH_URL, timeout=30000, wait_until="load")
        await self.page.wait_for_timeout(5000)

        # 填关键词
        inp = await self.page.query_selector("input[placeholder*='标题']")
        if inp: await inp.fill(keyword)

        # 验证码 + 查询
        from captcha_solver import trigger_captcha_and_solve
        ok = await trigger_captcha_and_solve(self.page, keyword)
        if not ok:
            logger.error("验证码失败")
            return 0
        await self.page.wait_for_timeout(2000)

        # 逐页
        for page_num in range(1, MAX_PAGES + 1):
            logger.info(f"📄 第 {page_num} 页")
            rows = await self.page.query_selector_all(
                ".el-table__body-wrapper tbody tr"
            )
            if not rows: break

            list_url = self.page.url

            for row in rows:
                cells = await row.query_selector_all("td")
                titles = [await c.inner_text() for c in cells]
                title = titles[3].strip() if len(titles) > 3 else ""
                if keyword not in title: continue

                # 点击行 → 拿详情 HTML
                result = await self._click_and_capture(row, list_url)
                if not result: continue
                html, detail_url = result

                # 提取基础元数据
                region = titles[0].strip() if len(titles) > 0 else ""
                publish_date = titles[-1].strip() if len(titles) > 4 else ""
                # 推断公告类型
                notice_type = "其他"
                for tag in ["公开招标","竞争性磋商","竞争性谈判","单一来源",
                           "询价","邀请招标","采购意向","中标","成交","合同",
                           "更正","澄清","答疑","废标","终止"]:
                    if tag in title: notice_type = tag; break

                url = detail_url

                try:
                    self.conn.execute(
                        """INSERT OR IGNORE INTO pages
                           (title, url, notice_type, region, publish_date, raw_html)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (title[:500], url, notice_type, region, publish_date, html)
                    )
                    self.conn.commit()
                    saved += 1
                    logger.info(f"  ✅ {title[:60]}")
                except Exception as e:
                    logger.debug(f"  入库失败: {e}")

            # 下一页
            has_next = await self._next_page()
            if not has_next: break
            await asyncio.sleep(3)

        logger.info(f"\n✅ 共保存 {saved} 条 HTML 到 llm_bidding.db")
        return saved

    async def _click_and_capture(self, row, list_url):
        """点击行并在详情加载后捕获 HTML 和 URL"""
        try:
            async with self.context.expect_page(timeout=8000) as popup:
                await row.click()
            detail = await popup.value
            await detail.wait_for_timeout(4000)
            html = await detail.content()
            url = detail.url
            await detail.close()
            return (html, url)
        except:
            try:
                await self.page.wait_for_timeout(4000)
                if "articleDetail" in self.page.url:
                    html = await self.page.content()
                    url = self.page.url
                    await self.page.goto(list_url, timeout=20000, wait_until="domcontentloaded")
                    await self.page.wait_for_timeout(1000)
                    return (html, url)
            except:
                pass
        return None

    async def _next_page(self):
        for sel in ["button:has-text('下一页')", ".el-pagination .btn-next"]:
            btn = await self.page.query_selector(sel)
            if btn:
                disabled = await btn.get_attribute("disabled")
                if disabled: return False
                await btn.click()
                await self.page.wait_for_timeout(3000)
                await self.page.wait_for_load_state("networkidle", timeout=15000)
                return True
        return False


async def main():
    c = Crawler()
    await c.start()
    try:
        n = await c.crawl("体育")
        logger.info(f"完成: {n} 条")
    finally:
        await c.close()


if __name__ == "__main__":
    asyncio.run(main())
