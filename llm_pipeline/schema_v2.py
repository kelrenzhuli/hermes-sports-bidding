"""
全网监控版 — 数据库 Schema
=========================
每条记录追踪项目全生命周期：
  招标中 → 已开标 → 已中标 → 已废标
同一项目通过 project_number 合并
"""

SCHEMA_SQL = """
-- 项目主表（一个项目一行，状态动态更新）
CREATE TABLE IF NOT EXISTS projects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_number  TEXT,               -- 项目编号（唯一标识，优先去重）
    title           TEXT NOT NULL,      -- 标题
    project_status  TEXT DEFAULT '招标中', -- 项目状态：招标中/已开标/已中标/已废标/已变更/已结束
    notice_type     TEXT,               -- 当前阶段公告类型
    province        TEXT,               -- 省
    city            TEXT,               -- 市
    district        TEXT,               -- 区/县
    industry        TEXT,               -- 行业
    publish_date    TEXT,               -- 发布时间
    first_crawled   TEXT,               -- 首次采集时间
    last_updated    TEXT,               -- 最后更新时间
    budget_raw      TEXT,               -- 预算原文（如"500万元"）
    budget_norm     REAL,               -- 预算标准化（统一为万元）
    submission_deadline TEXT,           -- 投标截止
    buyer           TEXT,               -- 业主单位
    agency          TEXT,               -- 代理机构
    eligibility     TEXT,               -- 资质要求
    scope_of_work   TEXT,               -- 招标范围
    winner          TEXT,               -- 中标供应商
    winning_price_raw TEXT,             -- 中标金额原文
    winning_price_norm REAL,            -- 中标金额标准化（万元）
    url             TEXT,               -- 原文链接
    attachment_urls TEXT,               -- 附件下载地址（JSON数组）
    source          TEXT,               -- 信息来源
    is_merged       INTEGER DEFAULT 0,  -- 是否经过合并（0=单条,1=已缝合）
    raw_html        TEXT,               -- 原始HTML（重新提取时用）
    status          TEXT DEFAULT 'raw', -- hermes处理状态
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_project_number ON projects(project_number);
CREATE INDEX IF NOT EXISTS idx_project_status ON projects(project_status);
CREATE INDEX IF NOT EXISTS idx_province_city ON projects(province, city);
CREATE INDEX IF NOT EXISTS idx_industry ON projects(industry);
CREATE INDEX IF NOT EXISTS idx_publish_date ON projects(publish_date);
CREATE UNIQUE INDEX IF NOT EXISTS idx_url_unique ON projects(url);
"""


AMOUNT_NORMALIZE_PROMPT = """
金额标准化规则：
- "500万元" → 500.0
- "5,000,000.00元" → 500.0
- "50.5万" → 50.5
- "189900" (无单位) → 保留原文
- 统一转换为"万元"单位
"""


EXTRACTION_PROMPT_V2 = """你是一个招投标信息提取器。从 HTML 中提取所有能找到的字段，返回 JSON。

## 字段

### 标识
- project_number: 项目编号/招标编号（如 [350001]RS[CS]2025001）
- title: 项目名称

### 状态
- project_status: 项目状态。根据公告类型推断：
  - 招标公告/竞争性磋商/单一来源/采购意向 → "招标中"
  - 开标公告/中标候选人公示 → "已开标"
  - 中标公告/结果公告/合同公告 → "已中标"
  - 废标公告/终止公告 → "已废标"
  - 更正公告/变更公告 → "已变更"
- notice_type: 公告类型原文

### 地区（三级拆分）
- province: 省
- city: 市
- district: 区/县

### 时间
- publish_date: 发布时间 (YYYY-MM-DD)
- submission_deadline: 投标截止/开标时间

### 金额（两个版本）
- budget_raw: 预算原文（如"500万元"）
- budget_norm: 标准化金额（统一转为"万元"，纯数字，如 500.0。无单位则保留原文）

### 干系人
- buyer: 业主单位/采购人
- agency: 代理机构

### 资质与需求
- eligibility: 资质要求（逐条，保留原文）
- scope_of_work: 招标范围/采购内容

### 结果（仅中标/结果公告）
- winner: 中标供应商
- winning_price_raw: 中标金额原文
- winning_price_norm: 标准化中标金额（万元）

### 附件
- attachment_urls: 附件链接列表（从HTML中的<a href="...pdf">提取）

## 规则
1. 只提取 HTML 中明确出现的，不编造，没有的设 null
2. 金额标准化：500万元→500.0, 5,000,000.00元→500.0, 50.5万→50.5
3. 地区必须拆分为省/市/区三级
4. project_status 根据公告类型推断
5. 只返回 JSON

## HTML
{html}

## JSON
"""


TITLE_ORDER = [
    "project_number",   # 1. 项目编号（唯一标识）
    "title",            # 2. 标题
    "project_status",   # 3. 项目状态
    "notice_type",      # 4. 公告类型
    "province",         # 5. 省
    "city",             # 6. 市
    "district",         # 7. 区县
    "industry",         # 8. 行业
    "publish_date",     # 9. 发布时间
    "first_crawled",    # 10. 采集时间
    "budget_raw",       # 11. 预算原文
    "budget_norm",      # 12. 预算(万元)
    "submission_deadline", # 13. 投标截止
    "buyer",            # 14. 业主
    "agency",           # 15. 代理机构
    "eligibility",      # 16. 资质
    "scope_of_work",    # 17. 招标范围
    "winner",           # 18. 中标供应商
    "winning_price_raw", # 19. 中标金额原文
    "winning_price_norm", # 20. 中标金额(万元)
    "url",              # 21. 原文链接
    "attachment_urls",  # 22. 附件
    "source",           # 23. 来源
]

print("Schema 和 Prompt V2 已就绪。")
print(f"共 {len(TITLE_ORDER)} 个字段，按优先级排序。")
