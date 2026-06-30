# Hermes 体育招投标自动化数据管道 — 操作手册

## 一、项目概览

```
hermes-sports-bidding/
│
├── llm_pipeline/
│   ├── crawl.py              ★ 爬虫：Playwright → cleaned_data.json
│   ├── db.py                 ★ 数据库操作：连接、upsert、查询
│   ├── export_v3.py          ★ Excel 导出（从 projects_v3 读）
│   ├── migrate_legacy.py     一次性迁移脚本（已完成）
│   └── schema_v3.py          库表 DDL 定义
│
├── final_export_full.py      ★ 导出入口（薄封装，调用 export_v3）
├── README.md                 ★ 核心规范（15 字段、决策树、提示词模板）
├── llm_bidding_v2.db         ★ 主数据库（含 projects_v3 表）
├── cleaned_data.json         爬虫输出的最新待提取数据
│
├── archived_scripts/         已归档的废弃脚本（可删除）
└── 其余 .py                  散落的辅助/调试脚本
```

### 数据库核心表

**projects_v3** — 业务主表，按 `project_number` 合并去重

| 字段 | 说明 |
|------|------|
| project_number | 项目编号（唯一合并键） |
| title | 项目名称 |
| timeliness_stratum | 时效层级（实时线索/市场情报） |
| project_status | 项目状态（进行中/预告中/已完结） |
| priority_tag | 优先级（YES/NO） |
| priority_reason | 标记理由 |
| budget_or_winning | 预算/成交金额 |
| supplier | 供应商 |
| submission_deadline | 投标截止时间 |
| buyer | 采购单位 |
| notice_type | 公告类型 |
| publish_date | 发布时间 |
| source_url | 原文链接 |
| scope_description | 项目描述 |
| lifecycle_status | 生命周期状态 |
| lifecycle_history | 生命周期轨迹（JSON） |
| source_page_ids | 来源 page_id 列表（JSON） |

---

## 二、自动化工作流

```
                  ┌─────────────────────────────┐
                  │      crawl.py  ← 你执行      │
                  │     输出 cleaned_data.json   │
                  └─────────────┬───────────────┘
                                │
                                ▼
                  ┌─────────────────────────────┐
                  │    步骤 1：读取 & 提取        │
                  │    ──────────────────────    │
                  │    读 cleaned_data.json      │
                  │    对每条记录：               │
                  │    ① 按 README 决策树判定    │
                  │    ② 提取 15 字段            │
                  └─────────────┬───────────────┘
                                │
                                ▼
                  ┌─────────────────────────────┐
                  │    步骤 2：自动验证           │
                  │    ──────────────────────    │
                  │    抽样规则：                 │
                  │    ≤50 条 → 全量验证          │
                  │    >50 条 → 随机抽 20%       │
                  │    抽检通过率 <90% → 扩到 50%│
                  │                              │
                  │    验证方式（全网搜索比对）：   │
                  │    ① 用项目编号搜             │
                  │    ② 用项目名称+预算搜        │
                  │    ③ 用供应商名称搜           │
                  │    ④ 用采购单位+项目名称搜    │
                  │    ⑤ 检查公告类型与发布日期    │
                  │                              │
                  │    置信度评分：               │
                  │    🟢 ≥4/5 → 直接入库         │
                  │    🟡 3/5   → 入库+标记待复核  │
                  │    🔴 <3/5  → 不入库，输出清单│
                  └─────────────┬───────────────┘
                                │
                                ▼
                  ┌─────────────────────────────┐
                  │    步骤 3：写入 projects_v3  │
                  │    ──────────────────────    │
                  │    调 db.upsert_project_v3() │
                  │    按 project_number 合并    │
                  │    相同项目追加生命周期历史   │
                  └─────────────┬───────────────┘
                                │
                                ▼
                  ┌─────────────────────────────┐
                  │    步骤 4：导出 Excel        │
                  │    ──────────────────────    │
                  │    python final_export_full  │
                  │    → 桌面情报单.xlsx         │
                  └─────────────────────────────┘
```

---

## 三、步骤详解

### 步骤 1：读取 cleaned_data.json 并提取 15 字段

**数据来源：** `cleaned_data.json`

结构：
```json
[
  {
    "id": 3,
    "title": "惠安县...青少年足球联赛...合同公告",
    "type": "合同公告",
    "date": "2026-06-29",
    "text": "（HTML 清洗后的纯文本）"
  }
]
```

**提取规则：** 详见 `README.md`

必须严格遵循：
- **优先级判定决策树**（README 第308-366行）— 三层分类
- **15 字段 JSON Schema**（README 第426-454行）— 输出格式
- **状态感知规则**（README 第233-241行）— 供应商/截止时间随状态变化
- **金额优先级**（README 第278-288行）— 中标金额 > 预算金额
- **空值处理**— 无值填 `原网页未披露该项`

**提示词模板**见 README 第487-580行，可直接使用。

提取完成后，将每条记录的 15 字段放入待验证队列。

---

### 步骤 2：自动验证（全网交叉比对）

#### 2.1 抽样

```python
total = len(records)
if total <= 50:
    sample = records  # 全量
else:
    import random
    sample = random.sample(records, max(10, int(total * 0.2)))
```

如果抽检通过率 < 90%，扩大到 50%；如果仍 < 90%，标记整批待人工复核。

#### 2.2 每条记录的验证项

