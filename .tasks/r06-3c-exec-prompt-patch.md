---
id: "r06-3c-exec-prompt-patch"
parent: "R06-3' + R06-4B + R06-1'"     # 三合一：补强 prompt + 注入上下文 + 降意图分类模型
type: "ui-ops"                          # TX 在 Dify Web 里操作，非 T3 代码执行
status: "pending"
tier: "TX"                              # 只能由管理员账号登录 Dify 来做
priority: "high"
risk: "medium"                          # 改的是生产 Chatflow，需谨慎

scope:
  - "Dify Chatflow → 意图分类节点（仅模型降级）"
  - "Dify Chatflow → 闲聊 LLM 节点（system prompt 追加边界）"
  - "Dify Chatflow → RAG 回答节点（system prompt 整段替换 + 温度 + max_tokens）"
  - "docs/design/dify-current-prompt.md"          # 变更完成后**回写**新状态
  - "docs/design/dify-current-config.md"          # 变更完成后**回写**新配置
  - "docs/design/dify-chatflow-design.md"         # 变更完成后同步更新 Top K / Dataset / prompt 链接

out_of_scope:
  - "services/**"                                 # 不改 gateway 代码
  - "apps/**"                                     # 不改前端
  - "Dify Dataset（知识库）"                       # 这是 R06-2 的范围
  - "Dify docker-compose 和容器"                   # 这是 R06-5 的范围
  - "Dify Chatflow 的其他节点（开始 / 问候回复 / 转人工回复 / 输出节点）"
  - "新建 Dify 应用或新建 Dataset"

context_files:
  - ".teb/antipatterns.md"
  - "docs/design/dify-prompt-review.md"           # R06-3b 审阅结论（依据）
  - "docs/design/dify-current-prompt.md"          # 变更前的基线
  - "docs/design/dify-current-config.md"
  - "docs/requirements/R06-P0-quick-wins.md"      # R06-3 / R06-3' / R06-4B / R06-1'
  - "docs/PROJECT-SECRETS.md"                     # §2.1 Dify 账号密码

done_criteria:
  L0: "Dify Chatflow 的 RAG 回答节点 system prompt 已替换为新版；温度 = 0.3；max_tokens = 1500"
  L1: "闲聊节点 system prompt 末尾已追加【边界】块"
  L2: "gateway 已 restart 后发一条测试问题（"能帮我点外卖吗？"），Dify 回复明确拒答并引导"
  L3: "docs/design/dify-current-prompt.md / dify-current-config.md 已回写新状态；R06 spec 标 R06-3' 与 R06-4B 为 ✅"

depends_on:
  - "r06-4a-exec-gateway-inputs"   # inputs 字段必须先就位，否则 {{#inputs.college_name#}} 取不到值
created_at: "2026-04-20"
---

> ⚠️ **Meta：T0 代劳起草** — 2026-04-20 TX 授权 T0 代 T1 起草本任务文件。
> 本任务是 R06-3b 审阅（分级 B）的落地动作；同时合并了 R06-4B 和 R06-1' 的部分动作以减少 UI 操作次数。
> T1 审阅后可直接采用、局部调整、或完全重写。
> 规范边界：[`.teb/antipatterns.md`](../.teb/antipatterns.md)。

# R06-3c Executor · Dify UI 三节点补强（TX 在 Web 控制台操作）

> 目标状态：
> 1. RAG 回答节点 system prompt 从"骨架版"升级为"边界+风格+上下文+引用规范"完整版
> 2. RAG 回答节点温度 `0.7 → 0.3`；`max_tokens` 未设 → `1500`
> 3. 闲聊节点追加【边界】块，引导回正事
> 4. 意图分类节点模型 `qwen-plus → qwen-turbo`（R06-1' 降本增效）
>
> **前置条件**：R06-4A 已 merge 部署（gateway inputs 已含 `college_name / campus / class_id`）

## 背景

本任务是 R06-3b 审阅的落地。审阅结论：**B. 局部补强**，具体缺口见 `docs/design/dify-prompt-review.md` § 2 / § 5。

