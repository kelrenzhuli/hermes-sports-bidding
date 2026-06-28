# Hermes 体育类招投标数据管道 — 使用说明书

## 一、项目概览

```
hermes-sports-bidding/
│
├── crawlers/                    ← 旧方案：2600行，正则提取
│   ├── gd_gpcms.py             广东/福建政府采购网 (Playwright)
│   ├── sz_ggzy.py              深圳公共资源交易中心
│   ├── ly_ggzy.py              龙岩市公共资源交易中心 (requests)
│   ├── ctbpsp.py               CTBPSP国家级 (暂停—加密API)
│   ├── fj_ggzy.py              福建省公共资源平台 (未验证)
│   ├── ccgp.py                 中国政府采购网 (反爬拦截)
│   └── base.py                 基类
│
├── llm_pipeline/                ← 新方案：240行，HTML入仓+LLM提取
│   ├── crawl.py                爬取：Playwright渲染→HTML入库
│   └── extract.py              提取：HTML→LLM→23字段JSON
│
├── captcha_solver.py            ddddocr验证码识别（两方案共用）
├── storage.py                  旧方案数据库模块
├── config.py                   旧方案配置
├── main.py                     旧方案统一入口
├── parallel_crawl.py           旧方案并发调度器
│
├── sports_bidding.db           旧方案数据库 (198条)
├── llm_bidding.db              新方案数据库 (20条)
└── PLATFORM_TEST_REPORT.md     平台试验报告
```

## 二、数据库说明

### 2.1 新方案数据库 (`llm_bidding.db`)

**pages 表 — 爬取的原始 HTML**

```sql
CREATE TABLE pages (
    id            INTEGER PRIMARY KEY,
    title         TEXT,              -- 公告标题
    url           TEXT UNIQUE,       -- 原文链接（去重键）
    source        TEXT,              -- 来源平台
    notice_type   TEXT,              -- 公告类型（爬取阶段推断）
    region        TEXT,              -- 地区
    publish_date  TEXT,              -- 发布时间
    raw_html      TEXT,              -- 完整 HTML（LLM 提取的输入）
    status        TEXT DEFAULT 'raw',-- raw / extracted / error
    crawled_at    TIMESTAMP
);
```

**extracted 表 — LLM 提取的结构化结果**

```sql
CREATE TABLE extracted (
    page_id       INTEGER PRIMARY KEY, -- 关联 pages.id
    data_json     TEXT,                -- 23字段 JSON
    extracted_at  TIMESTAMP,
    FOREIGN KEY (page_id) REFERENCES pages(id)
);
```

### 2.2 旧方案数据库 (`sports_bidding.db`)

```sql
-- 单表结构，status 字段供 hermes 消费
SELECT * FROM bidding_records WHERE status = 'raw';
-- status: raw → processed → deduped → notified
```

## 三、爬虫操作

### 3.1 运行新方案爬虫（推荐）

```bash
# 进入项目目录
cd hermes-sports-bidding

# 运行（默认：福建省政府采购网，搜索"体育"，50页）
python llm_pipeline/crawl.py

# 修改参数：编辑 crawl.py 顶部全局变量
#   MAX_PAGES = 50    → 调节页数
#   SPORTS_KW = "体育" → 搜索关键词
#   BASE_URL = "..."  → 切换平台
```

**运行特征：**
- 需要桌面环境（Playwright 启动可见浏览器）
- 每条约 4 秒（页面渲染 + 点击 + 等待）
- 50 页 × 10 行 = 最多 500 条 HTML，约 2000 秒（33分钟）
- 重复运行安全：`url UNIQUE` 自动跳过已抓页面
- 内存占用：约 500MB（Chrome 浏览器）

### 3.2 运行旧方案爬虫

```bash
# 单个平台
python main.py --site fj_gpcms --keyword 体育

# 并发（多城市同时跑）
python parallel_crawl.py --site all --workers 4

# 单独平台
python main.py --site ly_ggzy    # 龙岩
python main.py --site sz_ggzy    # 深圳
```

### 3.3 定时任务配置

