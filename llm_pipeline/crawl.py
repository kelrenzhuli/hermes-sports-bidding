"""
LLM 管道 — 爬取阶段（v3 稳定版 + 两阶段溯源）
===============
阶段1: 逐行点击（原始稳定方式），爬取所有公告
阶段2: 独立浏览器实例，批量溯源招标公告
"""
import asyncio, logging, sys, re, os
from datetime import datetime
from urllib.parse import urljoin

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S', stream=sys.stdout)
logger = logging.getLogger(__name__)

BASE_URL = "https://zfcg.czt.fujian.gov.cn"
SEARCH_URL = f"{BASE_URL}/maincms-web/xmgg"
MAX_PAGES = 3
SEARCH_KEYWORDS = ["体育", "赛", "赛事", "运动", "智慧体育", "智能体育", "数字体育", "智慧场馆", "体育数字化", "体育信息化", "体育大数据"]
BIDDING_KWS = {"公开招标", "竞争性磋商", "竞争性谈判", "单一来源", "询价", "邀请招标"}

class Crawler:
    def __init__(self):
        self._pw = None
        self.browser = None
        self.context = None
        self.page = None
        self.conn = None
        self.trace_queue = []

    async def start(self):
        from playwright.async_api import async_playwright
        import sqlite3
        self._pw = await async_playwright().start()
        self.browser = await self._pw.chromium.launch(headless=True)
        self.context = await self.browser.new_context(viewport={"width":1560,"height":900}, user_agent="Mozilla/5.0 Chrome/125.0.0.0", locale="zh-CN")
        self.page = await self.context.new_page()
        self._init_db()
        logger.info("浏览器已启动")

    async def close(self):
        if self.browser: await self.browser.close()
        if self._pw: await self._pw.stop()

    def _init_db(self):
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "llm_bidding_v2.db")
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, url TEXT UNIQUE,
            source TEXT DEFAULT '福建省政府采购网', notice_type TEXT, region TEXT,
            publish_date TEXT, raw_html TEXT, status TEXT DEFAULT 'raw',
            project_number TEXT, procurement_method TEXT, crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS extracted (
            page_id INTEGER PRIMARY KEY, data_json TEXT,
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        self.conn.commit()

    def _extract_project_number(self, html):
        for p in [r'项目编号[：:]\s*(\[[\w]+\][\w\[\]]+)', r'[三四]、项目编号[：:]<[^>]*>\s*(\[[\w]+\][\w\[\]]+)']:
            m = re.search(p, html)
            if m: return m.group(1).strip()
        return None

    # ═══════ 阶段1：原始稳定版爬取 ═══════
    async def crawl_phase1(self, keyword):
        saved = 0
        await self.page.goto(SEARCH_URL, timeout=30000, wait_until="load")
        await self.page.wait_for_timeout(5000)
        inp = await self.page.query_selector("input[placeholder*='标题']")
        if inp: await inp.fill(keyword)

        from captcha_solver import trigger_captcha_and_solve
        ok = await trigger_captcha_and_solve(self.page, keyword)
        if not ok: logger.error("验证码失败"); return 0
        await self.page.wait_for_timeout(2000)

        for page_num in range(1, MAX_PAGES + 1):
            logger.info(f"📄 第 {page_num} 页")
            rows = await self.page.query_selector_all(".el-table__body-wrapper tbody tr")
            if not rows: break
            list_url = self.page.url

            row_idx = 0
            while row_idx < len(rows):
                # 每次重新查询，防止行元素句柄失效
                current_rows = await self.page.query_selector_all(".el-table__body-wrapper tbody tr")
                if row_idx >= len(current_rows): break
                row = current_rows[row_idx]

                cells = await row.query_selector_all("td")
                titles = [await c.inner_text() for c in cells]
                title = titles[3].strip() if len(titles) > 3 else ""
                if keyword not in title:
                    row_idx += 1
                    continue

                result = await self._click_and_capture(row, self.page.url)
                if not result:
                    row_idx += 1
                    continue
                html, detail_url = result

                region = titles[0].strip() if len(titles) > 0 else ""
                proc_method = titles[1].strip() if len(titles) > 1 else ""
                pub_date = titles[-1].strip() if len(titles) > 4 else ""
                notice_type = "其他"
                for tag in ["公开招标","竞争性磋商","竞争性谈判","单一来源","询价","邀请招标",
                           "采购意向","中标","成交","合同","更正","澄清","答疑","废标","终止"]:
                    if tag in title: notice_type = tag; break

                project_number = self._extract_project_number(html)

                try:
                    self.conn.execute("""INSERT OR IGNORE INTO pages (title, url, notice_type, region, publish_date, raw_html, project_number, procurement_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (title[:500], detail_url, notice_type, region, pub_date, html, project_number, proc_method))
                    self.conn.commit()
                    saved += 1
                    logger.info(f"  ✅ {title[:60]}")
                except Exception as e:
                    logger.debug(f"  入库失败: {e}")
                    continue

                if notice_type in ("合同","结果","采购意向","更正") and project_number:
                    exist_row = self.conn.execute("SELECT id FROM pages WHERE project_number=? ORDER BY id DESC LIMIT 1", (project_number,)).fetchone()
                    if exist_row: self.trace_queue.append((project_number, exist_row[0]))
                row_idx += 1  # 处理完成，移到下一行

            has_next = await self._next_page()
            if not has_next: break
            await asyncio.sleep(3)

        logger.info(f"📦 阶段1完成: 爬取 {saved} 条, 待溯源 {len(self.trace_queue)} 个")
        return saved

    async def _click_and_capture(self, row, list_url):
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
                    html = await self.page.content(); url = self.page.url
                    await self.page.goto(list_url, timeout=20000, wait_until="domcontentloaded")
                    await self.page.wait_for_timeout(1000)
                    return (html, url)
            except: pass
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

    # ═══════ 阶段2：新浏览器实例做溯源 ═══════
    async def crawl_phase2(self):
        """阶段2：独立浏览器，逐条溯源。避免与原context冲突"""
        from playwright.async_api import async_playwright
        from captcha_solver import trigger_captcha_and_solve
        
        if not self.trace_queue:
            logger.info("无待溯源项目"); return 0

        traced = 0
        # 为每个溯源项目开独立浏览器（稳定但稍慢）
        for idx, (proj_num, src_page_id) in enumerate(self.trace_queue):
            logger.info(f"  🔍 溯源 [{idx+1}/{len(self.trace_queue)}] {proj_num}")

            src = self.conn.execute("SELECT title FROM pages WHERE id=?", (src_page_id,)).fetchone()
            if not src: continue
            project_name = src[0]
            for suffix in ["政府采购合同公告","结果公告","采购意向","更正公告","终止公告"]:
                project_name = project_name.replace(suffix, "").strip()
            if len(project_name) < 5: continue

            # 查是否已有同项目招标公告
            exist = self.conn.execute("SELECT id FROM pages WHERE title LIKE ? AND notice_type IN ('公开招标','竞争性磋商','竞争性谈判') LIMIT 1", (f"%{project_name[:20]}%",)).fetchone()
            if exist: continue

            # 开独立浏览器实例
            _pw = await async_playwright().start()
            _browser = await _pw.chromium.launch(headless=True)
            _page = await _browser.new_page(viewport={"width":1560,"height":900}, user_agent="Mozilla/5.0 Chrome/125.0.0.0", locale="zh-CN")
            
            try:
                await _page.goto(SEARCH_URL, timeout=30000, wait_until="load")
                await _page.wait_for_timeout(3000)
                ti = await _page.query_selector("input[placeholder*='标题']")
                if ti: await ti.fill(project_name[:80])
                pi = await _page.query_selector("input[placeholder='请输入项目编号']")
                if pi: await pi.fill("")

                ok = await trigger_captcha_and_solve(_page, project_name[:20])
                if not ok: continue
                await _page.wait_for_timeout(3000)

                rows = await _page.query_selector_all(".el-table__body-wrapper tbody tr")
                for row in rows:
                    cells = await row.query_selector_all("td")
                    texts = [await c.inner_text() for c in cells]
                    title = texts[3].strip() if len(texts) > 3 else ""
                    is_bidding = any(kw in title for kw in BIDDING_KWS)
                    if not is_bidding: continue

                    # 点击打开
                    try:
                        async with _browser.contexts[0].expect_page(timeout=8000) as pp:
                            await row.click()
                        detail = await pp.value
                        await detail.wait_for_timeout(4000)
                        html = await detail.content()
                        url = detail.url
                        await detail.close()
                    except:
                        continue

                    nt = "招标公告"
                    for tag in BIDDING_KWS:
                        if tag in title: nt = tag; break
                    region = texts[0].strip() if len(texts) > 0 else ""
                    pub = texts[4].strip() if len(texts) > 4 else ""
                    method = texts[1].strip() if len(texts) > 1 else ""

                    try:
                        self.conn.execute("""INSERT OR IGNORE INTO pages (title, url, notice_type, region, publish_date, raw_html, project_number, procurement_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (title[:500], url, nt, region, pub, html, proj_num, method))
                        self.conn.commit()
                        traced += 1
                        logger.info(f"    ✅ 溯源成功: [{method}] {title[:55]}")
                    except Exception as e:
                        logger.debug(f"    入库失败: {e}")
                    break  # 只取第一个招标公告
            except Exception as e:
                logger.warning(f"    溯源异常: {e}")
            finally:
                await _browser.close()
                await _pw.stop()

        logger.info(f"📦 阶段2完成: 溯源追回 {traced} 条")
        return traced


async def main():
    c = Crawler()
    await c.start()
    try:
        # 阶段1 - 遍历所有检索词
        total_saved = 0
        for kw in SEARCH_KEYWORDS:
            logger.info(f"🔍 正在使用检索词 [{kw}] 进行爬取...")
            total_saved += await c.crawl_phase1(kw)
        
        # 阶段2 - 独立浏览器溯源
        n2 = await c.crawl_phase2()
        logger.info(f"\n✅ 全部完成: 爬取 {total_saved} 条 + 溯源追回 {n2} 条")
    finally:
        await c.close()

if __name__ == "__main__":
    asyncio.run(main())
