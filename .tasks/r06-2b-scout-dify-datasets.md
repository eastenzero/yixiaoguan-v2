---
id: "r06-2b-scout-dify-datasets"
parent: "R06-2"
type: "feature"
status: "pending"
tier: "T3"
priority: "high"
risk: "low"
foundation: true                    # R06-2 Executor 的策略裁决依赖此 Scout 的产出

scope:
  - "docs/design/dify-datasets-diff-report.md"   # 仅允许创建此产出文件

out_of_scope:
  - "services/**"
  - "apps/**"
  - "../../kb-pipeline/**"          # KB 仓只读
  - "scripts/migrate_kb.py"         # Executor 任务才会改
  - "任何对 Dify Dataset 的写操作"   # 严格只读
  - "任何对 Dify Chatflow 的修改"
  - "任何对 Dify 草稿 Dataset 的'发布'点击"

context_files:
  - ".teb/antipatterns.md"
  - "docs/requirements/R06-P0-quick-wins.md"       # R06-2 章节
  - "docs/design/kb-source-scout-report.md"         # r06-2 Scout 已确认 local 835 条
  - "docs/design/dify-current-prompt.md"            # r06-3a 已披露两个 Dataset ID
  - "docs/design/dify-current-config.md"
  - "docs/PROJECT-SECRETS.md"                       # §2.1 Dify 账号 / §3.1 165 SSH

done_criteria:
  L0: "docs/design/dify-datasets-diff-report.md 存在"
  L1: "报告给出两个 Dataset 各自的文档数、前 20 个文档名、最新一条更新时间"
  L2: "报告给出 '已发布 Dataset vs final-merged/ 的 title 集合差异'（缺失集 / 多余集 / 重叠数）"
  L3: "报告末尾给出明确的 R06-2 策略裁决建议：A / B / C 之一，并附证据"

depends_on:
  - "r06-2-scout-kb-source"          # 本地 835 条清单来源
  - "r06-3a-scout-dify-prompt"       # 两个 Dataset ID 来源
created_at: "2026-04-20"
---

> ⚠️ **Meta：T0 代劳起草** — 2026-04-20 TX 授权 T0 代 T1 起草本任务文件。
> T1 审阅后可直接采用、局部调整、或完全重写。
> 规范边界：[`.teb/antipatterns.md`](../.teb/antipatterns.md)。

# R06-2b Scout · 核查 Dify 两个 Dataset 的实际内容与 final-merged/ 差异

> 目标状态：给 R06-2 Executor 一个**有证据**的策略裁决——
> **A** 已完成（直接标 ✅）/ **B** 切换到草稿 Dataset 并发布 / **C** 重新灌一遍。
>
> **严格只读**：本任务不新建 / 不删除 / 不发布任何 Dify Dataset。

## 背景

r06-2 和 r06-3a 的 Scout 报告揭示了矛盾事实：

- **本地** `kb-pipeline/04-output/final-merged/` 有 **835 条** v2 条目（12 分类子目录）
- **Dify 已发布 Dataset**（`ec072e85-ebb3-4f2a-a966-a21566b88995`）: r06-2 报告说"已与本地 835 条完全同步"——但这个结论来源未给证据
- **Dify 草稿 Dataset**（`4db0c819-7847-4a95-bf06-5b73a9d41d70`）: 疑似新建但未发布，内容未知
- Memory 里的 S3 迁移记录：当时跑 `migrate_kb.py` 成功导入 **433 条 v1 数据**，而非 835

这三者必须对齐后才能决定 R06-2 要不要跑迁移脚本，以及到底该指向哪个 Dataset。

## 必读上下文

1. `docs/requirements/R06-P0-quick-wins.md` § R06-2（父需求）
2. `docs/design/kb-source-scout-report.md`（本地 835 条详情）
3. `docs/design/dify-current-prompt.md` § 2.4（两个 Dataset ID 及 Top K / rerank 配置）
4. `docs/PROJECT-SECRETS.md` § 2.1（Dify 管理员账号）+ § 3.1（165 SSH）

