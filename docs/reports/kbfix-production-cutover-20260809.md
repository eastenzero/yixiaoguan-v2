# Dify 知识库正式切换与协作交接记录

日期：2026-08-09
服务器：`tx-new`
状态：`PRODUCTION_ACTIVE`
正式切换完成时间：`2026-08-09T21:23:32+08:00`

## 任务与结论

本轮任务是在已完成蓝绿重建和 120 条验收的基础上，经人工确认执行正式替换，同时保留一键反向回滚能力；随后将实施任务、决策、运行证据和协作信息提交 Git 并写入服务器日志。

正式替换已经完成。原 App 和已有会话继续使用，正式 App 只发布了经过验收的新工作流；Gateway、教师知识条目及 Dify API/Worker/Beat 同步切换到绿版和 `kbfix` 镜像。5 条生产冒烟全部通过，7 次连续观察无错误，正式会话计数在切换前后均为 1,122。当前具备正式上线能力，且已处于生产运行状态。

## 当前生产指针

| 项目 | 当前值 | 回滚值/说明 |
|---|---|---|
| 正式 App | `8cfaee92-f95c-4316-80a4-ab5d93614772` | App 未更换，保障会话连续 |
| 正式工作流 | `bd5b740d-1302-49fc-83b5-4a521f83dd5e` | 原工作流 `f98baa82-d73f-44b0-aec5-de83078e8b37` |
| 正式主库 | `a5732fe1-a85c-42a8-962c-2a4d8015b56a` | 原主库 `4db0c819-7847-4a95-bf06-5b73a9d41d70` |
| 学业影响专项库 | `6f8c8f85-9893-4036-b327-15c34ccb9aa5` | 独立路由 |
| 奖学金备库 | `5a3c8e8f-b2b5-46b3-b350-f63c086c62de` | 只保留备用，正式流程不重复检索 |
| Shadow App / Workflow | `76f7ba2c-5c61-47cb-a257-5800cf185e21` / `882b1331-6721-4dbe-acca-9d630d0cad37` | 验收基线保留至少 14 天 |
| 正式镜像 | `yixiaoguan/dify-api:1.13.3-kbfix-20260809` | API、Worker、Beat 均已启用 |
| 镜像 ID | `sha256:fe3dc3d5e946b42eaa2ab4fbc56ba83ff1b0cee8bd92e49dc4a08e7317c4a141` | 原镜像 ID `sha256:d1c73b3be4ba3212d4119c77e15230215e8bcf760ed64f80cfea121c277e1108` |

正式工作流继续使用 `qwen3.6-plus`、`qwen3-rerank`、Top-6 和安全提示词。普通校园咨询及奖学金检索绿版主库；挂科、不及格、补考、重修、补修以及对入党、奖学金、评优影响的问题路由至中文标题专项库。

## 切换内容

1. 在写操作前再次验证完整备份、SHA256 清单、恢复演练、活动队列、镜像、正式工作流指针、Gateway Dataset ID 和教师映射状态。
2. 为本次切换创建即时恢复点 `/home/easten/backups/yixiaoguan-v2/switch-20260809-212238`。
3. 将 Dify API、Worker、Worker Beat 切换为不可变 `kbfix` 镜像。
4. 在原正式 App 下发布生产工作流 `bd5b740d-1302-49fc-83b5-4a521f83dd5e`，没有更换 App、API Key 或 conversation ID。
5. 将 Gateway 主库指针切换至 `a5732fe1-a85c-42a8-962c-2a4d8015b56a`。
6. 原子更新 319 条可精确映射的教师知识条目：`old=319,new=0` 变为 `old=0,new=319`。另外 949 条未匹配历史条目继续冻结，没有被误改。
7. 完成 Gateway 健康检查、正式 API 冒烟、服务日志检查、队列和 Redis 观察。

## 验收指标

切换前冻结的 120 条验收集全部完成。最终绿版指标如下：

| 指标 | 结果 |
|---|---:|
| Segment ↔ Vector 覆盖 | 主库 740/740、专项 55/55、备库 145/145，均为 100% |
| UUID 与 `doc_id/index_node_id` 一致 | 100%，不一致 0 |
| 陈旧向量 / 重复正文 / 待核实活动内容 | 0 / 0 / 0 |
| 主库综合 Top-1 / Top-3 | 97.87% / 100% |
| 学业影响 Top-1 / Top-3 | 100% / 100% |
| 端到端可用率 / 错误率 | 100% / 0% |
| 严格精准率 / 语义复核精准率 | 99.17% / 100% |
| 安全拒答通过率 | 100% |
| 双并发 P95 / 最大延迟 | 5.99 秒 / 6.69 秒 |

