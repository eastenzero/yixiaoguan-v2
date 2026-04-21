# KB 增强需求

> 来源：2026-04-14 与 TX 讨论
> 状态：**已确认方案，待排期实现**
> 关联：KB-SPEC.md、Dify Chatflow

---

## 需求 1：Top 10 高频操作图文教程

### 背景

像"怎么交电费"这类高频问题，纯文字步骤表述力不足。学生手册 PDF 中有截图示范，
但 Dify KB 的纯文本回复无法内嵌图片。需要一种方式让用户看到可视化的操作指引。

### 确认方案：KB 文字 + 前端图文卡片

**不在 Dify 加新分支**（"交电费"和普通 kb_query 无法可靠区分意图），
改为前端渲染增强。

```
用户："怎么交电费"
  → Dify 意图分类 → kb_query（不变）
  → RAG 检索 → 命中 KB 段落（含精确文字步骤 + 特殊标记）
  → AI 回复文本中包含 [tutorial:electricity-payment]
  → 前端检测到 [tutorial:xxx] 标记
  → 文字下方自动渲染图文教程卡片（图片存前端或 CDN）
```

### 改动范围

| 层 | 改动 | 工作量 |
|----|------|--------|
| KB 内容 | 高频操作段落末尾加 `[tutorial:xxx]` 标记 | 小 |
| 前端学生端 | 识别标记，渲染图文卡片组件 | 中 |
| Dify | 不动 | — |
| Gateway | 不动 | — |

### KB 文字描述标准

涉及 APP 操作的知识点，文字必须做到"导航级精确"：

- ❌ 模糊："在完美校园APP中进行电费充值"
- ✅ 精确："打开完美校园APP → 底部第三个Tab'校园卡' → 右上角'电费充值' → 选择校区/楼栋/房间 → 输入金额 → 支付"

每一步精确到**按钮名称和位置**。

### 初步 Top 10 清单（待确认）

1. 电费缴纳（完美校园APP）
2. 校园卡充值/绑定
3. 成绩查询（信息门户）
4. 选课操作
5. 图书馆借还书/座位预约
6. 校园网连接/VPN 设置
7. 宿舍报修
8. 请假申请
9. 通勤车时刻查询
10. 证件自助打印

---

## 需求 2：高频无答案问题统计

> **⚠️ 状态变更**（2026-04-21）：本需求的**数据层 + 统计层**（`chat_analytics` 表 / Gateway 落库 / Top N 看板）已被 `R08-教师-KB-运营闭环.md` 完整承接，并在 R08 基础上扩展为"教师答复 + AI 润色 + 分作用域发布"的完整运营闭环。
>
> **后续以 R08 为准**；本条目保留原始规划作历史参考。

### 背景

学生提问后 RAG 检索不到或置信度低，说明 KB 有盲区。需要自动发现这些盲区，
作为 KB 持续完善的数据驱动依据。

### 确认方案：Gateway 层记录 + 后台统计

**不在 Dify 加分支**，纯后端分析功能。

```
Gateway 层：
  每次 Dify 返回 message_end 事件 → 提取 metadata（检索结果、分数）
  → 写入 PG chat_analytics 表

定期统计：
  → 置信度低 / 未命中的 query 按频次排序
  → 生成"Top 未覆盖问题"报告
  → 管理后台展示，人工审核后补充 KB
```

### 改动范围

| 层 | 改动 | 工作量 |
|----|------|--------|
| Gateway | 解析 message_end metadata，写入分析表 | 中 |
| 数据库 | 新建 `chat_analytics` 表 | 小 |
| 前端管理端 | 展示"未覆盖问题 Top N"看板 | 中 |
| Dify | 不动 | — |

### 数据表初步设计

```sql
chat_analytics (
  id SERIAL PRIMARY KEY,
  conversation_id VARCHAR(128),
  user_query TEXT NOT NULL,
  rag_score FLOAT,            -- RAG 最高匹配分数，null=未命中
  kb_doc_matched VARCHAR(255), -- 命中的 KB 文档名
  is_answered BOOLEAN,         -- AI 是否给出了有效回答
  created_at TIMESTAMP DEFAULT NOW()
)
```

---

## 需求 3：学院/班级个性化知识

### 背景

不同学院的学生可能需要不同的回答（如"实验室在哪"），需要 AI 优先返回
与该学生所属学院相关的信息。

### 确认方案：Dify 输入变量 + KB 标签 + Prompt 引导

**不加 Dify 分支，不建多个 dataset**。

```
Gateway 调 Dify 时：
  inputs: {
    college_name: "临床与基础医学院",
    campus: "济南校区",
    class_id: "2024-临床1班"
  }

Dify RAG 检索后，LLM prompt 中加：
  "该学生来自{{college_name}}（{{campus}}），请优先使用与其学院相关的信息回答。"
```

### 改动范围

| 层 | 改动 | 工作量 |
|----|------|--------|
| Gateway | 调 Dify 时传入 college_name / campus / class_id | 小 |
| Dify Chatflow | 知识检索输出节点 prompt 加用户上下文 | 小 |
| KB 内容 | 段落标注学院/校区信息（已在 KB-SPEC 中定义） | — |
| 前端 | 不动 | — |

---

## 需求 4：教师定制通知/消息

### 背景

老师可能需要向特定班级/学院推送定制消息（如"明天的课改到3楼"），
这类消息时效性强、精确定向，不适合放 KB。

### 确认方案：Gateway 拦截层 + PG 通知表

**不在 Dify 做**，在 Gateway 进 Dify 之前拦截。

```
用户发消息
  → Gateway 先查 PG：有没有针对该用户（学院/班级）的活跃通知？
     → 有：优先返回通知内容 + "你还可以继续提问哦"
     → 无：继续走 Dify Chatflow（不变）
```

### 改动范围

| 层 | 改动 | 工作量 |
|----|------|--------|
| 数据库 | 新建 `announcements` 表 | 小 |
| Gateway | chat 路由增加通知拦截逻辑 | 中 |
| 前端教师端 | 通知发布页面（选目标人群、写内容、设过期时间） | 中 |
| Dify | 不动 | — |

### 数据表初步设计

```sql
announcements (
  id SERIAL PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  target_type VARCHAR(32) NOT NULL,  -- 'all' / 'college' / 'class'
  target_value VARCHAR(128),          -- college_id 或 class_id
  created_by INTEGER REFERENCES users(id),
  expire_at TIMESTAMP NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
)
```

---

## 优先级排序

| 需求 | 优先级 | 依赖 | 阶段 |
|------|--------|------|------|
| Top 10 图文教程 | P1 | KB 生成完成后 | 与 KB 入库同步 |
| 学院个性化 | P1 | Dify prompt 微调 | 随时可做 |
| 高频无答案统计 | P2 | Gateway 改造 | KB 入库后 |
| 教师定制通知 | P2 | 教师端开发 | 与教师端迭代同步 |

---

*创建日期：2026-04-14*
*来源：与 TX 对话讨论确认*
