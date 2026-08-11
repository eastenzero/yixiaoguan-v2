# Dify 知识库蓝绿修复最终验收报告

> 后续状态更新（2026-08-09 21:23:32 +08:00）：经人工确认，绿版已正式切换并通过生产冒烟与观察。本文件保留切换前验收快照；当前生产状态及回滚信息见 [正式切换与协作交接记录](kbfix-production-cutover-20260809.md)。

日期：2026-08-09
服务器：`tx-new`
状态：`PASS_WAITING_SWITCH_CONFIRMATION`

## 结论

绿版已完成完整修复并通过本轮所有上线硬门槛，具备在人工确认后执行真实切换的技术条件。建议按既定维护窗口切换后先灰度观察，不直接跳过灰度全量放量。

本轮没有切换正式流量。正式 App、正式工作流、正式 API Key、Gateway Dataset ID 和已有 Dify conversation ID 均保持不变：

- 正式 App：`8cfaee92-f95c-4316-80a4-ab5d93614772`
- 正式工作流：`f98baa82-d73f-44b0-aec5-de83078e8b37`
- 正式主库：`4db0c819-7847-4a95-bf06-5b73a9d41d70`
- 正式 App `updated_at`：`2026-08-04 15:13:01.412709`，修复后未变化
- 正式 API/Worker/Beat 镜像：仍为原 `langgenius/dify-api:1.13.3`

当前明确处于“等待切换确认”状态。

## 最优版本

| 用途 | 选定版本 | Dataset ID | 结果 |
|---|---|---|---|
| 普通校园咨询与奖学金 | `医小管-GREEN-RC3-主库最终候选-20260809` | `a5732fe1-a85c-42a8-962c-2a4d8015b56a` | 47 条主库+奖学金检索 Top‑1 97.9%，Top‑3 100% |
| 学业影响专项 | `医小管-GREEN-RC6-学业影响最终候选-20260809` | `6f8c8f85-9893-4036-b327-15c34ccb9aa5` | 15 条 Top‑1/Top‑3/MRR 均 100% |
| 奖学金备库 | `医小管-GREEN-RC3-奖学金备库最终候选-20260809` | `5a3c8e8f-b2b5-46b3-b350-f63c086c62de` | Top‑1 95%，Top‑3 100%；仅保留备用，不接 Shadow |
| 端到端 App | `GREEN Shadow R7` | App `76f7ba2c-5c61-47cb-a257-5800cf185e21` / Workflow `882b1331-6721-4dbe-acca-9d630d0cad37` | 当前最终验收版 |

主库迭代从兼容候选 59.3%/70.4%，提升至 RC2 的 81.5%/96.3%，最终 RC3 在广域题上达到 100%/100%，与奖学金题合并后为 97.9%/100%。严格治理候选因覆盖不足仅 37.0%/44.4%，已作为失败对照冻结，没有被选中。

学业影响库比较了原 embedding 与 `text-embedding-v4`。初轮分别为 73.3%/86.7% 和 80%/100%；经过中文标题与窄路由卡修正，RC6 达到 100%/100%。奖学金库按 Top‑1、MRR、延迟顺序比较，最终 `text-embedding-v4` 候选达到 95%/100%，优于前序原 embedding 候选。

## 验收结果

| 硬门槛 | 要求 | 最终结果 | 状态 |
|---|---:|---:|---|
| Segment ↔ Vector 精确覆盖 | 100% | 主库 740/740、专项 55/55、备库 145/145 | PASS |
| 对象 UUID = `doc_id/index_node_id` | 100% | 身份不一致 0 | PASS |
| 陈旧向量 / 重复正文 / 待核实活动内容 | 0 | 0 / 0 / 0 | PASS |
| 综合检索 Top‑1 | ≥90% | 97.9% | PASS |
| 综合检索 Top‑3 | ≥96% | 100% | PASS |
| 学业影响 Top‑1 / Top‑3 | 100% / 100% | 100% / 100% | PASS |
| 端到端可用率 | ≥95% | 120/120，100% | PASS |
| 端到端精准率 | ≥85% | 严格字面 119/120，99.17%；语义复核 120/120 | PASS |
| Shadow 错误率 | <1% | 0% | PASS |
| Shadow P95 | ≤8 秒 | 双并发 P95 5.99 秒，最大 6.69 秒 | PASS |
| 安全拒答 | 无 P0/P1 | 10/10，100% | PASS |
| 跨学院、跨学年 | 无 P0/P1 | 10/10，100% | PASS |
| 429/中断恢复与幂等 | 可恢复、无重复 | 检查点恢复成功；重复执行待处理数 0、无重复对象 | PASS |

严格字面唯一未命中为 AC103：“今年所有学院奖学金最终名额各是多少”。回答明确表示无法提供、当前库未收录 2026 年各学院最终名额，并引导查询所在学院最新通知，与预期语义一致，人工证据复核为通过。冻结题目没有被修改。

Shadow 使用 `qwen3.6-plus`、`qwen3-rerank`、Top‑6 和完整安全规则。普通咨询只查绿版主库；普通奖学金仍走主库；挂科、不及格、补考、重修、补修及其对入党/奖学金/评优的影响走中文标题专项库。确定性分流消除了模型分类抖动，回答限长将首版双并发 P95 从 9.86 秒降到 5.99 秒。

详细证据：

- [120 条最终验收结果](kbfix-20260809/shadow-final-acceptance.json)
- [主库与奖学金检索结果](kbfix-20260809/retrieval-rc3-full-results.json)
- [学业影响专项检索结果](kbfix-20260809/retrieval-rc6-academic-results.json)
- [绿版发布状态校验](kbfix-20260809/green-release-verification.json)
- [主库/备库结构校验](kbfix-20260809/green-rc3-validation.json)
- [专项库结构校验](kbfix-20260809/green-rc6-academic-validation.json)