正式切换后的生产验证：

- 冒烟：5/5 PASS；覆盖选课、学业影响路由、国家奖学金、伪造票据拒答、历史奖学金公示。
- 路由：5/5 命中预期 Dataset。
- 会话连续性：正式 conversation 数 `1122 → 1122`。
- Gateway：`postgres=ok`、`redis=ok`、`dify=ok`。
- 连续观察：7 个样本、每 30 秒一次，队列始终为 0；API healthy，Worker/Beat running。
- 切换后错误：API 0、Worker 0、Worker Beat 0、Gateway 0。
- Redis：`1.92 MB`。

运行证据位于 [production-cutover](kbfix-20260809/production-cutover/)；完整切换前验收见 [蓝绿修复最终验收报告](kbfix-green-release-20260809.md)。

## 异常与处置记录

本轮保留了两次未成功执行的真实记录，便于后续协作排查：

- 首次调用在任何生产写入前停止。原因是切换脚本把初始备份成功标志误认为根目录 `PASS`，而真实恢复演练证据位于 `metadata/restore-drill.txt`。修正预检条件后重新执行，生产状态未发生变化。
- 第一次实际切换的恢复点为 `/home/easten/backups/yixiaoguan-v2/switch-20260809-212031`。Gateway 容器重启后尚未就绪，立即健康检查失败，自动回滚于 `21:21:34` 完成；正式工作流、319 条教师映射、Gateway Dataset ID 和原镜像全部恢复，没有残留半切状态。
- 同时修复了失败 trap 在回滚后可能继续执行的问题：现在会移除 `ERR` trap、执行回滚并强制以非零状态退出；Gateway 健康检查改为最多等待 120 秒，并且必须返回 `status=ok`。自动回滚只有在原镜像、原工作流、原教师映射和 Gateway 全部校验通过后才写 `FAILED_ROLLED_BACK`，否则写 `FAILED_ROLLBACK_INCOMPLETE`，避免产生虚假的成功标志。
- 修正后于 `/home/easten/backups/yixiaoguan-v2/switch-20260809-212238` 完成正式切换，`21:23:32` 写入可信 `PASS`。失败恢复点中的误写标志已重命名为 `PASS.invalid-after-auto-rollback`，以免被协作者误判。

上述第一次实际切换的自动回滚记录已归档为 [first-attempt-FAILED_ROLLED_BACK](kbfix-20260809/production-cutover/first-attempt-FAILED_ROLLED_BACK)。

## 备份与恢复

- 完整初始恢复点：`/home/easten/backups/yixiaoguan-v2/kbfix-20260809-162508`
- 每日备份样本：`/home/easten/backups/yixiaoguan-v2/daily-20260809-163729`
- 成功切换即时恢复点：`/home/easten/backups/yixiaoguan-v2/switch-20260809-212238`
- 队列归档：`/home/easten/backups/yixiaoguan-v2/queue-archive-20260809-1642`，共 133,298 个任务
- 自动备份：每日 03:20，保留 14 天
- PostgreSQL 与 Weaviate 恢复演练：PASS

回滚命令：

```bash
ssh tx-new
/home/easten/dev/dify-deploy/kbfix-run-20260809/rollback_kbfix_remote.sh \
  --confirm ROLLBACK_KBFIX_20260809
```

回滚脚本会恢复原 Compose/镜像、原正式工作流、Gateway 原 Dataset ID 及 319 条教师映射。严重故障仍可使用完整快照恢复。

最终部署脚本 SHA256：

- `switch_kbfix_remote.sh`：`99462c9e6af9ae407a73ca0e82cdf02e2c70d0f14ce78a07b0e163b12bd4b794`
- `rollback_kbfix_remote.sh`：`8e61ba8a84730955f39c897ccf3aaddd8f994660558e48238ee14eed3d67eb16`

## 服务器协作入口

以下服务器文件面向后续合作开发：

- 总交接日志：`/home/easten/logs/yixiaoguan-kbfix-20260809.log`
- 可浏览交接文档：`/home/easten/dev/dify-deploy/kbfix-run-20260809/COLLABORATION-HANDOFF.md`
- 运行证据：`/home/easten/backups/yixiaoguan-v2/switch-20260809-212238`
- 工具与回滚包：`/home/easten/dev/dify-deploy/kbfix-run-20260809`
- Git 提交信息：`/home/easten/dev/dify-deploy/kbfix-run-20260809/git-commit.txt`

凭据轮换和历史 Git 凭据清理仍不在本轮范围。所有交付文件只记录 ID、摘要和证据路径，不写入 API Key、数据库密码或其他明文凭据。
