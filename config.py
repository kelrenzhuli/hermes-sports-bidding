"""
爬虫配置文件
==========
所有可调整的参数集中在此，方便维护。
新增平台时只需在 PLATFORMS 中添加条目。
"""

# ===== 目标站点注册表 =====
# 每个平台一个条目，type: government / industry / news
PLATFORMS = {
    # ── 政府平台（已验证） ──
    "gd_gpcms": {
        "name": "广东省政府采购网",
        "url": "https://gdgpo.czt.gd.gov.cn",
        "type": "government",
        "enabled": True,
    },
    "fj_gpcms": {
        "name": "福建省政府采购网",
        "url": "https://zfcg.czt.fujian.gov.cn",
        "type": "government",
        "enabled": True,
    },
    "sz_ggzy": {
        "name": "深圳公共资源交易中心",
        "url": "https://www.szggzy.com",
        "type": "government",
        "enabled": True,
    },

    # ── 政府平台（待验证） ──
    "gd_ggzy": {
        "name": "广东省公共资源交易平台",
        "url": "https://www.gdggzy.org.cn",
        "type": "government",
        "enabled": True,
    },
    "fj_ggzy": {
        "name": "福建省公共资源交易平台",
        "url": "https://ggzyfw.fujian.gov.cn",
        "type": "government",
        "enabled": True,
    },
    "ly_ggzy": {
        "name": "龙岩市公共资源交易中心",
        "url": "https://ggzy.longyan.gov.cn",
        "type": "government",
        "enabled": True,
    },
    "sz_gov": {
        "name": "深圳市政府采购监管网",
        "url": "https://zfcg.sz.gov.cn",
        "type": "government",
        "enabled": True,
    },
    "ccgp": {
        "name": "中国政府采购网",
        "url": "https://www.ccgp.gov.cn",
        "type": "government",
        "enabled": True,
    },

    # ── 行业平台 ──
    "ctbpsp": {
        "name": "中国招标投标公共服务平台",
        "url": "https://www.ctbpsp.com",
        "type": "industry",
        "enabled": True,
    },
    "bidding_cno": {
        "name": "中国采购与招标网",
        "url": "https://www.chinabidding.cn",
        "type": "industry",
        "enabled": True,
    },

    # ── 地方新闻/体育局 ──
    "sz_sports": {
        "name": "深圳市文化广电旅游体育局",
        "url": "https://wtl.sz.gov.cn",
        "type": "news",
        "enabled": True,
    },
    "gd_sports": {
        "name": "广东省体育局",
        "url": "https://tyj.gd.gov.cn",
        "type": "news",
        "enabled": True,
    },
    "fj_sports": {
        "name": "福建省体育局",
        "url": "https://tyj.fujian.gov.cn",
        "type": "news",
        "enabled": True,
    },
    "ly_gov": {
        "name": "龙岩市人民政府（公告公示）",
        "url": "https://www.longyan.gov.cn",
        "type": "news",
        "enabled": True,
    },
}

# ===== 搜索关键词（体育类） =====
SPORTS_KEYWORDS = [
    "体育", "健身", "球场", "体育器材", "体育设施",
    "运动场", "体育馆", "游泳馆", "田径场", "体育用品",
    "赛事", "运动装备", "体育设备", "体育工程",
    # 体育赛事运营类（重点）
    "体育赛事", "赛事运营", "体育比赛", "体育竞赛",
    "马拉松", "龙舟赛", "运动会", "体育节",
    "体育表演", "赛事服务", "赛事活动", "体育交流",
    "群众体育", "全民健身", "体育产业", "体育运营",
    "体育服务", "体育培训", "体育组织", "赛事组织",
]

# ===== 目标区域 =====
GUANGDONG_CITIES = [
    "深圳市", "广州市", "东莞市", "佛山市", "珠海市",
    "惠州市", "中山市", "汕头市", "江门市", "湛江市",
    "茂名市", "肇庆市", "梅州市", "清远市", "韶关市",
    "河源市", "阳江市", "潮州市", "揭阳市", "云浮市",
    "汕尾市",
]

FUJIAN_CITIES = [
    "龙岩市", "福州市", "厦门市", "泉州市", "漳州市",
    "莆田市", "三明市", "南平市", "宁德市",
]

# ===== 爬虫行为控制（合规关键） =====
REQUEST_DELAY = 3           # 每次操作间隔（秒），不低于 3 秒
PAGE_LOAD_TIMEOUT = 30000   # 页面加载超时（毫秒）
CAPTCHA_RETRY = 3           # 验证码识别最大重试次数
MAX_PAGES = 50              # 每个搜索条件下的最大翻页数
BROWSER_HEADLESS = False    # 是否无头模式（开发阶段建议 False 方便观察）

# ===== 数据存储 =====
DB_PATH = "sports_bidding.db"
EXPORT_EXCEL = True
EXCEL_PATH = "sports_bidding_export.xlsx"

# ===== 日志 =====
LOG_LEVEL = "INFO"
LOG_FILE = "crawler.log"