| # | 验证项 | 搜索方式 | 通过条件 |
|---|--------|---------|---------|
| 1 | 项目编号真实存在 | 搜索 `project_number` | 在政府采购网或其他网站找到对应公告 |
| 2 | 项目名称与预算匹配 | 搜索 `title + budget` | 其他来源金额一致（±5% 容忍） |
| 3 | 供应商信息属实 | 搜索 `supplier` | 该公司确实在该地区有相关业务 |
| 4 | 采购单位与项目匹配 | 搜索 `buyer + title` | 找到该单位发布的对应公告 |
| 5 | 公告类型与日期合理 | 检查 `notice_type + publish_date` | 类型与日期逻辑一致 |

#### 2.3 置信度评分

| 分数 | 标记 | 处理 |
|:----:|:----:|:----|
| 5/5 | 🟢 高置信度 | 直接入库 |
| 4/5 | 🟢 高置信度 | 直接入库 |
| 3/5 | 🟡 中置信度 | 入库，`priority_reason` 后加 `[需复核]` |
| ≤2/5 | 🔴 低置信度 | **不入库**，写入 `failed_records.json` |

#### 2.4 验证报告输出

验证完成后在桌面生成一份验证报告：

```
验证报告_2026-07-01.md

抽样: 8/40 条
🟢 高置信度: 7 条 (87.5%)
🟡 中置信度: 1 条 (12.5%)
🔴 低置信度: 0 条

中置信度明细:
  id=9 — 项目编号为占位符，无法搜索验证（采购意向无编号）
```

---

### 步骤 3：写入 projects_v3

对 🟢 和 🟡 的记录，调用 `llm_pipeline/db.py` 的 upsert 接口：

```python
import sys
sys.path.insert(0, "C:/Users/cc/hermes-sports-bidding")
from llm_pipeline.db import get_conn, upsert_project_v3

conn = get_conn()

for record in your_extracted_list:
    action, pn = upsert_project_v3(conn, record)
    print(f"  {action}: {pn}")

conn.close()
```

`upsert_project_v3` 会自动处理：
- 新 `project_number` → INSERT
- 已有 `project_number` → UPDATE（追加生命周期历史、正向跃迁状态）
- 财务字段 → 首次有效值保留
- 生命周期字段（title、notice_type 等）→ 新值覆盖旧值

**参数格式：**

```python
record = {
    "page_id": 3,
    "title": "公告标题",
    "project_number": "[350521]YXG[CS]2026001",
    "notice_type": "合同公告",
    "publish_date": "2026-06-29",
    "source_url": "原网页未保留",
    "project_status": "已完结",        # 可选，不传则从 notice_type 推断
    "lifecycle_status": "已完结",       # 可选，不传则从 notice_type 推断
    "priority_tag": "YES",             # YES/NO
    "priority_reason": "体育赛事运营 (青少年足球联赛)",
    "budget_or_winning": "560,000元",
    "supplier": "道吧体育产业（泉州市）有限公司",
    "submission_deadline": "2026-07-09",
    "buyer": "惠安县文化体育和旅游局",
    "scope_description": "项目描述文本...",
    "raw_html": item.get("text", ""),  # 保留原文用于追溯
}
```

注意：`project_number` 不要传 `"原网页未披露该项"`，传 `None` 即可，upsert 会自动处理。

---

### 步骤 4：导出 Excel

```bash
cd C:\Users\cc\hermes-sports-bidding
python final_export_full.py
```

输出：`C:\Users\cc\Desktop\体育招投标_商业情报单.xlsx`

两个 Sheet：
- **完整数据** — 全部记录，YES 行黄色高亮
- **高价值汇总** — 仅 YES 记录

---

## 四、日常操作检查清单

每次跑完完整流程后，确认：

- [ ] `cleaned_data.json` 已读取，N 条记录全部提取
- [ ] 验证抽样完成，通过率 ≥ 90%
- [ ] `projects_v3` 已写入，行数增加 N 条（或更新已有的）
- [ ] `final_export_full.py` 执行成功
- [ ] 桌面 Excel 打开正常，Sheet1/Sheet2 数据正确

---

## 五、故障处理

| 现象 | 原因 | 处理 |
|------|------|------|
| `cleaned_data.json` 不存在 | 爬虫未运行 | 先跑 `python llm_pipeline/crawl.py` |
| 大量记录验证不通过（<70%） | 搜索被限流或规则需要调整 | 检查 README 决策树，调整提示词 |
| `upsert_project_v3` 报错 | 字段格式不符 | 检查必填字段是否完整 |
| Excel 导出报 `PermissionError` | 文件被 Excel 打开 | 关掉 Excel 再跑 |
| `projects_v3` 行数没变 | 新数据 `project_number` 与已有记录重复 | 正常现象，说明是已有项目的补充公告 |

---

## 六、与旧版区别

| 维度 | 旧版（之前） | 新版（现在） |
|:----|:------------|:------------|
| 数据库 | `llm_bidding.db`（pages + extracted） | `llm_bidding_v2.db`（projects_v3） |
| 字段数 | 23 字段 | 15 字段（按 README v3 规范） |
| 提取方式 | 手动 copy-paste 给 Claude | Hermes 自动提取 + 验证 + 入库 |
| 合并逻辑 | 无，每条公告独立 | 按 project_number 合并，追踪生命周期 |
| 导出 | 多个脚本各出各的 | 统一 `final_export_full.py` |
| 验证 | 无 | 自动抽样 20%，全网搜索交叉比对 |
