# R08-3 Executor Report · 教师端 KB 运营工作台

## 改动文件

- `apps/teacher-app/src/pages/knowledge/index.vue`
- `apps/teacher-app/src/pages/knowledge/detail.vue`
- `apps/teacher-app/src/api/knowledge.ts`
- `apps/teacher-app/src/types/api.ts`
- `apps/teacher-app/src/stores/user.ts`
- `.tasks/reports/r08-3-exec-teacher-kb-workbench_report.md`

## 页面改造前后对照

### 改造前

知识库页主要还是旧“浏览知识文档”骨架：

- 仅有静态分类 tab
- 调用旧 `entries/detail/offline` 接口
- 没有待补问题运营入口
- 没有管理员待审核视角

### 改造后

统一复用同一页面：

- **教师视角**
  - Tab A：`高频待补`
  - Tab B：`我的知识`
- **管理员视角**
  - Tab A：`待审核`
  - Tab B：`知识库`

并实现：

- 高频待补卡片
- 当前页展开答复表单
- `scope` 选择
- 提交后 toast 区分 `已发布到知识库 / 已提交管理员审核`
- 管理员待审核卡片最小审核动作

## 核心实现

### 1. 新增前端数据类型

在 `src/types/api.ts` 中补齐：

- `KnowledgeScope`
- `UnansweredTopItem`
- `UnansweredTopResponse`
- `KnowledgeEntry`
- `CreateKnowledgeDraftPayload`
- `CreateKnowledgeDraftResponse`

### 2. `user` store 增补统一角色派生

在 `src/stores/user.ts` 中新增：

- `role`
- `isAdmin`
- `isTeacher`
- `preferredKnowledgeScope`

前端角色判断不再散落。

### 3. `knowledge.ts` API 封装最小闭环

已封装：

- `getUnansweredTop(limit)`
- `createKnowledgeDraft(payload)`
- `getKnowledgeEntries(params)`
- `getKnowledgeDetail(id)`
- `getPendingReviews(limit)`
- `approveKnowledge(id)`
- `rejectKnowledge(id, reject_reason)`

另外加了本地缓存降级：

- 当旧 `entries/detail/offline` 后端尚未实现时，详情页和我的知识列表仍可使用本地缓存兜底

### 4. 高频待补表单

每张卡片展示：

- `question_text`
- `hit_count`
- `latest_at`
- `sample_conv_ids`
- `去补充`

展开后可填写：

- `raw_answer`
- `scope`
- 提交按钮

### 5. 详情页兼容新状态

`detail.vue` 已兼容：

- `approved`
- `pending`
- `rejected`
- `offline`

并增加：

- `reject_reason` 横幅展示
- `representative_query` 作为信息头部来源

## 已知偏差 / 降级

### 偏差 1：旧知识详情与下线接口在当前网关未找到真实实现

教师端原先调用：

- `GET /api/v1/knowledge/entries/{id}`
- `POST /api/v1/knowledge/entries/{id}/offline`

但当前后端仓库未找到对应真实路由实现。本轮处理方式：

- 保留原调用
- 增加本地缓存降级

因此页面可以继续打开，但“完整线上详情 / 下线”仍依赖后续后端补齐或已有外部服务。

### 偏差 2：`type-check` 全量失败来自既有无关文件

当前 `npm run type-check` 失败点位于：

- `src/api/escalation.ts`
- `src/pages/login/index.vue`
- `src/pages/profile/index.vue`

本轮未新增 `knowledge/*` 范围内的错误，但无法宣称全量 `teacher-app type-check` 通过。

## 联调接口清单

- `GET /api/v1/knowledge/unanswered-top`
- `POST /api/v1/knowledge/drafts`
- `GET /api/v1/knowledge/reviews/pending`
- `POST /api/v1/knowledge/reviews/{id}/approve`
- `POST /api/v1/knowledge/reviews/{id}/reject`

前端同时兼容后端单数别名：

- `/api/v1/knowledge/review/*`

## 本地校验输出

### teacher-app type-check

```text
npm run type-check
```

结果：

- 未能全量通过
- 失败项为既有文件：`api/escalation.ts`、`pages/login/index.vue`、`pages/profile/index.vue`
- 本轮改动文件未从过滤输出中暴露新增错误

## L0-L3 自检结论

### L0

- 已完成
- 教师能看到高频待补问题
- 可选择 scope
- 可提交答复
- 管理员可进入待审核视图

### L1

- 部分完成
- 页面与详情页均可打开
- 但全量 `teacher-app type-check` 受既有历史错误阻塞

### L2

- 待运行入口挂载后做 165 联调
- 由于 `knowledge_router` 当前未在 `app/main.py` 挂载，尚无法直接走真实网关路径

### L3

- 已具备加载态、空态、提交态、失败态、待审核态
- UI 为最小闭环，不含复杂富文本或草稿自动保存

## 165 远端验证建议步骤

在知识路由挂载后：

1. 教师登录进入 `知识库`
2. 在 `高频待补` 中选择 1 条问题
3. 填写答复并选择 `班级发布` 或 `学院发布`
4. 观察 toast：
   - `已发布到知识库`
   - 或 `已提交管理员审核`
5. 切到 `我的知识` 验证新条目状态
6. 管理员登录进入同页，验证 `待审核` tab 可见

## 截图建议

当前未在本地生成截图，建议联调时补以下 4 张：

- 教师视角：高频待补列表
- 教师视角：展开答复表单
- 管理员视角：待审核卡片
- 详情页：驳回原因展示