```cron
# hermes 配置两条定时：
# 早上 8:00 跑新方案
0 8 * * * cd /path/to/hermes-sports-bidding && python llm_pipeline/crawl.py

# 下午 18:00 再跑一次（捕捉白天新发布的公告）
0 18 * * * cd /path/to/hermes-sports-bidding && python llm_pipeline/crawl.py
```

## 四、LLM 提取接口

### 4.1 数据读取

```python
import sqlite3, json

conn = sqlite3.connect("hermes-sports-bidding/llm_bidding.db")
conn.row_factory = sqlite3.Row

# 取待提取的页面
pending = conn.execute("""
    SELECT id, title, notice_type, raw_html
    FROM pages
    WHERE status = 'raw' AND raw_html IS NOT NULL
    ORDER BY id
    LIMIT 50  -- 每次处理 50 条
""").fetchall()
```

### 4.2 Prompt 构造

见 `llm_pipeline/extract.py` 中的 `EXTRACTION_PROMPT`。核心：

```
你是一个招投标信息提取器。从下面的 HTML 中提取所有能找到的字段，返回 JSON。

## 字段说明
{23个字段的定义和提取规则}

## 规则
1. 只提取 HTML 中明确出现的，不编造
2. 没有的字段设为 null
3. 金额格式：数字+单位
4. 资质逐条列出
5. 日期格式：YYYY-MM-DD

## HTML
{raw_html}

## JSON
```

### 4.3 结果写入

```python
# LLM 返回的 JSON
result = {
    "title": "福建省泉州体育运动学校物业管理服务...",
    "project_number": "[2025]04991",
    "notice_type": "竞争性磋商公告",
    "industry": "体育服务",
    "region": "福建省泉州市",
    ...
}

# 写入
conn.execute(
    "INSERT OR REPLACE INTO extracted (page_id, data_json) VALUES (?, ?)",
    (page_id, json.dumps(result, ensure_ascii=False))
)
conn.execute(
    "UPDATE pages SET status = 'extracted' WHERE id = ?",
    (page_id,)
)
conn.commit()
```

### 4.4 Token 估算

| 项目 | 数值 |
|------|------|
| HTML 大小 | 平均 30KB |
| 截断后输入 | ~15KB ≈ 8000 token |
| Prompt 开销 | ~500 token |
| 输出 JSON | ~300 token |
| **单条成本** | **~9000 token** |
| 每天 50 条新公告 | ~45 万 token/天 |
| Claude Haiku 价格 | $0.25/百万 token ≈ $0.11/天 |

## 五、数据消费

### 5.1 查询已提取的体育类项目

```sql
-- 新方案：从 extracted 表查
SELECT
    json_extract(e.data_json, '$.title') AS title,
    json_extract(e.data_json, '$.budget_amount') AS budget,
    json_extract(e.data_json, '$.submission_deadline') AS deadline,
    json_extract(e.data_json, '$.region') AS region,
    json_extract(e.data_json, '$.buyer') AS buyer,
    json_extract(e.data_json, '$.industry') AS industry,
    p.url
FROM extracted e
JOIN pages p ON e.page_id = p.id
WHERE json_extract(e.data_json, '$.industry') IN ('体育赛事','体育场馆','体育器材','体育服务','全民健身')
ORDER BY p.crawled_at DESC;
```

### 5.2 推送逻辑

```python
def get_new_projects():
    """获取未推送的新项目"""
    conn = sqlite3.connect("llm_bidding.db")
    rows = conn.execute("""
        SELECT p.id, e.data_json, p.url
        FROM pages p
        JOIN extracted e ON p.id = e.page_id
        WHERE p.status = 'extracted'
          AND json_extract(e.data_json, '$.industry') LIKE '%体育%'
        ORDER BY p.crawled_at DESC
    """).fetchall()

    new_projects = []
    for row in rows:
        data = json.loads(row[1])
        # 只推送最近 24 小时的
        if is_recent(data.get('publish_date')):
            new_projects.append({
                "title": data["title"],
                "budget": data.get("budget_amount"),
                "deadline": data.get("submission_deadline"),
                "buyer": data.get("buyer"),
                "qualification": data.get("eligibility"),
                "url": row[2],
            })

    return new_projects
```

