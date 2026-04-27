# R04-N1 / D1 交付报告 — Dify Chatflow 用户上下文集成

**任务编号**：R04-N1（D1）
**交付日期**：2026-04-27
**验收结论**：**PASS** — 端到端验证通过，AI 回答带强上下文意识

---

## 一、需求回顾

来自 `docs/requirements/R04-v2-新增需求.md` § N1：

> Dify Chatflow 分支优化 — 已确认不加新分支，但需要微调：
> - RAG 检索后的 LLM prompt 加入用户上下文（college_name, campus）
> - 意图分类的 inputs 增加用户属性字段

## 二、交付内容

### 2.1 Backend 代码改动（gateway）

| 文件 | 类型 | 说明 |
|---|---|---|
| `services/gateway/app/models/user.py` | 修改 | `College` model 加 `campus: Mapped[Optional[str]]` 列 |
| `services/gateway/app/routers/chat.py` | 修改 | `build_dify_inputs()` 重命名 `class_id` → `class_name`；`campus` 改读 `user.college.campus` |
| `services/gateway/alembic/versions/b4592e64bdd6_colleges_add_campus.py` | 新增 | alembic migration 加 colleges.campus varchar(64) 列 |
| `services/gateway/tests/test_chat_dify_inputs.py` | 新增 | 4 个单元测试覆盖 build_dify_inputs 各分支 |
| `services/gateway/tests/test_chat_inputs.py` | 修改 | 同步字段名 class_id → class_name |
| `services/gateway/tests/test_ai_pause_resume.py` | 修改 | 同步字段名 class_id → class_name |

**Migration 链**：`c4a81b9d1e21` → `b4592e64bdd6` (head)

**测试结果**：62 passed, 0 failed（含 D1 新增 4 个）

### 2.2 Dify Chatflow 配置（DSL 覆盖导入）

| 项目 | 内容 |
|---|---|
| 文件 | `scripts/chatflow_v2_d1.yaml`（14,253 bytes） |
| App | 医小管-主对话流（id `8cfaee92-f95c-4316-80a4-ab5d93614772`） |
| 导入方式 | Dify 1.13.3 UI "Import DSL" 覆盖导入 |
| 新 workflow id | `0bc6108d-a2a3-417e-9e5d-efe7bc5222cf`（2026-04-27 13:54 published） |

**改动节点**：

1. **Start 节点**（id `1000000000001`）— 添加 3 个变量：
   - `college_name`：text-input，max_length=48，optional
   - `campus`：text-input，max_length=48，optional
   - `class_name`：text-input，max_length=48，optional

2. **RAG LLM 节点**（id `1000000000031`）— system prompt 占位符替换：
   - **BEFORE**：`【学生上下文】当前学生：（这里插入变量，见下方说明）`
   - **AFTER**：`【学生上下文】当前学生：{{#1000000000001.college_name#}} {{#1000000000001.class_name#}} {{#1000000000001.campus#}}。`

3. **闲聊 LLM 节点**（id `1000000000020`）— system prompt 末尾追加：
   ```
   当前学生来自 {{#1000000000001.college_name#}} 学院，可适当关联校园场景并调整语气。
   ```

### 2.3 数据库种子升级（colleges 表）

**策略**：选项 D（按真实 21 学院重建），用 in-place UPDATE 保留 user.college_id FK 关联，零迁移风险。

| 操作 | 行数 | 备注 |
|---|---|---|
| UPDATE | 4 | id=1..4 改名 + 加 campus（保留 FK 引用） |
| INSERT | 17 | id=5..21 新学院 |
| 总计 | **21** | 济南校区 12 + 泰安校区 9 |

**Mapping 文档**：`docs/data/colleges-campus-mapping.md`（61 行，git rev 479782b）

**SQL 脚本**：`/tmp/seed_real_colleges.sql`（执行于 165 yx_postgres）

**用户 / 班级 关联保持**：
- users.college_id 分布：id=1(2 users), id=2(1 user) — 不变
- classes.college_id 分布：id=1(1 班), id=2(1 班) — 不变

### 2.4 文档新增

| 文件 | 内容 |
|---|---|
| `docs/data/colleges-campus-mapping.md` | 21 学院 ↔ 5 校区权威映射，附 kb-pipeline 数据来源置信度 |
| `.tasks/reports/r04-n1-d1-delivery.md` | 本报告 |

