# KB 仓 960 条数据源侦察报告

> 侦察日期：2026-04-20  
> 执行者：T3 Scout  
> 数据来源：kb-pipeline（`C:\Users\Administrator\Documents\code\kb-pipeline`）  
> 目标：为 `.tasks/r06-2-exec-kb-migrate.md` 提供精确的数据源情报

---

## 1. 文件位置

### 1.1 v2（KB 仓 W1 最终产出）
- **主产出路径**：`C:\Users\Administrator\Documents\code\kb-pipeline\04-output\final-merged\`
- **组织方式**：按 12 个分类建立子目录，每个子目录下存放该分类的全部 `.md` 文件
- **子目录清单**：
  - `医疗与心理/`
  - `国际交流/`
  - `图书馆与信息化/`
  - `奖助学金/`
  - `学术与竞赛/`
  - `就业与毕业/`
  - `教务与学籍/`
  - `校园生活/`
  - `研究生事务/`
  - `行政与规章/`
  - `财务与缴费/`
  - `院系与学校/`

- **次要产出**：
  - `04-output/from-raw/` — W1 新增 164 条的原始草稿（已被合并进 final-merged，**不作为入库源**）
  - `04-output/merged/` — 三路合并中间产物（796 条， outdated，**不作为入库源**）
  - `tutorials/` — 图文教程包（12 原子 + 4 组合），**不属于 KB 条目，不入 Dify Dataset**

### 1.2 v1（当前脚本指向的旧数据源）
- **路径**：`C:\Users\Administrator\Documents\code\yixiaoguan\knowledge-base\entries\`
- **子目录**：
  - `entries/` — 433 个 `KB-*.md`
  - `first-batch-drafts/` — 433 个 `KB-*.md`（与 entries/ 内容高度重合，当前脚本未扫描此目录）
- **总文件数**：866（但当前 `migrate_kb.py` 的 `--entries-dir` 通常只指向 `entries/` 子目录，扫描到 433 个）

> ⚠️ **重要发现**：任务描述中的 "v1 的 731 条" 与实际文件数量（433 或 866）不符。731 可能是 Dify 中实际可见的文档数（含早期手动上传或部分过滤），而非磁盘文件数。Executor 应以实际文件为准。

---

## 2. 数据格式

### 2.1 文件类型
- **纯 Markdown（`.md`）**，单文件模式（非 JSONL / 非汇总文件）

### 2.2 命名规则
```
KB-V2-C{两位分类编号}-{三位序号}.md
```
示例：
- `KB-V2-C07-001.md`（医疗与心理第 1 条）
- `KB-V2-C04-050.md`（奖助学金第 50 条）
- `KB-V2-C01-132.md`（教务与学籍第 132 条）

### 2.3 单条 schema（v2）

每个文件由 **YAML frontmatter** + **Markdown body** 组成：

```yaml
---
doc_id: "KB-V2-C02-001"          # 文档唯一标识
title: "后勤管理部 — 学生服务指南"  # 文档标题
category: "校园生活"               # 12 分类之一
tags:                              # 自由标签数组
  - 报修
  - 宿舍
sources:                           # 数据来源（对象数组）
  - type: "website"                # website / raw_material / wechat / reference
    path: "W2/scraped-pages/后勤管理部/"
campus: "通用"                     # 通用 / 济南校区 / 泰安校区
last_verified: "2026-04-14"        # 最后验证日期
---
```

**正文结构规则**：
- 不使用 `#` 一级标题（留给 frontmatter 的 `title`）
- `##` 二级标题 = 一个独立知识点（Dify 分段的主要切分点）
- `###` 三级标题 = 知识点内子节
- 知识点之间用 `---` 分隔
- 每个 `##` 段落控制在 50–500 字

### 2.4 单条 schema（v1，供对比）

