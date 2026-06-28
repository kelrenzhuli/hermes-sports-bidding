"""
体育类招投标信息爬虫 — 统一入口（模块化版）
======================================
用法：
    python main.py --site fj_gpcms       # 福建政府采购网
    python main.py --site gd_gpcms       # 广东政府采购网
    python main.py --site sz_ggzy        # 深圳公共资源交易中心
    python main.py --site ly_ggzy        # 龙岩公共资源交易中心
    python main.py --site ctbpsp         # 中国招标投标公共服务平台
    python main.py --site fj_ggzy        # 福建省公共资源交易平台
    python main.py --site all            # 爬取所有已启用平台
    python main.py --keyword 体育赛事    # 指定关键词
    python main.py --stats               # 查看统计
    python main.py --export              # 导出 Excel
"""

import asyncio
import sys
import logging
from datetime import datetime

from config import (
    GUANGDONG_CITIES, FUJIAN_CITIES,
    LOG_LEVEL, LOG_FILE,
)
from storage import Database

# 爬虫注册表
CRAWLER_REGISTRY = {
    "gd_gpcms": ("crawlers.gd_gpcms", "GpcmCrawler"),
    "fj_gpcms": ("crawlers.gd_gpcms", "GpcmCrawler"),
    "sz_ggzy": ("crawlers.sz_ggzy", "SzGgzyCrawler"),
    "ly_ggzy": ("crawlers.ly_ggzy", "LyGgzyCrawler"),
}


def setup_logging():
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )


def show_stats():
    db = Database()
    stats = db.get_statistics()
    sep = "=" * 50
    print(f"\n{sep}\n📊 爬取统计\n{sep}")
    print(f"总记录数: {stats['total']}")
    if stats.get("by_status"):
        print("\n处理状态:")
        for status, count in sorted(stats["by_status"].items()):
            emoji = {"raw": "🆕", "processed": "✅", "deduped": "🔄", "notified": "📤"}.get(status, "❓")
            print(f"  {emoji} {status}: {count} 条")
    if stats.get("by_source"):
        print("\n来源分布:")
        for source, count in sorted(stats["by_source"].items(), key=lambda x: -x[1])[:10]:
            print(f"  {source:25s} {count} 条")
    if stats.get("by_region"):
        print("\n地区分布:")
        for region, count in sorted(stats["by_region"].items(), key=lambda x: -x[1])[:10]:
            print(f"  {region or '未知':12s} {count} 条")
    if stats.get("latest"):
        print("\n最新:")
        for row in stats["latest"][:5]:
            print(f"  [{row[2]}] {row[0][:50]}...")
    print()


async def run_gpcms(site_id: str, url: str, site_name: str, cities: list, keyword: str) -> int:
    """运行 GPCMS 类型爬虫（gd_gpcms / fj_gpcms）"""
    from crawlers.gd_gpcms import GpcmCrawler
    c = GpcmCrawler(base_url=url, site_name=site_name)
    try:
        total = await c.crawl_all_cities(cities, keyword)
    except Exception as e:
        logging.getLogger(__name__).error(f"{site_id} 异常: {e}")
        total = 0
    return total


async def run_sz_ggzy(keyword: str) -> int:
    """运行深圳爬虫"""
    from crawlers.sz_ggzy import SzGgzyCrawler
    c = SzGgzyCrawler()
    await c.start()
    try:
        return await c.crawl(keyword)
    finally:
        await c.close()


async def run_ly_ggzy(keyword: str) -> int:
    """运行龙岩爬虫（纯 requests，无需 start/close）"""
    from crawlers.ly_ggzy import LyGgzyCrawler
    c = LyGgzyCrawler()
    return c.crawl(keyword)


async def run_playwright_crawler(module_name: str, class_name: str, keyword: str) -> int:
    """通用 Playwright 爬虫运行器"""
    import importlib
    mod = importlib.import_module(module_name)
    cls = getattr(mod, class_name)
    c = cls()
    await c.start()
    try:
        return await c.crawl(keyword)
    finally:
        await c.close()


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="体育类招投标信息爬虫")
    parser.add_argument("--site", choices=["gd_gpcms", "fj_gpcms", "sz_ggzy",
                                            "ly_ggzy", "ctbpsp", "fj_ggzy", "all"],
                       default="fj_gpcms", help="目标站点")
    parser.add_argument("--keyword", type=str, default="体育", help="搜索关键词")
    parser.add_argument("--stats", action="store_true", help="显示统计")
    parser.add_argument("--export", action="store_true", help="导出 Excel")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    print(f"\n{'█'*50}")
    print(f"  体育类招投标信息爬虫 v2 (modular)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'█'*50}\n")

    if args.stats:
        show_stats()
        return

    if args.export:
        db = Database()
        path = db.export_to_excel()
        print(f"已导出: {path}")
        return

    start_time = datetime.now()
    total = 0

    # ═══ 福建 GPCMS ═══
    if args.site in ("fj_gpcms", "all"):
        print(f"🔵 福建政府采购网 ({len(FUJIAN_CITIES)}城)...")
        n = await run_gpcms("fj_gpcms",
                            url="https://zfcg.czt.fujian.gov.cn",
                            site_name="福建省政府采购网",
                            cities=FUJIAN_CITIES,
                            keyword=args.keyword)
        total += n
        print(f"   福建: +{n} 条\n")

    # ═══ 广东 GPCMS ═══
    if args.site in ("gd_gpcms", "all"):
        print(f"🔵 广东政府采购网 ({len(GUANGDONG_CITIES)}城)...")
        n = await run_gpcms("gd_gpcms",
                            url="https://gdgpo.czt.gd.gov.cn",
                            site_name="广东省政府采购网",
                            cities=GUANGDONG_CITIES,
                            keyword=args.keyword)
        total += n
        print(f"   广东: +{n} 条\n")

    # ═══ 深圳 ═══
    if args.site in ("sz_ggzy", "all"):
        print(f"🟠 深圳公共资源交易中心...")
        n = await run_sz_ggzy(args.keyword)
        total += n
        print(f"   深圳: +{n} 条\n")

    # ═══ 龙岩 ═══
    if args.site in ("ly_ggzy", "all"):
        print(f"🟢 龙岩市公共资源交易中心...")
        n = await run_ly_ggzy(args.keyword)
        total += n
        print(f"   龙岩: +{n} 条\n")

    # ═══ CTBPSP 国家级 ═══
    if args.site in ("ctbpsp", "all"):
        print(f"🔴 中国招标投标公共服务平台（国家级）...")
        try:
            n = await run_playwright_crawler("crawlers.ctbpsp", "CtbpspCrawler", args.keyword)
            total += n
            print(f"   CTBPSP: +{n} 条\n")
        except Exception as e:
            print(f"   CTBPSP 异常: {e}\n")

    # ═══ 福建公共资源 ═══
    if args.site in ("fj_ggzy", "all"):
        print(f"🟡 福建省公共资源交易平台...")
        try:
            n = await run_playwright_crawler("crawlers.fj_ggzy", "FjGgzyCrawler", args.keyword)
            total += n
            print(f"   福建资源: +{n} 条\n")
        except Exception as e:
            print(f"   福建资源异常: {e}\n")

    # ═══ 导出 ═══
    elapsed = (datetime.now() - start_time).total_seconds()
    db = Database()
    path = db.export_to_excel()
    show_stats()

    print(f"{'='*50}")
    print(f"  完成: {total} 条 | 耗时 {elapsed:.0f}s")
    print(f"  文件: {path}")


if __name__ == "__main__":
    asyncio.run(main())
