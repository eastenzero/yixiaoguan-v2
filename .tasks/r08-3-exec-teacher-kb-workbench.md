---
id: "r08-3-exec-teacher-kb-workbench"
parent: "R08-3"
type: "feature"
status: "pending"
tier: "T3"
priority: "high"
risk: "medium"
foundation: false

scope:
  - "apps/teacher-app/src/pages/knowledge/index.vue"
  - "apps/teacher-app/src/pages/knowledge/detail.vue"
  - "apps/teacher-app/src/pages.json"
  - "apps/teacher-app/src/api/knowledge.ts"
  - "apps/teacher-app/src/types/api.ts"
  - "apps/teacher-app/src/stores/user.ts"
  - ".tasks/reports/r08-3-exec-teacher-kb-workbench_report.md"

out_of_scope:
  - "services/gateway/app/routers/chat.py"
  - "services/gateway/app/services/analytics.py"
  - "复杂富文本编辑器"
  - "草稿协同 / 多人并发编辑"
  - "管理员审核后端逻辑"

context_files:
  - "docs/requirements/R08-教师-KB-运营闭环.md"
  - ".tasks/r08-2-exec-unanswered-top-api.md"
  - ".tasks/r08-4-exec-polish-draft-publish.md"
  - "apps/teacher-app/src/pages/knowledge/index.vue"
  - "apps/teacher-app/src/pages/knowledge/detail.vue"
  - "apps/teacher-app/src/utils/request.ts"
  - "apps/teacher-app/src/types/api.ts"

done_criteria:
  L0: "教师端知识库页形成最小闭环：能看到高频待补问题、选择 scope、填写教师答复、提交后收到‘已发布’或‘待审核’反馈；管理员账号进入同一页面时可看到审核列表入口"
  L1: "teacher-app type-check 通过；无新增编译错误；原有知识库页与详情页仍可打开"
  L2: "165 联调：教师登录后可从知识页发起一次班级/学院范围答复并成功提交；管理员登录后可看到待审核条目数量或列表"
  L3: "UI 不要求精装修，但状态必须清晰：待补问题、答复中、提交成功、提交失败、待审核"

depends_on:
  - "r08-2-exec-unanswered-top-api"
  - "r08-4-exec-polish-draft-publish"
created_at: "2026-04-21"
---

# R08-3 Executor · 教师端 KB 运营工作台

> **目标状态**：教师端不再只是“浏览知识库”，而是具备最小运营能力：看到高频待补问题、填写答复、选择发布范围、提交生成知识条目。管理员账号复用同一页面体系进入审核模式。

## 背景

当前 `teacher-app` 已经存在 `pages/knowledge/index.vue` 和 `pages/knowledge/detail.vue` 的页面骨架，但它们仍面向旧的“知识库浏览”场景，且网关没有完整匹配的后端。R08-3 的目标是**最小改造现有页面**，复用导航与视觉结构，不新开一套独立 admin-app。

## 必读上下文

1. `apps/teacher-app/src/pages/knowledge/index.vue`
2. `apps/teacher-app/src/pages/knowledge/detail.vue`
3. `apps/teacher-app/src/api/knowledge.ts`
4. `apps/teacher-app/src/stores/user.ts`
5. `.tasks/r08-2-exec-unanswered-top-api.md`
6. `.tasks/r08-4-exec-polish-draft-publish.md`

## 执行重点

### 1. 页面职责重排

`pages/knowledge/index.vue` 改造成 2 个主视图：

- **教师视角**
  - Tab A：`高频待补`
  - Tab B：`我的知识`

- **管理员视角**
  - Tab A：`待审核`
  - Tab B：`知识库`

管理员/教师均复用同一页面，通过 `userInfo.role` 区分，不新建独立端。

### 2. 高频待补卡片最小字段

每张卡片至少展示：

- 问题文本
- 命中次数 `hit_count`
- 最近出现时间 `latest_at`
- 一个“去补充”按钮

点击“去补充”后，在当前页弹出或展开一个**简表单**：

- `raw_answer` 文本域
- `scope` 单选：`class` / `college` / `global`
- 提交按钮

### 3. 提交流程

对接 R08-4 的提交接口：

```ts
POST /api/v1/knowledge/drafts
```

提交后前端根据响应里的 `publish_mode` 做区分：

- `published` → toast `已发布到知识库`
- `pending_review` → toast `已提交管理员审核`

提交成功后：

- 从“高频待补”列表移除该项，或重新刷新列表
- “我的知识”列表同步刷新

### 4. 详情页兼容

`pages/knowledge/detail.vue` 保留详情查看能力，但要兼容新状态：

- `已发布`
- `审核中`
- `已驳回`
- `已下线`

如果后端返回 `reject_reason`，详情页应有位置展示。

### 5. 约束

- 不引入富文本编辑器
- 不做草稿自动保存
- 不做复杂状态管理，局部 `ref` 即可
- 不改底部导航结构，知识库页仍然是 tab 入口

## 联调接口最小集

前端至少需要封装：

- `getUnansweredTop(limit)`
- `createKnowledgeDraft(payload)`
- `getKnowledgeEntries(params)`
- `getKnowledgeDetail(id)`
- `getPendingReviews(limit)`（管理员）
- `approveKnowledge(id)` / `rejectKnowledge(id)`（管理员可放在 R08-5 页面按钮中接）

## 测试 / 验收方式

本任务以 **type-check + 人工联调** 为主：

1. `npm run type-check` 或等价命令通过
2. 教师账号能成功提交一条知识答复
3. 管理员账号能看到待审核列表入口
4. 页面空态、加载态、错误态都存在

## 已知陷阱

- 不要把教师端页面写死成仅教师可见；管理员也要复用
- 不要假设后端总会返回 `rows`；对空数组做兜底
- 不要把 role 判断散落太多处，尽量在页面顶部统一派生 `isAdmin`
- 避免一次性大改样式，优先保证流程通

## 报告应包含

1. 页面改造前后对照
2. 教师/管理员两种视角的核心截图
3. 联调接口清单
4. 已知未做项（若有）
5. type-check 结果

## 回滚方案

- 恢复 `knowledge/index.vue` 与 `knowledge/detail.vue`
- 恢复 `api/knowledge.ts` 改动
- 不影响其他 tab 页