```yaml
---
entry_id: KB-20260324-0139         # 或不存在
material_id: "学生手册-生活服务"
title: "电费缴纳指南"
category: "生活服务"
tags: ["电费", "缴费", "完美校园", "宿舍", "电控"]
source: "学生手册-生活服务.md 行 4927-5041"   # 单字符串
source_url: ""
campus: "通用"
status: "active" / "draft"
---
```

正文结构：通常包含 `## 适用对象`、`## 问题概述`、`## 标准答复`、`## 详细说明` 等固定板块。

---

## 3. 字段映射（v1 → v2）

| v1 字段 | v2 字段 | 是否一致 | 转换规则 |
|---------|--------|---------|---------|
| `title` | `title` | ✅ 一致 | 直接透传 |
| `category` | `category` | ❌ 值域不同 | v1 有 30 个旧分类 → 需映射到 12 个新分类（见第 4 章） |
| `content`（body） | `content`（body） | ⚠️ 结构不同 | 直接透传正文；v2 使用 `##`/`###`/`---` 分段，Dify automatic 模式兼容 |
| `source`（单字符串） | `sources`（对象数组） | ❌ 格式不同 | 取 `sources[0].path` 作为 `original_source`；若 `type==website` 可尝试补 `source_url` |
| `source_url` | — | ❌ v2 已移除 | v2 无直接对应字段；如需保留，建议从 website 类型的 sources 推断，或留空 |
| `tags` | `tags` | ✅ 一致 | 都是 `string[]`，直接透传 |
| `material_id` | `doc_id` | ⚠️ 语义不同 | `material_id` 是原材料编号；`doc_id` 是 v2 统一编号。建议将 `doc_id` 写入 `material_id` 或新增字段 |
| `campus` | `campus` | ⚠️ 值域收紧 | v1 有 "济南"、"济南校区"、"通用" 等变体；v2 严格三选一：`通用` / `济南校区` / `泰安校区`。建议做归一化 |
| `status` | — | ❌ v2 已移除 | v2 默认全部 active，无需处理 |
| `entry_id` | `doc_id` | ⚠️ 替代关系 | v1 的 `entry_id` 被 v2 的 `doc_id` 取代 |
| — | `last_verified` | ❌ v2 新增 | 当前 PG 表无此字段，如需记录需加 migration |

**PG 表 `kb_entries` 当前字段与 v2 的对应**：

| PG 字段 | v2 来源 | 说明 |
|---------|--------|------|
| `title` | `frontmatter.title` | ✅ 直接映射 |
| `category` | `frontmatter.category` | ⚠️ 需做分类映射 |
| `tags` | `frontmatter.tags` | ✅ 直接映射 |
| `original_source` | `frontmatter.sources[0].path` | ⚠️ 从数组取首个元素的 `path` |
| `source_url` | — | ⚠️ v2 无直接对应，建议留空或从 website source 推断 |
| `material_id` | `frontmatter.doc_id` | ⚠️ 建议复用此字段存 `doc_id` |
| `campus` | `frontmatter.campus` | ⚠️ 建议归一化 |
| `original_filename` | 文件名 | ✅ 直接映射 |

---

## 4. 分类体系映射

### 4.1 v1 旧分类集合（实际抽样 866 条统计）

| v1 旧分类 | 数量（近似） |
|-----------|------------|
| 毕业与就业 | 100 |
| 校园生活与服务 | 98 |
| 奖助贷补 | 76 |
| 生活服务 | 52 |
| 教务与课程 | 46 |
| 财务与缴费 | 38 |
| 就业与毕业 | 38 |
| 证件与校园服务 | 36 |
| 图书馆服务 | 36 |
| 院系与专业 | 32 |
| 事务申请与审批 | 30 |
| 研究生教育 | 30 |
| 国际交流 | 26 |
| 心理与测评 | 26 |
| 信息化服务 | 24 |
| 竞赛与第二课堂 | 24 |
| 入学与学籍 | 22 |
| 招生与深造 | 22 |
| 心理健康 | 20 |
| 科研与创新 | 18 |
| 研究生事务 | 14 |
| 图书馆 | 12 |
| 学生资助 | 10 |
| 学籍与教务 | 8 |
| 学业管理 / 学生管理 / 学校概况 / 学生服务 / 教学与培养 / 校园安全 / 学业发展 | 各 ≤6 |

