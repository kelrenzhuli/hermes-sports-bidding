"""
projects_v3 Schema
==================
15 字段结构化存储 + 项目生命周期追踪。
与 llm_bidding_v2.db 同库，project_number 为唯一合并键。
"""

PROJECTS_V3_DDL = """

CREATE TABLE IF NOT EXISTS projects_v3 (
    -- 标识
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    project_number   TEXT UNIQUE,        -- 项目编号（唯一合并键）
    title            TEXT NOT NULL,      -- 项目名称

    -- 15 个业务字段（直接对应 Excel 列）
    timeliness_stratum   TEXT DEFAULT '市场情报',  -- 时效层级：实时线索 / 市场情报
    project_status       TEXT DEFAULT '进行中',    -- 项目状态：进行中 / 预告中 / 已完结
    priority_tag         TEXT DEFAULT 'NO',        -- 优先级：YES / NO
    priority_reason      TEXT,                     -- 标记理由
    budget_or_winning    TEXT,                     -- 预算/成交金额（展示用）
    supplier             TEXT,                     -- 供应商（中标供应商）
    submission_deadline  TEXT,                     -- 投标截止时间
    buyer                TEXT,                     -- 采购单位
    notice_type          TEXT,                     -- 公告类型（最新阶段）
    publish_date         TEXT,                     -- 发布时间
    source_url           TEXT,                     -- 原文链接
    scope_description    TEXT,                     -- 项目描述

    -- 生命周期追踪
    lifecycle_status     TEXT DEFAULT '进行中',     -- 进行中 / 预告中 / 已完结
    lifecycle_history    TEXT DEFAULT '[]',         -- JSON: [{notice_type, date, url, page_id}, ...]

    -- 地区拆分（三级）
    province   TEXT,     -- 省
    city       TEXT,     -- 市
    district   TEXT,     -- 区/县

    -- 结构化财务（标准化数值）
    budget_raw          TEXT,      -- 预算原文（如 "500万元"）
    budget_norm         REAL,      -- 预算标准化（万元）
    winning_price_raw   TEXT,      -- 中标金额原文
    winning_price_norm  REAL,      -- 中标金额标准化（万元）

    -- 干系人
    agency       TEXT,     -- 代理机构
    eligibility  TEXT,     -- 资质要求
    winner       TEXT,     -- 中标供应商（原始）

    -- 来源追踪
    source           TEXT DEFAULT '福建省政府采购网',
    source_page_ids  TEXT DEFAULT '[]',     -- JSON: [page_id1, page_id2, ...]
    attachment_urls  TEXT,                  -- 附件链接
    raw_html         TEXT,                  -- 招标公告原始 HTML（用于重提取）
    industry         TEXT,                  -- 行业分类

    -- 元数据
    first_crawled    TEXT,     -- 首次采集时间
    last_updated     TEXT,     -- 最后更新时间
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_v3_project_number ON projects_v3(project_number);
CREATE INDEX IF NOT EXISTS idx_v3_lifecycle      ON projects_v3(lifecycle_status);
CREATE INDEX IF NOT EXISTS idx_v3_priority        ON projects_v3(priority_tag);
CREATE INDEX IF NOT EXISTS idx_v3_province_city   ON projects_v3(province, city);
CREATE INDEX IF NOT EXISTS idx_v3_publish_date    ON projects_v3(publish_date);
CREATE INDEX IF NOT EXISTS idx_v3_industry        ON projects_v3(industry);

"""

# 公告类型 → 生命周期状态跃迁映射
NOTICE_TYPE_TRANSITIONS = {
    # 预告阶段
    "采购意向":      "预告中",
    "采购需求预告":   "预告中",
    "单一来源公示":   "预告中",

    # 进行中阶段
    "公开招标":      "进行中",
    "竞争性磋商":    "进行中",
    "竞争性谈判":    "进行中",
    "单一来源":      "进行中",
    "询价":          "进行中",
    "邀请招标":      "进行中",

    # 中标后阶段（生命周期保持，字段更新）
    "中标公告":      None,  # 不改变 lifecycle_status，仅更新字段
    "结果公告":      None,
    "成交公告":      None,

    # 已完结
    "合同公告":      "已完结",
    "废标公告":      "已完结",
    "终止公告":      "已完结",

    # 其他
    "更正公告":      None,
    "变更公告":      None,
}

# 优先级：越后面优先级越高（新公告覆盖旧公告）
NOTICE_TYPE_PRIORITY = [
    "采购意向",
    "采购需求预告",
    "单一来源公示",
    "公开招标",
    "竞争性磋商",
    "竞争性谈判",
    "单一来源",
    "询价",
    "邀请招标",
    "更正公告",
    "变更公告",
    "中标公告",
    "结果公告",
    "成交公告",
    "合同公告",
    "废标公告",
    "终止公告",
]

if __name__ == "__main__":
    print("=== projects_v3 Schema ===")
    print(PROJECTS_V3_DDL)
    print(f"公告类型→状态跃迁映射: {len(NOTICE_TYPE_TRANSITIONS)} 条")
    print(f"公告类型优先级排序: {len(NOTICE_TYPE_PRIORITY)} 级")