### 5.3 推送模板（钉钉/飞书）

```markdown
🏟️ 新标通知

**{title}**
地区: {region} | 类型: {notice_type} | {publish_date}

💰 预算: {budget_amount}
⏰ 截止: {submission_deadline}

📋 资质要求:
{eligibility 逐条}

🏢 业主: {buyer}
🔗 {url}
```

## 六、23 字段说明

### 基础信息
| 字段 | Key | 说明 |
|------|-----|------|
| 项目名称 | title | 公告标题 |
| 项目编号 | project_number | 招标编号，如 `[2025]04991` |
| 信息类型 | notice_type | 招标公告/采购意向/中标/合同/更正/废标 |
| 所属行业 | industry | 体育设施/体育赛事/体育器材/体育培训/全民健身/文化体育/教育/建筑/IT/医疗/其他 |
| 行政区划 | region | 省→市→区县 |
| 信息来源 | source | 福建省政府采购网/深圳公共资源交易中心/… |
| 原文链接 | url | 详情页 URL |

### 关键时间节点
| 字段 | Key | 说明 |
|------|-----|------|
| 发布时间 | publish_date | YYYY-MM-DD HH:MM:SS |
| 获取招标文件截止 | doc_deadline | 买标书/下标准的截止日期 |
| 答疑截止 | qa_deadline | 提问截止日期 |
| 投标截止/开标 | submission_deadline | 最核心的时间节点 |

### 公告核心内容
| 字段 | Key | 说明 |
|------|-----|------|
| 预算金额 | budget_amount | 数字+单位（万元/元） |
| 最高限价 | ceiling_price | 报价红线 |
| 投标保证金 | bid_bond | 金额+缴纳方式 |
| 资质要求 | eligibility | 逐条列出，保留原文 |
| 招标范围 | scope_of_work | 采购内容/技术需求 |

### 项目干系人
| 字段 | Key | 说明 |
|------|-----|------|
| 业主单位 | buyer | 出资方/采购人 |
| 代理机构 | agency | 招标代理 |
| 联系方式 | contact | 电话/邮箱/地址 |

### 结果与变更
| 字段 | Key | 说明 |
|------|-----|------|
| 变更内容 | amendment | 中标/变更公告才有 |
| 中标供应商 | winner | 竞争对手情报 |
| 中标金额 | winning_price | 最终成交价 |
| 评标专家 | panelists | 少部分公告含 |

### 不同公告类型的字段可用性

| 类型 | 可提取字段数 | 特有字段 |
|------|-------------|---------|
| 招标公告/竞争性磋商/单一来源 | 16-20 | 资质要求、截止日期、预算、代理机构 |
| 采购意向 | 10-12 | 预算（表格）、采购内容 |
| 中标/结果公告 | 10-12 | 中标供应商、中标金额 |
| 合同公告 | 8-10 | 合同金额、签约方 |
| 更正/废标公告 | 6-8 | 变更内容 |
| 澄清/答疑 | 4-6 | 澄清内容 |

## 七、故障处理

| 现象 | 原因 | 处理 |
|------|------|------|
| crawl.py 报 `Target crashed` | 浏览器内存耗尽 | 减 `MAX_PAGES` 到 10-20，分多次跑 |
| 验证码识别失败 | ddddocr 精度不足 | 重跑，验证码会自动刷新重试 |
| INSERT 数量远小于日志 | URL 去重拦截 | 正常现象，说明都已抓过 |
| HTML 全是导航代码 | 详情页未完全渲染 | 增大 `wait_for_timeout` |
| extracted 表为空 | hermes 尚未调 LLM | 检查 `pages.status = 'raw'` |

## 八、扩展新平台

在 `llm_pipeline/crawl.py` 中修改三个变量即可：

```python
BASE_URL = "https://gdgpo.czt.gd.gov.cn"  # 换成广东
SEARCH_URL = f"{BASE_URL}/maincms-web/xmgg"
SPORTS_KW = "体育"
```

GPCMS 框架（粤闽两省）完全通用。其他非 GPCMS 平台需要适配页面结构。