### 4.2 v2 新分类（12 个）

| 编号 | category 值 |
|------|-------------|
| C01 | 教务与学籍 |
| C02 | 校园生活 |
| C03 | 财务与缴费 |
| C04 | 奖助学金 |
| C05 | 就业与毕业 |
| C06 | 图书馆与信息化 |
| C07 | 医疗与心理 |
| C08 | 研究生事务 |
| C09 | 国际交流 |
| C10 | 学术与竞赛 |
| C11 | 行政与规章 |
| C12 | 院系与学校 |

### 4.3 映射表（v1 → v2）

| v1 旧分类 | v2 新分类 | 备注 |
|-----------|----------|------|
| 教务与课程 | C01 教务与学籍 | — |
| 学籍与教务 | C01 教务与学籍 | — |
| 入学与学籍 | C01 教务与学籍 | — |
| 学业管理 | C01 教务与学籍 | — |
| 教学与培养 | C01 教务与学籍 | — |
| 学业发展 | C01 教务与学籍 | — |
| 校园生活与服务 | C02 校园生活 | — |
| 生活服务 | C02 校园生活 | — |
| 学生服务 | C02 校园生活 | — |
| 财务与缴费 | C03 财务与缴费 | — |
| 奖助贷补 | C04 奖助学金 | — |
| 学生资助 | C04 奖助学金 | — |
| 毕业与就业 | C05 就业与毕业 | — |
| 就业与毕业 | C05 就业与毕业 | — |
| 图书馆服务 | C06 图书馆与信息化 | — |
| 图书馆 | C06 图书馆与信息化 | — |
| 信息化服务 | C06 图书馆与信息化 | — |
| 心理与测评 | C07 医疗与心理 | — |
| 心理健康 | C07 医疗与心理 | — |
| 研究生教育 | C08 研究生事务 | — |
| 研究生事务 | C08 研究生事务 | — |
| 招生与深造 | C08 研究生事务 | — |
| 国际交流 | C09 国际交流 | — |
| 竞赛与第二课堂 | C10 学术与竞赛 | — |
| 科研与创新 | C10 学术与竞赛 | — |
| 证件与校园服务 | C11 行政与规章 | — |
| 事务申请与审批 | C11 行政与规章 | — |
| 学生管理 | C11 行政与规章 | — |
| 校园安全 | C11 行政与规章 | — |
| 院系与专业 | C12 院系与学校 | — |
| 学校概况 | C12 院系与学校 | — |

> 所有 v1 分类均有对应 v2 分类，**无丢弃项**。

---

## 5. 数量清点

| 指标 | 数值 | 说明 |
|------|------|------|
| **预期（任务描述）** | 960 | W1-FINAL-REPORT.md 中 P3.1 合并后的数字 |
| **实际（final-merged）** | **835** | 经 W1-POST-CLEANUP-REPORT.md 去重合并后的真实有效数量 |
| **差异原因** | −125 | 960 条存在 111 组重复标题（236 个重复文件），经 R1 删除 82 个完全重复副本 + R2 合并 27 组（吸收 43 个副本），最终 835 条 |
| **Dify 现状** | 835 | POST-CLEANUP 后 Dify 数据集已与本地 835 条完全同步 |

### 分类分布（835 条实际）

| 分类 | 数量 |
|------|------|
| 教务与学籍 | 132 |
| 医疗与心理 | 125 |
| 行政与规章 | 119 |
| 学术与竞赛 | 97 |
| 就业与毕业 | 77 |
| 奖助学金 | 50 |
| 校园生活 | 50 |
| 院系与学校 | 47 |
| 研究生事务 | 43 |
| 图书馆与信息化 | 42 |
| 国际交流 | 29 |
| 财务与缴费 | 24 |
| **合计** | **835** |

