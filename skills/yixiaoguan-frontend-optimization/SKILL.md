---
name: yixiaoguan-frontend-optimization
description: Apply the YiXiaoGuan purple liquid-glass visual system and a reusable student-to-teacher frontend workflow when redesigning, aligning, or reviewing its web UI.
metadata:
  short-description: Reuse YiXiaoGuan's visual language in teacher UI
---

# 医小管前端优化

把学生端已经验证过的紫色玻璃质感、克制流光、自然点击反馈和移动端比例，安全地复用到教师端。目标是形成可维护的同一套体验，而不是复制学生端页面或改动后端知识库。

## 适用范围

- 优化医小管教师端的工作台、学生提问、问答详情、知识库和个人中心。
- 让教师端与学生端在色彩、层级、动效、图标和状态语义上协调一致。
- 复核现有前端的错位、断点、点击反馈、空状态、加载状态或证据来源展示。

## 工作契约

1. 先读取实际页面、共用 token、路由和 API，再决定改动点；不要凭截图重写整页。
2. 默认只改前端展示层。保留现有 API、WebSocket、知识库内容、状态值和权限边界；只有用户明确要求时才改后端。
3. 复用现有组件和图标：学生端优先使用 `AppIcon`，教师端优先使用 `components/icons/`，不要为单个图标新增依赖。
4. 不新增第三种紫色。先识别当前 token 与页面硬编码色值的差异，再在一个 token 层收敛；任何全局换色都必须检查对比度和历史页面。
5. “在线”只在有真实连接状态且能帮助判断时显示；不要把装饰性在线徽章放在问答或导航顶部。
6. 参考资料必须保留正式中文标题、发布单位、日期和可打开的官方链接；不要用内部 ID 作为用户可见标题。

## 执行路径

1. **建立基线**：检查 `apps/student-app/src/styles/`、`apps/student-app/src/pages/home/index.vue`、`apps/student-app/src/pages/chat/index.vue`，以及教师端 `apps/teacher-app/src/styles/`、`pages/dashboard/`、`pages/questions/`。记录现状截图、断点和可回滚提交。
2. **选择最小改动面**：先复用 token、容器、状态类和已有组件；只在现有结构无法表达时新增组件。将教师端改动拆成工作台、队列/详情、知识库三类，不要同时重排所有页面。
3. **实现视觉层**：按照 [design-system.md](references/design-system.md) 使用暖白底、统一紫色、半透明表面、柔和边缘和少量紫色折射阴影。玻璃效果是层级，不是每个卡片都加阴影。
4. **实现交互层**：默认状态安静；悬停/按下时用轻微下沉、缩放和一次性高光中断流光。持续流光只用于主入口或 CTA，并提供 `prefers-reduced-motion` 降级。
5. **复用到教师端**：按照 [teacher-porting.md](references/teacher-porting.md) 把学生端模式映射到教师工作流，优先保证“待处理问题 → 详情 → 回复/转人工 → 返回队列”的连续性。
6. **验收与发布**：至少运行类型检查、生产构建、`git diff --check`，并用实际 viewport 检查移动窄屏、桌面宽屏、长文本、空列表、加载和错误状态。部署前先复制线上静态目录和涉及的服务文件，写出可执行回滚命令。

## 给其他模型的交接

需要交给智谱或其他编码模型时，直接提供 [zhipu-handoff.md](references/zhipu-handoff.md)，并同时给出目标仓库、目标页面、当前分支和“只改前端/是否允许上线”的明确边界。不要只发送一句“参考苹果风格”。

## 完成标准

- 教师端使用同一套颜色和层级规则，但信息密度仍适合处理学生问题。
- 关键操作有清晰的按下反馈，流光不抢正文，不影响阅读和输入。
- 问答、来源、加载、错误和空状态都能在窄屏与桌面宽屏稳定显示。
- 现有接口和知识库未被隐式改写；每次发布都有提交号、备份路径和回滚命令。
