# R10 — AI 回答后关联问题推荐

> Status: **In Progress**
> Priority: P1
> Est: 0.5 day

## 用户故事

学生提问后，AI 回答下方自动展示 3 条关联问题气泡，点击即可直接提问，降低输入成本、引导深入了解。

## 交互流程

```
学生: "奖学金怎么申请？"
AI:   (正常回答)
      ┌────────────────────────────────────────┐
      │ 💡 你可能还想问：                        │
      │  [奖学金有哪些类型？]                     │
      │  [申请截止时间是什么时候？]                │
      │  [需要准备什么材料？]                     │
      └────────────────────────────────────────┘
学生点击 → 自动填入输入框并发送
```

## 技术方案

### 后端（Gateway）

1. **生成时机**：`_stream_ai_response` 中 AI 消息保存完成后
2. **生成方式**：异步调用 qwen-turbo，prompt 如下：
   ```
   用户问："{query}"
   AI 答（摘要）："{answer[:300]}"
   请基于以上对话，生成3个用户可能接着问的简短问题。
   仅输出 JSON 数组，如 ["问题1","问题2","问题3"]，不要其他内容。
   ```
3. **SSE 事件**：在 `message_end` 之后、`done` 之前，插入：
   ```
   event: suggestions
   data: {"questions": ["问题1", "问题2", "问题3"]}
   ```
4. **容错**：异步生成，超时 5s 或失败则跳过，不影响主回答流

### 前端（student-app）

1. **sse.ts**：新增 `onSuggestions` 回调，解析 `suggestions` 事件
2. **chat/index.vue**：
   - 新增 `suggestedQuestions` ref，存储当前推荐问题列表
   - AI 消息下方渲染可点击气泡
   - 点击气泡 → `inputMessage = question` → 调用 `sendMessage()`
   - 用户发送新消息时清空上一轮推荐
3. **样式**：圆角胶囊按钮，主题色描边，横向滚动或折行

### 触发条件

- 仅 `ai_serving` 状态下触发（教师对话模式不需要）
- 仅当 AI 成功回答时生成（error 时跳过）
- 每轮对话只展示最新一组推荐

### 不做

- 不持久化推荐问题到 DB
- 不做推荐问题的点击率统计（后续可加）
- 教师端不涉及

## 文件变更清单

| 文件 | 变更 |
|------|------|
| `services/gateway/app/routers/chat.py` | `_stream_ai_response` 末尾加异步推荐生成 |
| `services/gateway/app/services/dify_client.py` | 新增 `generate_suggestions()` 方法 |
| `apps/student-app/src/utils/sse.ts` | `SSECallbacks` 加 `onSuggestions` |
| `apps/student-app/src/pages/chat/index.vue` | 渲染推荐气泡 + 点击交互 |
| `apps/student-app/src/types/chat.ts` | Message type 加 `suggestions` 可选字段 |