> ⚠️ **对 Executor 的关键提醒**：若任务 spec 中仍写 "960 条"，需以 Scout 报告的 **835** 为准。这是 POST-CLEANUP 后的真实数字，本地与 Dify 已 100% 对齐。

---

## 6. 样本展示

### 样本 1：医疗与心理（C07-001，大文档模式）

**文件**：`final-merged/医疗与心理/KB-V2-C07-001.md`

```yaml
---
doc_id: "KB-V2-C07-001"
title: "后勤管理部 — 校医院医疗服务指南"
category: "医疗与心理"
tags:
  - 校医院
  - 医疗
  - 医保
  - 接种门诊
  - 济南校区
  - 泰安校区
sources:
  - type: "website"
    path: "W2/scraped-pages/后勤管理部/fwztc_ylfw.htm.md"
campus: "通用"
last_verified: "2026-04-16"
---
```

正文含 3 个 `##` 知识点（校医院概况与科室设置、主要职能与服务、联系方式），知识点间以 `---` 分隔，总长度约 600 字。

### 样本 2：奖助学金（C04-001，多 source）

**文件**：`final-merged/奖助学金/KB-V2-C04-001.md`

```yaml
---
doc_id: "KB-V2-C04-001"
title: "学生工作部（武装部）—— 奖助与勤工助学指南"
category: "奖助学金"
tags:
  - 弘毅奖学金
  - 勤工助学
  - 学生资助
  - 学工部
  - 奖助学金
  - 岗位申请
sources:
  - type: "website"
    path: "W2/scraped-pages/学生工作部（武装部）/bmjs_bmzz.htm.md"
  - type: "website"
    path: "W2/scraped-pages/学生工作部（武装部）/info_1341_21411.htm.md"
  - type: "website"
    path: "W2/scraped-pages/学生工作部（武装部）/info_1341_21441.htm.md"
  - type: "website"
    path: "W2/scraped-pages/学生工作部（武装部）/info_1341_21451.htm.md"
campus: "通用"
last_verified: "2026-04-16"
---
```

正文含 5 个 `##` 知识点（部门职责、弘毅奖学金条件、评选程序、勤工助学岗位、上岗申请流程、联系方式），总长度约 1200 字。

### 样本 3：教务与学籍（C01-001，含精读说明）

**文件**：`final-merged/教务与学籍/KB-V2-C01-001.md`

```yaml
---
doc_id: "KB-V2-C01-001"
title: "发展规划与学科建设部（教学评估办公室）— 教学巡查与督导工作指南"
category: "教务与学籍"
tags:
  - 教学巡查
  - 教学督导
  - 教学质量
  - 课堂纪律
  - 教务管理
  - 发展规划
sources:
  - type: "website"
    path: "W2/scraped-pages/发展规划与学科建设部（教学评估办公室）/"
campus: "通用"
last_verified: "2026-04-16"
---
```

正文含 5 个 `##` 知识点 + 末尾一段 `## 精读说明`（元数据注释，非知识点），总长度约 800 字。

> **观察**：v2 单条长度普遍大于 v1（v1 通常 200–400 字，v2 通常 500–1500 字）。这是因为 v2 按主题/部门合并为大文档模式，一个 `.md` 文件覆盖多个知识点（以 `##` 切分）。这对 Dify `create_document_by_text` 的上传策略无影响，但会影响 PG `kb_entries` 表中 `title` 的粒度（v2 标题是部门级，v1 标题是问题级）。

---

## 7. 推荐 Executor 做法

### 7.1 迁移脚本 `--entries-dir` 调整
- **旧值**：`../yixiaoguan/knowledge-base/entries`
- **新值**：`C:\Users\Administrator\Documents\code\kb-pipeline\04-output\final-merged`
- **扫描方式**：由于 v2 文件分布在 12 个子目录中，`entries_dir.glob("KB-*.md")` 必须改为 **`entries_dir.rglob("KB-*.md")`**（递归扫描）。