## 备份、恢复与队列

完整恢复点位于 `/home/easten/backups/yixiaoguan-v2/kbfix-20260809-162508`，包含两套 PostgreSQL、Weaviate、Redis、Dify storage、Compose 配置、正式工作流 DSL 和镜像信息，并有 SHA256 清单。

恢复演练结果：Dify 10 个 Dataset、1,763 个 Document、4,063 个 Segment、15 个 Workflow；业务库 1,268 条 `kb_entries`；Weaviate 10 个 Class、4,192 个 Object，全部恢复校验通过。每日 03:20 自动备份已启用，保留 14 天；首次自动备份 `daily-20260809-163729` 通过。

`trigger_refresh_publisher` 实际发现 133,298 个任务，已完整归档到 `/home/easten/backups/yixiaoguan-v2/queue-archive-20260809-1642`，恢复测试通过。10 分钟观察中活动队列除初始 1 条外持续为 0，Worker 无错误，Redis 内存稳定在约 1.1–1.45 MB；最终复核队列为 0。

证据：

- [初始恢复演练](kbfix-20260809/initial-restore-drill.txt)
- [每日备份通过记录](kbfix-20260809/daily-backup-pass.txt)
- [队列归档摘要](kbfix-20260809/metadata.txt)
- [队列 10 分钟观察](kbfix-20260809/observation.tsv)
- [Worker 错误记录](kbfix-20260809/worker-errors.txt)

## 修复镜像

- Tag：`yixiaoguan/dify-api:1.13.3-kbfix-20260809`
- Image ID：`sha256:fe3dc3d5e946b42eaa2ab4fbc56ba83ff1b0cee8bd92e49dc4a08e7317c4a141`
- Base：`sha256:d1c73b3be4ba3212d4119c77e15230215e8bcf760ed64f80cfea121c277e1108`
- Patch SHA256：`90e7fed837a2b63db89067bab6640a0f9cfd694b335764e60fb72fef87305bbf`
- 镜像内身份回归：PASS
- 当前状态：已暂存，未替换正式 API/Worker/Beat

证据：[镜像清单](kbfix-20260809/image-manifest.json)、[镜像内回归](kbfix-20260809/image-verification.txt)。

## 教师知识条目映射

绿版主库 350 个 Document 中，339 个可追溯到旧 UUID 文档，319 条业务 `kb_entries` 可建立精确旧新映射；另 11 个是本轮新增官方资料卡。其余 949 条历史业务条目不在绿版收录范围，保持原 ID 和原 Dataset 冻结，不会被切换脚本误改。

切换脚本只原子更新这 319 条精确映射；回滚脚本按业务条目 ID 和新旧双重条件反向恢复。映射状态演练结果为 `old=319, new=0, other=0, missing=0`。

证据：[教师条目旧新 ID 映射](kbfix-20260809/teacher-id-mapping.json)。

## 切换与回滚包

下列脚本已部署到服务器 `/home/easten/dev/dify-deploy/kbfix-run-20260809/`。默认不执行；缺少固定确认口令时均安全拒绝。

人工确认后执行正式切换：

```bash
ssh tx-new
/home/easten/dev/dify-deploy/kbfix-run-20260809/switch_kbfix_remote.sh \
  --confirm SWITCH_KBFIX_20260809
```

该脚本会再次验证备份、队列、镜像、正式工作流指针、Gateway Dataset ID 和 319 条教师映射；为本次切换新建即时恢复点；启用 kbfix 镜像；在原正式 App 下发布新工作流；更新 Gateway Dataset ID 和教师映射；检查 Gateway 健康和正式会话数量连续性。任一步失败都会自动回滚已执行阶段。

正式切换后的反向回滚：

```bash
ssh tx-new
/home/easten/dev/dify-deploy/kbfix-run-20260809/rollback_kbfix_remote.sh \
  --confirm ROLLBACK_KBFIX_20260809
```

当前尚未接流量的绿版若决定撤回，只需禁用 Shadow App，Dataset 保留 14 天：

```bash
ssh tx-new
docker cp /home/easten/dev/dify-deploy/kbfix-run-20260809/manage_shadow_app.py \
  docker-api-1:/tmp/manage_shadow_app.py
docker exec -e PYTHONPATH=/app/api -w /app/api docker-api-1 \
  python /tmp/manage_shadow_app.py disable \
  --confirm DISABLE_GREEN_SHADOW_20260809
```

本地交付脚本：

- [正式切换脚本](../../tools/kb_repair/switch_kbfix_remote.sh)
- [正式回滚脚本](../../tools/kb_repair/rollback_kbfix_remote.sh)
- [正式工作流发布器](../../tools/kb_repair/publish_formal_workflow.py)
- [教师 ID 映射器](../../tools/kb_repair/apply_teacher_id_mapping_remote.py)
- [Shadow 启停工具](../../tools/kb_repair/manage_shadow_app.py)
- [发布清单](../../deploy/dify/kbfix/release-manifest.json)

## 上线判断与边界

结论为：**具备真实上线能力，等待人工切换确认。**

该判断覆盖本方案要求的结构完整性、检索准确率、端到端正确性、安全边界、双并发延迟、队列恢复、备份恢复和反向回滚。上线仍应按维护窗口和灰度执行；如果预期同时并发远高于本轮双并发验收，应在全量放量前追加与目标峰值一致的容量测试。

凭据轮换和 Git 历史清理按范围约定未纳入本轮。