## 三、端到端验证证据

### 3.1 Smoke test（165 远端）

- **测试用户**：stu1 (`2024010001` 张小洋)
  - college_id=1 → 临床与基础医学院 / 济南校区
  - class_id → 临床2024-1班
- **会话**：conv_id=37
- **问题**：`我想了解一下我们学院的奖学金政策，应该怎么申请？`
- **AI 答复开头**：
  > 你好！**临床与基础医学院**的奖学金政策主要包含国家奖学金、省政府奖学金、国家励志奖学金和校级综合奖学金等几类（见《学生手册 第三章》）。
- **上下文意识等级**：**Strong** — AI 在第一句话就明确点名学院

### 3.2 Dify 端 inputs 接收验证

`messages.inputs` JSON：
```json
{"college_name": "临床与基础医学院", "campus": "济南校区", "class_name": "临床2024-1班"}
```

✅ 三字段全部正确传输

### 3.3 Gateway 健康检查

```json
{"status": "ok", "version": "2.0.0", "checks": {"postgres": "ok", "redis": "ok", "dify": "ok"}}
```

### 3.4 单元测试

- `test_chat_dify_inputs.py`: 4/4 pass（D1 新增）
- `test_chat_inputs.py`: 3/3 pass（字段名同步）
- `test_ai_pause_resume.py`: 9/9 pass（字段名同步）
- 全套：62 passed, 0 failed

## 四、已知限制与后续待办

### 4.1 colleges 数据是 one-off SQL，不在 alembic data migration

165 上 colleges 表升级到 21 学院是通过 `/tmp/seed_real_colleges.sql` 一次性 INSERT/UPDATE 落地的，**不在** alembic migration 链中。这意味着：

- ✅ 165 生产环境正常运行
- ⚠️ 任何 fresh dev DB / staging DB 仍是旧 4 学院测试 seed
- 🔜 待后续正式 prod 部署 V2 时，把 21 学院 seed 落到一个 data migration（建议 idempotent 写法 INSERT ON CONFLICT）

### 4.2 双校区学院降级处理

医学信息与人工智能学院实际为济南+泰安双校区。当前 colleges.campus 只支持单值，已选择"济南校区"作为主校区（其行政主体）。后续如需精细化，可：
- 加 `campus_secondary: Optional[str]` 列
- 或改用 ARRAY(String) 类型存多校区

### 4.3 历下校区 / 章丘校区 / 天外村校区

校章程列出的 5 校区中，3 个在抓取数据中无明确教学学院归属。`docs/data/colleges-campus-mapping.md` 已记录这一事实，留后续运营补充。

### 4.4 Worktree 临时文件

worktree 里 `scripts/kimi-task-*.txt` 是 cascade 下发任务的临时 prompt，**不需要进 git**。建议 `.gitignore` 加 `scripts/kimi-task-*.txt` 或本地清理。

## 五、给 user 的 git 同步建议

D1 改动当前在 165 working tree (`/home/easten/dev/yixiaoguan-v2/`) 里，未 commit 到主仓 master。建议步骤：

1. **本地主仓**：mutagen 应已自动同步 165 改动 → 主仓 working tree
2. **检查改动 scope**：`git status && git diff --stat`
3. **commit + push**（建议 commit message 模板）：
   ```
   feat(D1/R04-N1): Dify chatflow user context integration

   - colleges table: add campus column + rebuild to real 21 colleges
   - gateway: build_dify_inputs renames class_id→class_name, reads user.college.campus
   - alembic: migration b4592e64bdd6 colleges_add_campus
   - tests: 4 new unit tests in test_chat_dify_inputs.py, 62 passed
   - chatflow DSL: chatflow_v2_d1.yaml imported to Dify (workflow 0bc6108d-...)
   - docs: docs/data/colleges-campus-mapping.md authoritative mapping
   ```
4. **Worktree 清理**（可选）：删除 `scripts/kimi-task-*.txt` 临时 prompt

---

**报告作者**：Cascade（T0 总协调）
**远端执行**：Kimi CLI（T3 执行子代理）
**TX 操作**：Dify UI DSL 导入 + Publish
**审阅 / 验收**：（user 签收）
