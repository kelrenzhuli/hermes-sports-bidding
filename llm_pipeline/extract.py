"""
LLM 管道 — 提取阶段
==================
从 DB 读取 raw HTML → LLM 提取 23 字段 → 结构化 JSON 入库。
分离于爬取，可独立运行、重试、增量处理。
"""

import sqlite3, json, logging, sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S', stream=sys.stdout
)
logger = logging.getLogger(__name__)

# ─── 23 字段 Schema ──────────────────────────────────
EXTRACTION_PROMPT = """你是一个招投标信息提取器。从下面的 HTML 中提取所有能找到的字段，返回 JSON。

## 字段说明

### 基础信息
- title: 项目名称（公告标题）
- project_number: 项目编号/招标编号
- notice_type: 公告类型（招标公告/采购意向/中标公告/更正公告/合同公告/单一来源/竞争性磋商/废标公告/其他）
- industry: 所属行业（从项目名称和内容推断：体育设施/体育赛事/体育器材/体育培训/全民健身/文化体育/教育/建筑/IT/医疗/其他）
- region: 行政区划（省→市→区县，尽可能完整）
- source: 信息来源平台
- url: 原文链接

### 时间节点
- publish_date: 发布时间 (YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS)
- doc_deadline: 获取招标文件截止时间
- qa_deadline: 答疑/提问截止时间
- submission_deadline: 投标截止时间/开标时间

### 核心内容
- budget_amount: 预算金额/预估价（带单位：万元或元）
- ceiling_price: 最高限价（如有）
- bid_bond: 投标保证金（金额和缴纳方式）
- eligibility: 投标人资质要求（逐条列出）
- scope_of_work: 招标范围/技术需求/采购内容

### 干系人
- buyer: 招标人/采购单位/业主
- agency: 招标代理机构
- contact: 联系人及联系方式（电话/邮箱/地址）

### 结果与变更（中标/变更公告才有）
- amendment: 变更内容
- winner: 中标供应商
- winning_price: 中标金额
- panelists: 评标专家名单

## 规则
1. 只有 HTML 中明确出现的才填，不要编造
2. 没有的字段设为 null
3. 金额统一为"数字+单位"格式（如 "189.9万元"）
4. 资质要求逐条列出，保留原文
5. 日期统一为 YYYY-MM-DD 格式
6. 只返回 JSON，不要其他文字

## HTML
{html}

## JSON
"""


def extract_from_html(html: str) -> dict:
    """用 LLM 从 HTML 提取字段——此处由 Claude 执行"""
    # 在实际部署中，这里调用 LLM API
    # 当前由 hermes 读取 DB 中的 raw_html 字段并调用 LLM
    raise NotImplementedError("由 hermes 调用 LLM 执行提取")


def get_pending_pages(db_path="llm_bidding.db"):
    """获取待提取的页面"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT p.id, p.title, p.notice_type, p.raw_html
        FROM pages p
        LEFT JOIN extracted e ON p.id = e.page_id
        WHERE e.page_id IS NULL AND p.raw_html IS NOT NULL
        ORDER BY p.id
    """).fetchall()
    conn.close()
    return rows


def save_extraction(db_path, page_id, data):
    """保存提取结果"""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT OR REPLACE INTO extracted (page_id, data_json) VALUES (?, ?)",
        (page_id, json.dumps(data, ensure_ascii=False))
    )
    conn.execute(
        "UPDATE pages SET status = 'extracted' WHERE id = ?",
        (page_id,)
    )
    conn.commit()
    conn.close()


def demo_extract(html_path="detail_0.html"):
    """演示：从 HTML 文件提取（由 Claude 执行）"""
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    prompt = EXTRACTION_PROMPT.format(html=html[:15000])  # 截断过长内容

    print("=" * 60)
    print("LLM 提取提示词 (前500字):")
    print(prompt[:500])
    print("...")
    print("=" * 60)
    print("复制以上提示词给 Claude/LLM 即可得到结构化 JSON")
    return prompt


if __name__ == "__main__":
    demo_extract()