## Scout 执行步骤

> 本任务**强烈推荐用 SSH + Dify PG 直查** 的方式（r06-3a 已验证可行），不要走浏览器分页点击。

### Step 1：拿到本地 835 条 title 清单

```bash
# 在 Windows 本地 或 165 上均可（前提是能访问 kb-pipeline）
cd /c/Users/Administrator/Documents/code/kb-pipeline/04-output/final-merged   # Windows Git Bash
# 或 165 上的等价路径（若已同步）

# 提取所有 frontmatter 中的 title 字段
find . -name "KB-V2-*.md" | while read f; do
  awk '/^title:/ {sub(/^title:[[:space:]]*"?/,""); sub(/"?$/,""); print; exit}' "$f"
done | sort -u > /tmp/local-835-titles.txt

wc -l /tmp/local-835-titles.txt  # 应 ≈ 835
```

### Step 2：拿到 Dify 两个 Dataset 的文档清单

```bash
ssh easten@192.168.100.165
# 进入 Dify PG 容器（r06-3a 已验证 docker-db_postgres-1）
docker exec -i docker-db_postgres-1 psql -U postgres -d dify <<'SQL'
-- 已发布 Dataset
\copy (
  SELECT name
  FROM documents
  WHERE dataset_id = 'ec072e85-ebb3-4f2a-a966-a21566b88995'
    AND archived = false
  ORDER BY name
) TO '/tmp/dify-published-titles.txt';

-- 草稿 Dataset
\copy (
  SELECT name
  FROM documents
  WHERE dataset_id = '4db0c819-7847-4a95-bf06-5b73a9d41d70'
    AND archived = false
  ORDER BY name
) TO '/tmp/dify-draft-titles.txt';

-- 两个 Dataset 的基本统计
SELECT
  dataset_id,
  COUNT(*) AS doc_count,
  MIN(created_at) AS first_created,
  MAX(updated_at) AS last_updated
FROM documents
WHERE dataset_id IN (
  'ec072e85-ebb3-4f2a-a966-a21566b88995',
  '4db0c819-7847-4a95-bf06-5b73a9d41d70'
) AND archived = false
GROUP BY dataset_id;
SQL

# 从容器里 copy 出来
docker cp docker-db_postgres-1:/tmp/dify-published-titles.txt ~/dify-published-titles.txt
docker cp docker-db_postgres-1:/tmp/dify-draft-titles.txt ~/dify-draft-titles.txt
```

**注意**：
- 若 PG 表名不是 `documents`，先跑 `\dt` 查实际表名
- 若 schema 不是 `public`，先 `SET search_path TO dify;`
- 若本地没办法直接访问本地 kb-pipeline，先 `scp` final-merged/ 的 title 清单到 165

### Step 3：三方 diff

```bash
# 假设三份清单都在 ~ 下（或先 scp 本地的 local-835-titles.txt 到 165）
cd ~

# Published Dataset 与本地的差集
comm -23 <(sort -u local-835-titles.txt) <(sort -u dify-published-titles.txt) > missing-in-published.txt
comm -13 <(sort -u local-835-titles.txt) <(sort -u dify-published-titles.txt) > extra-in-published.txt

# Draft Dataset 与本地的差集
comm -23 <(sort -u local-835-titles.txt) <(sort -u dify-draft-titles.txt) > missing-in-draft.txt
comm -13 <(sort -u local-835-titles.txt) <(sort -u dify-draft-titles.txt) > extra-in-draft.txt

wc -l *.txt
```

### Step 4：抽样验证文档正文一致性（可选，仅在 title 匹配时）

若 Step 3 显示 published 与本地 title 集合重叠率 >95%，进一步抽 3 条对比正文：

```bash
docker exec -i docker-db_postgres-1 psql -U postgres -d dify -c \
  "SELECT ds.content FROM documents d JOIN document_segments ds ON ds.document_id = d.id \
   WHERE d.dataset_id = 'ec072e85-...' AND d.name = '<抽样 title>' ORDER BY ds.position LIMIT 5;"
```