三合一的理由：
- 改 RAG 节点 prompt 和改温度是同一节点，一次操作
- R06-4B（注入 `{{#inputs.xxx#}}`）必须写进同一个 prompt，没必要分两次
- 意图分类降 qwen-turbo 在同一次 Chatflow 编辑会话里顺手完成，避免再登录一次

## 必读上下文

1. `docs/design/dify-prompt-review.md`（本次变更的**依据**，含完整新 prompt 文本）
2. `docs/design/dify-current-prompt.md`（变更前基线，**操作时对照着改**）
3. `docs/PROJECT-SECRETS.md § 2.1`（Dify 登录账号）
4. `docs/requirements/R06-P0-quick-wins.md` § R06-3' / R06-4B

## 前置准备

### 1. 确认 R06-4A 已落地

```powershell
# 在本地 windows
cd C:\Users\Administrator\Documents\code\yixiaoguan-v2
git log --oneline -20 | Select-String "R06-4A|gateway-inputs"
```

若看不到 R06-4A 的 commit，**停止**，先让 T3 跑 r06-4a-exec-gateway-inputs 任务。

### 2. 登录 Dify

- URL: `http://192.168.100.165:3000`
- 账号密码：从 `docs/PROJECT-SECRETS.md § 2.1` 取

### 3. 打开医小管-主对话流

- 进入"应用"列表 → 找到 **医小管-主对话流**（app-zG64GT2sQ24WPT6Y9K0Kw042）
- 点击进入，选择"编排"（或"工作流"）标签

### 4. 全屏截图作为备份

- F12 打开开发者工具 → 把 Chatflow 整体截个图，存到本地 `~/Desktop/dify-chatflow-YYYYMMDD-before.png`
- 目的：万一改砸，有参照

---

## Step 1 · 意图分类节点（1 分钟，最低风险）

1. 画布上点击 **"意图分类"** 节点
2. 右侧面板 → "模型" 下拉
3. 从 `qwen-plus` 切换为 **`qwen-turbo`**
4. 温度保持 `0.1`，其他不变
5. ⚠️ **不点"保存"也不"发布"**，继续下一步

**验收**：右侧面板显示 `qwen-turbo`

---

## Step 2 · 闲聊 LLM 节点（3 分钟）

1. 画布上点击 **"闲聊LLM"** 节点
2. 右侧面板 → "SYSTEM" 输入框
3. **在现有 prompt 末尾追加**（不是替换）：

   ```text


   【边界】
   - 不讨论天气、外卖、娱乐、时政、医疗诊断
   - 学生若问非校园事务，礼貌回复 1 句 + 引导"校园里有什么可以帮你？"
   ```

4. 其他参数不变（温度 0.7）
5. ⚠️ 不点"保存"也不"发布"，继续下一步

**验收**：SYSTEM 输入框末尾有【边界】块，和原 prompt 用空行分隔

---

## Step 3 · RAG 回答节点（核心改动，10 分钟）

### 3.1 温度与参数

1. 画布上点击 **"RAG 回答"** 节点（kb_query 分支最后一个 LLM 节点）
2. 右侧面板 → "模型配置" 展开
3. **温度**：`0.7` → **`0.3`**
4. **max_tokens**：点开"高级"，设 **`1500`**
5. 其他（top_p / 模型名）不变

### 3.2 system prompt 整段替换

⚠️ **整段替换**，先 Ctrl+A 全选原内容再删除再粘贴。**不是追加**。

粘贴以下内容（来自 `docs/design/dify-prompt-review.md § 5.1`）：

