# 设计稿 vs 当前实现 差距分析

> 生成日期：2026-04-27
> 范围：`docs/design/ui-references/` 中 stitch 设计稿对照 `apps/{teacher,student}-app/src/pages/` 的实际 Vue 文件

## 教师端 (apps/teacher-app)

| Stitch 设计稿 | 当前 Vue 文件 | 状态 | 备注 |
|---|---|---|---|
| `login_screen/code.html` | `apps/teacher-app/src/pages/login/index.vue` | ✅ exists | 登录页已实现 |
| `dashboard/code.html` | `apps/teacher-app/src/pages/dashboard/index.vue` | ✅ exists | 教师首页已实现 |
| `knowledge_base/code.html` | `apps/teacher-app/src/pages/knowledge/index.vue` | ✅ exists | 知识库列表已实现 |
| `knowledge_detail/code.html` | `apps/teacher-app/src/pages/knowledge/detail.vue` | ✅ exists | 知识详情已实现 |
| `question_list/code.html` | `apps/teacher-app/src/pages/questions/index.vue` | ✅ exists | 提问列表已实现 |
| `question_detail/code.html` | `apps/teacher-app/src/pages/questions/detail.vue` | ✅ exists | 提问详情已实现 |
| `profile_settings/code.html` | `apps/teacher-app/src/pages/profile/index.vue` | ✅ exists | 个人中心已实现 |

### 教师端总结
- 已有页面: 7
- 缺失页面: 0
- 设计与实现明显偏差的: 待具体视觉走查确认

## 学生端 (apps/student-app)

| Stitch 设计稿 | 当前 Vue 文件 | 状态 | 备注 |
|---|---|---|---|
| `login_page/code.html` | `apps/student-app/src/pages/login/index.vue` | ✅ exists | 登录页已实现 |
| `home_page/code.html` | `apps/student-app/src/pages/home/index.vue` | ✅ exists | 学生首页已实现 |
| `services_page/code.html` | — | ❌ missing | 服务大厅聚合页未实现 |
| `ai_chat_page/code.html` | `apps/student-app/src/pages/chat/index.vue` | ✅ exists | AI 问答主界面已实现 |
| `chat_history/code.html` | `apps/student-app/src/pages/chat/history.vue` | ✅ exists | 历史会话已实现 |
| `my_questions/code.html` | — | ❌ missing | 我的提问列表未实现 |
| `my_applications/code.html` | — | ❌ missing | 我的申请列表未实现 |
| `application_detail/code.html` | — | ❌ missing | 申请详情页未实现 |
| `classroom_booking_form/code.html` | — | ❌ missing | 空教室预约表单未实现 |
| `knowledge_detail/code.html` | — | ❌ missing | 学生侧知识库详情未实现 |
| `pdf_viewer/code.html` | — | ❌ missing | PDF 文档预览未实现 |
| `profile_page/code.html` | `apps/student-app/src/pages/profile/index.vue` | ✅ exists | 个人中心已实现 |

### 学生端总结
- 已有页面: 5
- 缺失页面: 7 (`services_page`, `my_questions`, `my_applications`, `application_detail`, `classroom_booking_form`, `knowledge_detail`, `pdf_viewer`)
- 设计与实现明显偏差的: 待具体视觉走查确认

## 总体观察

1. **教师端页面覆盖度较高**：7 个 stitch 设计页全部有对应 Vue 实现，核心功能链路完整。
2. **学生端缺失大量服务类页面**：`services_page`、`my_applications`、`application_detail`、`classroom_booking_form` 等办事/申请相关页面均未实现。
3. **学生端缺少知识库浏览能力**：`knowledge_detail` 在教师端已实现，但学生侧查看入口缺失。
4. **学生端缺少 PDF 预览**：`pdf_viewer` 未实现，可能影响文档类知识或申请材料的查看。
5. **两端均未发现独立的「我的提问」页**：学生端 `my_questions` 缺失，可能当前合并在其他模块中。

## 建议下一步

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | 实现 `services_page` | 学生端服务大厅是多个申请的统一入口，影响导航结构 |
| P0 | 实现 `my_applications` + `application_detail` | 办事申请的核心闭环 |
| P1 | 实现 `classroom_booking_form` | 高频服务场景，设计稿已完整 |
| P1 | 实现 `my_questions` | 学生查看自己提问历史的独立页面 |
| P1 | 实现 `knowledge_detail`（学生端） | 复用教师端逻辑，调整权限与展示字段 |
| P2 | 实现 `pdf_viewer` | 通用文档预览能力，可作为组件沉淀 |
| P2 | 视觉走查教师端 `dashboard` | 确认待处理任务模块与设计稿一致 |
