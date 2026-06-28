"""
并发爬取调度器
============
每个城市启动独立 Playwright 实例，多城市并行抓取。
用法:
    python parallel_crawl.py --site gd_gpcms --workers 4
    python parallel_crawl.py --site fj_gpcms --workers 4
    python parallel_crawl.py --site all --workers 6
"""

import asyncio, logging, sys, argparse
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S', stream=sys.stdout
)
logger = logging.getLogger(__name__)


async def crawl_one_city(base_url: str, site_name: str, city: str, keyword: str) -> int:
    """单个城市的爬取任务（独立浏览器实例）"""
    from crawlers.gd_gpcms import GpcmCrawler
    c = GpcmCrawler(base_url=base_url, site_name=site_name)
    try:
        await c.start()
        n = await c.crawl(keyword, city)
        logger.info(f"  ✅ {city}: {n} 条")
        return n
    except Exception as e:
        logger.error(f"  ❌ {city}: {e}")
        return 0
    finally:
        await c.close()


async def run_parallel(base_url: str, site_name: str, cities: list,
                       keyword: str, workers: int = 4):
    """并发爬取多个城市"""
    total = 0
    semaphore = asyncio.Semaphore(workers)

    async def worker(city):
        nonlocal total
        async with semaphore:
            n = await crawl_one_city(base_url, site_name, city, keyword)
            total += n
            return n

    tasks = [worker(city) for city in cities]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for city, result in zip(cities, results):
        if isinstance(result, Exception):
            logger.error(f"  {city}: 异常 - {result}")

    return total


async def main():
    parser = argparse.ArgumentParser(description="并发爬取调度器")
    parser.add_argument("--site", choices=["gd_gpcms", "fj_gpcms", "all"],
                       default="fj_gpcms")
    parser.add_argument("--workers", type=int, default=4, help="并发数")
    parser.add_argument("--keyword", type=str, default="体育")
    args = parser.parse_args()

    from config import GUANGDONG_CITIES, FUJIAN_CITIES

    print(f"\n{'█'*55}")
    print(f"  体育类招投标并发爬取")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  并发: {args.workers} workers")
    print(f"{'█'*55}\n")

    start = datetime.now()
    grand_total = 0

    if args.site in ("fj_gpcms", "all"):
        print(f"🔵 福建政府采购网 ({len(FUJIAN_CITIES)}城, {args.workers}并发)")
        n = await run_parallel(
            base_url="https://zfcg.czt.fujian.gov.cn",
            site_name="福建省政府采购网",
            cities=FUJIAN_CITIES,
            keyword=args.keyword,
            workers=args.workers,
        )
        grand_total += n
        print(f"   福建: +{n} 条\n")

    if args.site in ("gd_gpcms", "all"):
        print(f"🔵 广东政府采购网 ({len(GUANGDONG_CITIES)}城, {args.workers}并发)")
        n = await run_parallel(
            base_url="https://gdgpo.czt.gd.gov.cn",
            site_name="广东省政府采购网",
            cities=GUANGDONG_CITIES,
            keyword=args.keyword,
            workers=args.workers,
        )
        grand_total += n
        print(f"   广东: +{n} 条\n")

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n{'='*55}")
    print(f"  总计: {grand_total} 条 | 耗时 {elapsed:.0f}s")

    # 导出
    from storage import Database
    db = Database()
    path = db.export_to_excel()
    stats = db.get_statistics()
    print(f"  数据库: {stats['total']} 条 | {path}")


if __name__ == "__main__":
    asyncio.run(main())