### 7.2 字段转换逻辑（`parse_frontmatter` 层）
1. **`sources` → `original_source`**：
   - v2 的 `sources` 是对象数组，脚本需取 `sources[0].path` 填入 `original_source`。
   - 若 `sources[0].type == "website"` 且同目录下存在对应 `.md` 源文件，可尝试从中提取 `source_url`；否则 `source_url` 留空。

2. **`doc_id` → `material_id`**：
   - 建议将 v2 的 `doc_id`（如 `KB-V2-C07-001`）写入 `kb_entries.material_id`，保留唯一标识便于溯源。

3. **`campus` 归一化**：
   - v2 理论上已归一化为 `通用` / `济南校区` / `泰安校区`，但脚本应做防御性校验，遇到空值默认填 `"通用"`。

### 7.3 分类映射层
- **建议独立函数** `normalize_category(v1_category: str) -> str`，使用第 4 章的映射表。
- 虽然本次迁移是从 **v2 直接入库**（v2 的 `category` 已合规），但若未来需要处理 v1 → v2 的混合格式迁移，该函数必备。
- 当前 v2 的 `category` 值已完全落在 12 分类内，可直接信任，但仍建议加断言校验：
  ```python
  assert category in ALLOWED_CATEGORIES, f"非法分类: {category}"
  ```

### 7.4 其他注意事项
1. **文档标题重复**：v2 经过 POST-CLEANUP 后唯一标题率 100%，但 Dify 上传时仍建议以 `title` 作为 `name`，无需额外加 `doc_id` 后缀（W1 早期曾用 `{title} [{doc_id}]` 格式导致名称不一致，现已统一为纯 `title`）。

2. **`last_verified` 字段**：当前 PG `kb_entries` 表无此字段。如需记录，需先跑 Alembic migration 新增字段；如不需要，可忽略。

3. **速率限制**：v2 单条长度显著大于 v1（平均 800–1200 字 vs 200–400 字），`create_document_by_text` 的耗时可能增加。建议保持 `RATE_LIMIT = 0.5` 或适当提高到 `1.0` 秒，避免触发 Dify API 限流。

4. **回滚与备份**：
   - 迁移前必须 `pg_dump yixiaoguan_v2 kb_entries > kb_entries_backup_$(date +%Y%m%d).sql`
   - 建议**不要直接删除旧 Dataset**，而是创建新 Dataset（如 `global-kb-v2`），测试通过后再切换 gateway 的 `dify_global_dataset_id`。

5. **脚本位置勘误**：任务描述写 `services/gateway/scripts/migrate_kb.py`，实际文件位于 **项目根目录的 `scripts/migrate_kb.py`**。Executor 不要创建重复文件。

---

## 8. 已知陷阱（补充）

| 陷阱 | 影响 | 规避方法 |
|------|------|---------|
| 960 vs 835 的数量偏差 | Executor 按 960 写循环/进度条会报错或悬空 | 以 Scout 报告 835 为准，用 `len(md_files)` 动态获取 |
| v2 文件在子目录 | `glob` 非递归会返回 0 文件 | 改用 `rglob("KB-*.md")` |
| v2 单条体积大 | Dify API 超时风险 | 保持 timeout=60s 或适当加大 |
| `sources` 是数组 | `meta.get("source")` 会返回 None | 改为 `meta.get("sources", [{}])[0].get("path", "")` |
| v2 标题是部门级 | 与用户问题粒度不完全对齐 | 不影响入库，RAG 按段落召回，不影响效果 |
| Dify 已存在 835 条 | 如果目标是"替换"而非"追加"，需先清旧 dataset | 建议走"新建 dataset → 切 gateway 配置"路线，而非物理删除 |

---

*报告完成。本报告仅做信息侦察，未修改任何代码或数据。*
