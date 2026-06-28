"""验证码识别模块（异步版 - 优化版）
==========
优化策略：先触发查询 → 验证码出现 → 再识别
"""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_ocr = None


def _get_ocr():
    """懒加载 OCR 引擎"""
    global _ocr
    if _ocr is None:
        import ddddocr
        _ocr = ddddocr.DdddOcr(show_ad=False)
        logger.info("ddddocr 引擎加载完成")
    return _ocr


async def find_captcha_image(page):
    """
    多策略寻找验证码图片元素

    Returns:
        Playwright element handle or None
    """
    # 策略1: img[src*='getVerify']
    img = await page.query_selector("img[src*='getVerify']")
    if img and await img.is_visible():
        return img

    # 策略2: 在 form 中找任何不是装饰性图片的 img
    form = await page.query_selector("form")
    if form:
        imgs = await form.query_selector_all("img")
        for img in imgs:
            src = await img.get_attribute("src") or ""
            if "getVerify" in src or src.endswith(".do") or "captcha" in src:
                return img
            # 如果 src 是 data:image 但尺寸小（< 300px），可能是验证码
            if src.startswith("data:image"):
                box = await img.bounding_box()
                if box and box["width"] < 300 and box["height"] < 150:
                    return img

    # 策略3: 找紧跟在"验证码"文本后面的 img
    try:
        all_imgs = await page.query_selector_all("img")
        for img in all_imgs:
            src = await img.get_attribute("src") or ""
            box = await img.bounding_box()
            if box and box["width"] < 300 and box["height"] < 150:
                return img
    except Exception:
        pass

    return None


async def solve_captcha_async(page, retries: int = 3) -> Optional[str]:
    """
    识别验证码

    Args:
        page: Playwright async page 对象
        retries: 最大重试次数

    Returns:
        识别的验证码文本，失败返回 None
    """
    ocr = _get_ocr()

    for attempt in range(retries):
        try:
            # 找到验证码图片
            img_element = await find_captcha_image(page)
            if not img_element:
                logger.warning(f"未找到验证码图片元素 (attempt {attempt + 1})")
                await page.wait_for_timeout(2000)
                continue

            # 截取图片
            screenshot = await img_element.screenshot()
            if not screenshot or len(screenshot) < 100:
                logger.warning(f"验证码截图过小 ({len(screenshot) if screenshot else 0} bytes)")
                await page.wait_for_timeout(1000)
                continue

            # OCR 识别
            result = ocr.classification(screenshot)
            result = result.strip()

            if result and len(result) >= 3:
                logger.info(f"验证码识别成功: {result}")
                return result
            else:
                logger.warning(f"验证码识别结果异常: '{result}' (attempt {attempt + 1})")

        except Exception as e:
            logger.warning(f"验证码识别异常 (attempt {attempt + 1}): {e}")

        # 刷新验证码：点击验证码图片刷新
        try:
            img = await page.query_selector("img[src*='getVerify']")
            if img:
                await img.click()
            else:
                # 尝试点击任意小图片刷新
                all_imgs = await page.query_selector_all("img")
                for img in all_imgs:
                    src = await img.get_attribute("src") or ""
                    if "getVerify" in src or "verify" in src.lower():
                        await img.click()
                        break
        except Exception:
            pass

        await page.wait_for_timeout(2000)

    logger.error(f"验证码识别失败，已重试 {retries} 次")
    return None


async def trigger_captcha_and_solve(page, keyword: str) -> bool:
    """
    在公告信息搜索页(xmgg)上解决验证码并提交查询
    """
    # 1. 等待页面稳定
    await page.wait_for_load_state("load", timeout=20000)
    await page.wait_for_timeout(3000)

    # 2. 填写关键词（如果还没填）
    kw_input = await page.query_selector("input[placeholder*='标题']")
    if kw_input:
        current = await kw_input.get_attribute("value") or ""
        if keyword not in current:
            await kw_input.fill(keyword)
            logger.info(f"已填写关键词: {keyword}")
    else:
        logger.warning("未找到标题输入框")

    # 3. 先关闭可能打开的下拉菜单（城市选择器遮挡问题）
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(500)

    # 4. 点击"查询"按钮触发验证码
    for attempt in range(3):
        await page.wait_for_timeout(500)

        # 点击查询按钮（force=True 绕过下拉菜单遮挡）
        query_btn = page.get_by_role("button", name="查询")
        if await query_btn.count() > 0:
            await query_btn.click(force=True)
        else:
            # 后备
            btns = await page.query_selector_all("form button")
            if btns:
                await btns[0].click()
            else:
                logger.error("找不到查询按钮")
                return False

        await page.wait_for_timeout(3000)
        await page.wait_for_load_state("load", timeout=20000)

        # 检查是否出现验证码要求
        need_captcha = await page.query_selector("text=请完成上方验证码, text=请输入验证码")
        if need_captcha:
            logger.info("验证码已触发")
            break

        # 如果表格中有数据行（即表头+至少1条数据），表示无需验证码
        data_rows = await page.query_selector_all("table tbody tr td")
        if data_rows and len(data_rows) >= 5:
            logger.info("已有数据返回（无需验证码）")
            return True

        await page.wait_for_timeout(2000)

    # 4. 找到验证码图片并识别
    captcha_img = None
    for attempt in range(5):
        imgs = await page.query_selector_all("form img")
        for img in imgs:
            box = await img.bounding_box()
            if box and 30 < box["width"] < 300 and 20 < box["height"] < 120:
                captcha_img = img
                logger.info(f"📷 验证码图片: {box['width']:.0f}x{box['height']:.0f}")
                break
        if captcha_img:
            break
        await page.wait_for_timeout(2000)

    if not captcha_img:
        logger.error("找不到验证码图片")
        return False

    # 5. OCR 循环
    ocr = _get_ocr()
    for attempt in range(3):
        screenshot = await captcha_img.screenshot()
        result = ocr.classification(screenshot).strip()
        if not result or len(result) < 3:
            logger.warning(f"验证码识别异常: '{result}' (attempt {attempt + 1})")
            await captcha_img.click()
            await page.wait_for_timeout(2000)
            continue

        logger.info(f"验证码识别成功: {result}")

        # 输入验证码
        captcha_input = page.get_by_placeholder("请输入验证码")
        await captcha_input.fill(result)
        await page.wait_for_timeout(1000)

        # 再次点击查询（force 绕过遮挡）
        query_btn = page.get_by_role("button", name="查询")
        if await query_btn.count() > 0:
            await query_btn.click(force=True)
        await page.wait_for_timeout(5000)
        await page.wait_for_load_state("load", timeout=20000)

        # 检查是否成功
        error = await page.query_selector("text=验证码错误, text=请输入正确验证码")
        if error:
            logger.warning(f"验证码错误: '{result}'")
            await captcha_img.click()
            await page.wait_for_timeout(2000)
            continue

        logger.info("✅ 验证码通过，查询成功")
        return True

    return False


async def refresh_captcha_async(page):
    """刷新验证码图片"""
    try:
        img = await page.query_selector("img[src*='getVerify']")
        if img:
            await img.click()
            await page.wait_for_timeout(1500)
            return True
        # 尝试找任意小图片
        all_imgs = await page.query_selector_all("img")
        for img in all_imgs:
            src = await img.get_attribute("src") or ""
            if "getVerify" in src:
                await img.click()
                await page.wait_for_timeout(1500)
                return True
    except Exception as e:
        logger.debug(f"刷新验证码异常: {e}")
    return False
