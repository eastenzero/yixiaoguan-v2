# ISSUE-004 教师知识入库缺少 AI 润色预览和确认

## 现象

后端仍会对老师输入的答案做 AI 润色，但教师端 UI 只提供一个答案输入框。老师提交后无法看到 AI 润色结果，也无法确认 AI 是否改错。

## 证据

- `create_knowledge_draft()` 调用 `polish_knowledge_content()`。
- `polish_knowledge_content()` 调用 `dify_client.polish_text()`。
- class/college scope 会在后端润色后直接发布到 Dify。
- 教师端 `apps/teacher-app/src/pages/knowledge/index.vue` 只有 textarea、scope 选择和提交按钮，没有润色预览/确认。

## 影响

- AI 润色如果改错，老师无感知。
- 入库内容不可控，尤其是学院/班级范围会直接发布。
- 原本“AI 帮老师润色新增条目”的设计没有形成完整产品闭环。

## 涉及区域

- `apps/teacher-app/src/pages/knowledge/index.vue`
- `apps/teacher-app/src/api/knowledge.ts`
- `services/gateway/app/routers/knowledge.py`
- `services/gateway/app/services/knowledge_service.py`
- `services/gateway/app/services/dify_client.py`

## 建议修复方向

- 将入库流程拆成两步：生成润色草稿、老师确认发布。
- 前端展示原始答案、AI 润色版、适用范围、将要发布的数据集。
- 提供“重新润色”“使用原文”“编辑后发布”。
- 对 class/college 直接发布增加确认页或二次确认。

