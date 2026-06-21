# ISSUE-006 学生/教师工单内测身份和通知边界问题

## 现象

学生端 pilot 匿名账号可以发起转人工并切换会话状态，但因为没有 `college_id`，教师通知可能不会发出。老师呼叫功能目前是通过发送“呼叫老师”等关键词触发，不是长按发送按钮。

## 证据

- pilot 匿名学生可创建会话、发送消息、触发转人工。
- 点击转人工调用 `/api/conversations/120/escalate` 返回 200，UI 切换到等待教师。
- 代码中 `_notify_college_teachers` 在学生没有 `college_id` 时会提前返回。
- 用户说明：老师呼叫功能目前通过手动发送“呼叫老师”或相关关键字自动弹出，长按是旧版本。

## 影响

- 内测如果使用匿名或未绑定学院学生，教师可能收不到通知。
- 工单状态变化和实际教师可见性可能不一致。
- 呼叫入口的产品预期需要重新确认，避免按旧长按逻辑修错方向。

## 涉及区域

- `services/gateway/app/routers/actions.py`
- `services/gateway/app/services/conversation_service.py`
- `apps/student-app/src/composables/useChatSession.ts`
- `apps/student-app/src/components/chat/ChatComposer.vue`
- `apps/teacher-app/src/pages/questions/index.vue`
- `apps/teacher-app/src/pages/questions/detail.vue`

## 建议修复方向

- 使用真实学号学生账号测试完整工单通知，而不是 pilot 匿名账号。
- 对无学院学生转人工给出明确提示或兜底通知管理员。
- 明确当前呼叫老师交互：关键词触发是否保留，是否恢复长按入口。
- 修完实时通信后再做双端工单全链路回归。