和本地对应 `.md` 的前 500 字比对，记录"文本一致 / 差异摘要"。

### Step 5：辅助摸清"当前 gateway 在用哪一个 Dataset"

```bash
ssh easten@192.168.100.165
grep -i DIFY_GLOBAL_DATASET_ID ~/dev/yixiaoguan-v2/services/gateway/.env
```

把实际的 `DIFY_GLOBAL_DATASET_ID` 值记进报告。

### Step 6：写产出报告

创建 `docs/design/dify-datasets-diff-report.md`，必含章节：

```markdown
# Dify Datasets 差异核查报告（YYYY-MM-DD）

> 核查者：T3 Kimi Scout
> 数据源：Dify PG (docker-db_postgres-1) + kb-pipeline/04-output/final-merged/
> 严格只读

## 1. 基本统计
| Dataset | 文档数 | 首创 | 末更 |
|---------|-------|-----|-----|
| published (ec072e85-...) | ... | ... | ... |
| draft (4db0c819-...) | ... | ... | ... |
| local final-merged/ | 835 | — | — |

## 2. gateway 当前指向
- `.env` 的 `DIFY_GLOBAL_DATASET_ID` = `...`

## 3. Published vs Local diff
- 本地独有（缺失在 published）：N 条（前 10 title）
- Published 独有（本地没有）：M 条（前 10 title）
- 重叠：K 条

## 4. Draft vs Local diff
- 本地独有（缺失在 draft）：...
- Draft 独有（本地没有）：...
- 重叠：...

## 5. 正文一致性抽样（若 §3/§4 重叠率 >95%）
- 抽样 3 条 title
- 每条给出"正文一致 / 差异摘要"

## 6. R06-2 策略裁决建议

### 证据
（从 §1-§5 提炼）

### 建议走哪条路
- **A. 已完成**：Published Dataset 与 local 重叠率 ≥99%，gateway 已指向 published → R06-2 标 ✅
- **B. 切草稿 Dataset**：Draft 与 local 重叠率 ≥99% 且比 published 更准 → gateway 切 DIFY_GLOBAL_DATASET_ID 到 draft；在 Dify UI 点"发布" Chatflow
- **C. 重新灌**：两个 Dataset 都与 local 差异过大 → 新建 Dataset，用 migrate_kb.py 灌 local 835 条，切 gateway 配置，删或归档旧 Dataset

### 附风险点
- ...
```

### Step 7：严格只读自检

完成前检查：

- 没有 `INSERT` / `UPDATE` / `DELETE` 过 Dify PG
- 没有在 Dify Web 里点过 "发布" / "删除" / "重新索引"
- 没有改过 `.env` 或任何 compose 文件
- 没有改过 KB 仓任何文件
- 只创建了 `docs/design/dify-datasets-diff-report.md` 一个文件

## 已知陷阱

- Dify PG 的表名在不同版本可能是 `dataset_documents` 而非 `documents`，先 `\dt` 核对
- 文档 `name` 字段可能带后缀（如 `xxx [doc_id]`），比对前先归一化
- 草稿 Dataset 可能完全为空，此时 draft diff 结果 = 本地全部 - 空 = 全部"缺失"，不是异常，是"该 Dataset 还没导数据"
- "archived" 的文档不算数，过滤掉
- `DIFY_GLOBAL_DATASET_ID` 可能出现在多处（gateway `.env`、165 的 systemd unit、docker-compose env），以 gateway 启动时生效的那个为准

## 不做的事（out_of_scope）

- 不改任何 Dify 配置
- 不改任何 V2 仓代码或 .env
- 不删除 / 归档 / 发布任何 Dataset
- 不跑 migrate_kb.py
- 不改 KB 仓

## 完成后

1. 产出 `docs/design/dify-datasets-diff-report.md`
2. 向 T1 回报文件路径 + §6 的 A/B/C 结论
3. T0 依结论起草 `.tasks/r06-2-exec-kb-migrate.md`（或在 R06 spec 中直接标 R06-2 ✅）