```text
你是「医小管」，山东第一医科大学校园智能服务助手。

【身份与风格】
- 友善、专业、简洁；口语化但不失规范
- 可以在回答末尾适当鼓励或关心学生
- 不滥用 emoji；不装可爱；不卖萌
- 单次回复控制在 3-6 句话，长流程用编号步骤

【学生上下文】
当前学生：{{#inputs.college_name#}}{{#inputs.campus#}}{{#inputs.class_id#}}
若上述字段为空，按"通用"处理；若与问题域无关，忽略。

【能力边界 — 我能做什么】
- 校园规则、流程、办事指南、时间、地点、联系方式
- 学业、奖助学金、图书馆、医疗、心理、国际交流等校园事务
- 不知道的事情诚实说"我暂时没有这方面资料"

【能力边界 — 我不能做什么】
- 医疗诊断 / 用药建议 → 引导至校医院或正规医院
- 心理危机干预 → 引导至心理中心 + 提醒 24 小时热线
- 法律咨询 / 案件判决 → 告知不提供，建议咨询专业律师
- 天气、外卖、导航、娱乐闲聊 → 礼貌说"这不是我的专长"
- 时政评论、宗教讨论、他人隐私 → 拒绝

【回答规范】
- 严格基于下方"参考资料"回答，不编造未出现的信息
- 严禁编造 URL、电话、地址、时间、政策条款、部门名称
- 参考资料信息不完整时，如实说明已知部分，建议"可以咨询辅导员或相应部门"
- 引用关键流程 / 表单 / 条款时，在该句末尾注明来源，如"（见《学生手册 第三章》）"
- 若学生追问详细流程但资料中仅有概述，主动建议转人工

参考资料：
{{#context#}}
```

### 3.3 变量引用检查

⚠️ **关键**：Dify UI 里 `{{#inputs.xxx#}}` 不能直接当字符串输入，**必须用"变量选择器"插入**：

- 把光标定位到 `当前学生：` 后
- 点右侧面板下方的 **"+ 变量"** 按钮
- 选择 `inputs` → `college_name` → 插入
- 重复选择 `campus`、`class_id`
- `{{#context#}}` 在现有 prompt 里已引用过，沿用即可

**验收**：
- SYSTEM 输入框的"当前学生"那行，显示的是可点击的彩色变量块（不是纯文本 `{{#inputs.college_name#}}`）
- `{{#context#}}` 所在的"参考资料"行也是彩色变量块

---

## Step 4 · 保存为草稿（先别发布）

1. 画布右上角点 **"保存"**（或自动保存提示出现）
2. **不要点"发布"**

**验收**：右上角状态显示"已保存（草稿）"

---

## Step 5 · 草稿版本的预览测试（Dify 内置 Preview）

Dify Chatflow 有"预览/调试"面板，用它先测再发布。

1. 画布右上 → 点 **"预览"** 或 **"调试"**
2. 在聊天框输入 5 条测试消息，逐条确认回复：

   | 测试 | 输入 | 期望回复特征 |
   |------|------|-------------|
   | T1 | 你好 | 走 greeting 分支，固定文本，含"🏥 医小管" |
   | T2 | 能帮我点外卖吗？ | **明确拒答**，引导校园事务；不调 KB |
   | T3 | 我这两天头疼得厉害，吃什么药？ | **明确拒答医疗诊断**，引导校医院 |
   | T4 | 怎么申请弘毅奖学金？ | 走 kb_query 分支，从 KB 召回，回复中带 "（见...）"来源标注 |
   | T5 | 找老师 | 走 transfer 分支，固定文本 |

   ⚠️ 任何一条失败 → 停止，不发布。

3. **预览时 `{{#inputs.xxx#}}` 可能为空**（预览面板无 inputs 注入），这是正常的；prompt 里已写"若为空按'通用'处理"。

---

## Step 6 · 发布

⚠️ **只有 Step 5 全部通过**才能执行此步。

1. 画布右上角 → 点 **"发布"**
2. 选择"更新现有版本"（不是"发布为新版本"）
3. 确认

**验收**：
- 状态变为"已发布"
- Dify 控制台的"发布历史"里能看到本次发布时间
- gateway 侧**不需要重启**（Dify API 切流量瞬时生效）

---

## Step 7 · 线上回归（通过 gateway 发真实请求）

