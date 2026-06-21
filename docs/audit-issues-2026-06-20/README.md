# 医小管内测问题清单（2026-06-20）

这个目录用于集中记录本轮教师端、学生端、知识库和实时通信审计中已经确认的问题。当前阶段只记录和排序问题，后续可以在新对话中按编号逐一修复。

## 修复顺序建议

1. `ISSUE-001` 实时通信链路不可用
2. `ISSUE-002` 知识问答质量判定过宽
3. `ISSUE-003` 高频待补队列被非知识问题污染
4. `ISSUE-004` 教师知识入库缺少 AI 润色预览和确认
5. `ISSUE-005` 教师端“我的知识”不展示真实知识库
6. `ISSUE-006` 学生/教师工单内测身份和通知边界问题
7. `ISSUE-007` 教师端知识 API fallback 容易掩盖真实错误
8. `ISSUE-008` 线上账号与管理入口不稳定

## 当前证据摘要

- 学生端 AI 聊天 HTTP/SSE 可用，能创建会话并返回流式答案。
- 教师端 `anjing` 可以登录，知识库页面可访问。
- H5 实时通信存在配置问题：`/ws?token=...` 被 Nginx 301，浏览器 WebSocket 不跟随跳转；Centrifugo subscribe proxy 也存在 secret/header 不匹配迹象。
- 线上业务库中 `unanswered_questions` 有 26 条，全部 unresolved，其中大量是寒暄、情绪表达、转人工、反馈投诉，而非知识库问题。
- 线上 `chat_analytics` 里低 RAG 分数但长回答会被判定为已回答，导致错误或弱来源答案不进入待补队列。
- 教师端“我的知识”对 `anjing` 返回空列表，但业务库 `kb_entries` 有 433 条，说明教师端看到的不是完整真实知识库。
- 教师知识入库后端仍有 AI 润色链路，但 UI 没有润色前后对比和确认步骤；班级/学院范围会直接发布。

## 相关审计材料

- 根目录 `findings.md`、`progress.md`、`task_plan.md` 记录了排查过程。
- `output/playwright/knowledge-live-anjing-20260620.png` 是教师端知识库截图。
- `output/playwright/student-kb-qa-samples.json` 是学生端样本问答导出。
- `output/playwright/teacher-knowledge-api-results.json` 是教师知识接口读取结果。

