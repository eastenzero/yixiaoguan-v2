# 医小管 KB 整合规划 v1

## 数据现状

| 来源 | 路径 | 条数 | 命名 | frontmatter | 质量 |
|---|---|---|---|---|---|
| v1 entries | `code\yixiaoguan\knowledge-base\entries\` | 432 (排除 SUMMARY) | `KB-NNNN-名字.md` 22 + `KB-YYYYMMDD-NNNN.md` 410 | material_id/title/category/tags/source/status/source_url/campus | active 190 / draft 196 / needs_review 1 / 无 status 45 |
| v2 final-merged | `code\kb-pipeline\04-output\final-merged\` | 835 | `KB-V2-CXX-NNN.md`（CXX = 学院/分类编码） | doc_id/title/category/tags/sources(数组多源)/campus/last_verified | 全 final，无 status 字段 |
| **重叠** | (filename) | **0** | 命名方案完全不同 | — | — |

**主题重叠**：必有（如奖学金、心理咨询、宿舍管理两边都出现），但 zero filename overlap 决定**必须语义去重，不能 dedupe by name**。

---

## 整合 plan（6 阶段）

### Phase 0 ✅ 数据盘点
完成。v1 432 + v2 835 = 1267 候选。

### Phase 1 — 分类对齐（Kimi 1 个任务，10min）
- 输入：两边的 category 字段分布
- 输出：unified-categories 映射表
  - 例：v1.`学生资助` + v2.`奖助学金` → unified.`奖助学金`
  - 例：v1.`生活服务` + v2.`校园生活` → unified.`校园生活`

### Phase 2 — 语义聚类找同主题（自动化，10min DashScope embedding 成本几毛）
- 1267 条全部 embedding（DashScope text-embedding-v3）
- 1267×1267 cosine similarity 矩阵
- 取 cosine > 0.80 的「疑似重复」对，输出 candidates.csv

### Phase 3 — 合并决策（Kimi + Codex **并行**处理疑似重复对，30min）
- 派 Kimi 跑 50% 候选对，Codex 跑 50%
- 对每对疑似重复，让 LLM 判断：
  - keep_v1 / keep_v2 / merge_both / not_duplicate
  - 若 merge：生成融合版（保留 v1 操作步骤 + v2 官方信息 + 多 source 追溯）
- 输出 decisions.csv → 自动应用

### Phase 4 — 统一 schema（Codex 批量改写，30min）
- 全部条目转成统一 v2.5 schema：
  ```yaml
  doc_id: "KB-V2-CXX-NNN"      # 重新编号
  title: ...
  category: <unified-category>
  tags: [...]
  sources: [{type, path, page?}]
  campus: ...
  last_verified: "YYYY-MM-DD"
  status: "published"           # 全部转为 published
  legacy_id: <原 v1 文件名 OR 原 v2 doc_id>
  ```
- v1 draft/needs_review 全标 published（需要后续 polish 的列入 followup.txt）

### Phase 5 — 质量校验（Kimi 抽样 30 条，10min）
- 随机抽 30 条转换结果
- 报告：frontmatter 完整度、正文质量、潜在丢信息

### Phase 6 — 入库（自动，12min）
1. 删 HK Dify 现有 432 条
2. 跑 migrate_kb.py 导入 ~1000-1100 条整合版
3. embedding indexing + retry rate-limited
4. chatflow 重发布（dataset 选中）

**总耗时估算**：~2 小时（不含人工 review）

---

## 备选方案：最小可行版（今晚 1 小时完成）

跳过 Phase 2-4 语义合并，直接：

1. **Phase 1 简化**：分类映射（Kimi 5min）
2. **Phase 4 简化**：v1 + v2 全部转 v2.5 schema（Codex 20min，机械操作不需要语义）
3. **Phase 6 入库**：删旧 + 导新 1267 条
4. **依赖 dify rerank**：chatflow 已有 qwen3-rerank 节点，重复主题靠 rerank 选最优 1-2 条返回 LLM

风险：同一问题可能被 v1 + v2 两个文档同时检索到，rerank 调序但 prompt 里仍含两份 → LLM 可能输出"我有两份资料显示..."等怪异表述。可后续观察 chat 实际质量再决定要不要回头做完整 plan。

---

## 任务派发（如选完整 plan）

| Phase | 工具 | 并行度 | 说明 |
|---|---|---|---|
| 1 分类对齐 | Kimi 1x | 1 | 单任务 |
| 2 embedding+cluster | python script | — | 跑 DashScope batch |
| 3 合并决策 | Kimi + Codex 并行 | 2 | 对半分疑似对 |
| 4 schema 转换 | Codex | 4 并行子任务（v1-22, v1-410, v2-835/2, v2-835/2） | 4 进程 |
| 5 抽样校验 | Kimi 1x | 1 | 单任务 |
| 6 入库 | 我 (cascade) | 1 | 自动化脚本 |