```bash
# 登录任一学生账号（如 staff_id=2024010001, pwd=2024010001）
# 拿 token 后，用 SSE 发请求

TOKEN=$(curl -s -X POST http://192.168.100.165:8100/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"staff_id":"2024010001","password":"2024010001"}' | jq -r .access_token)

# 创建会话
CONV=$(curl -s -X POST http://192.168.100.165:8100/api/conversations \
  -H "Authorization: Bearer $TOKEN" | jq -r .id)

# 发测试消息
curl -N -X POST http://192.168.100.165:8100/api/chat/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"conv_id\":$CONV,\"content\":\"能帮我点外卖吗？\"}"
```

期望：SSE 流返回的回复包含"这不是我的专长 / 校园事务"字样。

---

## Step 8 · 回写文档（5 分钟）

### 8.1 更新 `docs/design/dify-current-prompt.md`

- § 2.1（意图分类节点）：模型改为 `qwen-turbo`
- § 2.3（闲聊 LLM 节点）：system prompt 末尾追加【边界】块
- § 2.5（RAG 回答节点）：**整段替换** system prompt；温度 0.3；max_tokens 1500
- § 3（差异对照）：草稿 = 已发布（本次已统一）

### 8.2 更新 `docs/design/dify-current-config.md`

- § 1 节点参数表：三个节点的新值
- § 4（与 R06-1' 对比）：意图分类 ✅；RAG 温度 ✅

### 8.3 更新 `docs/design/dify-chatflow-design.md`

- 若里面有 prompt 片段，指向新版
- Top K / Dataset ID / rerank 配置若已过时也一并刷新（见 r06-3a 报告的"数据一致性异常"）

### 8.4 更新 R06 spec

- `docs/requirements/R06-P0-quick-wins.md` 的总览表：
  - R06-1' 标 ✅（意图分类已降级）
  - R06-3' 标 ✅（prompt 已补强）
  - R06-4B 标 ✅（学生上下文变量已注入）
- 变更日志追加 v5 行

---

## 回滚方案

### Level 1：还没发布，只是草稿改坏了
- Dify Chatflow 右上 → "发布历史" → 点旧版本的"恢复为草稿"
- 再"保存"即可

### Level 2：已发布但效果差
- "发布历史" → 旧版本的"发布"
- 回滚瞬时生效

### Level 3：已发布 + 历史记录被清
- 从 `docs/design/dify-current-prompt.md` 的 Git 历史回溯到本次变更前的版本
- 按同样步骤手动贴回旧 prompt + 温度 0.7

---

## 已知陷阱

| 陷阱 | 规避方法 |
|------|---------|
| `{{#inputs.xxx#}}` 粘贴成纯文本 | 必须用变量选择器插入，否则 Dify 不识别 |
| 预览时变量为空 | 预览面板无 inputs 注入；是正常现象，prompt 已处理 |
| qwen-turbo 偶发意图误分类 | R06-1' 建议值；若发现闲聊被分成 kb_query，改回 qwen-plus |
| 发布后 gateway 还在用旧 prompt | Dify 发布即生效，gateway 无需重启；若确实旧，检查 Dify API 缓存或 nginx |
| KB 检索节点的 Dataset ID | 本任务**不动** Dataset 配置；若 r06-2b 结论是切草稿 Dataset，走独立任务 |
| 一次性改太多 | 若不放心，可分两次发布：Step 3 单独一次；Step 1 + 2 合一次 |

---

## 不做的事（out_of_scope）

- 不改 gateway 代码
- 不改 Dataset（知识库内容）
- 不改 docker-compose
- 不动其他 Dify 应用
- 不改 Dify 账号密码
- 不在本任务里做 R06-5 瘦身

---

## 完成后

1. 回写完毕的 4 份文档 `git commit -m "docs: R06-3c prompt patch applied"`
2. 在 `.tasks/r06-3c-exec-prompt-patch.md` 末尾追加执行记录（时间、操作人、异常）
3. 通知 T1 / T0：R06-3'、R06-4B、R06-1' 同步闭环；batch-4 仅剩 r06-5b 和 r06-2b 的后续动作
