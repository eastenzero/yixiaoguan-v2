---
id: "r06-3a-scout-dify-prompt"
parent: "R06-3'"
type: "feature"
status: "done"
tier: "T3"
priority: "high"
risk: "low"
foundation: true                    # R06-3b 审阅依赖此 Scout 的产出

scope:
  - "docs/design/dify-current-prompt.md"
  - "docs/design/dify-current-config.md"   # 如果顺带抓了节点配置也一起记

out_of_scope:
  - "services/**"
  - "apps/**"
  - "任何对 Dify 的写操作"          # 严格只读 UI
  - "修改 Dify Chatflow 节点"
  - "修改 Dify Dataset"

context_files:
  - ".teb/antipatterns.md"
  - "docs/requirements/R06-P0-quick-wins.md"     # 第 R06-3 和 R06-3' 章节
  - "docs/PROJECT-SECRETS.md"                     # §2.1 Dify 账号密码

done_criteria:
  L0: "docs/design/dify-current-prompt.md 存在且非空"
  L1: "文件中包含至少一个完整的 system prompt（不少于 50 字）"
  L2: "文件中列出：节点名、模型名、温度、max_tokens、system prompt 全文"
  L3: "T0 审阅后可据此开始 R06-3b 的差异分析"

depends_on: []
created_at: "2026-04-17"
---

> ⚠️ **Meta：T0 代劳起草** — 2026-04-17 TX 授权，T0 代 T1 起草本任务文件。
> T1 审阅后可直接采用、局部调整、或完全重写。若 T1 重写，删除本 meta 块即可。
> 规范边界：[`.teb/antipatterns.md`](../.teb/antipatterns.md)。

# R06-3a Scout · 抓取 Dify Chatflow 主 LLM 节点的 system prompt 现状

> 目标状态：V2 仓中有一份**完整准确**的 Dify Chatflow 主回复 LLM 节点 system prompt 文本（含节点元数据）。
> **严格只读**：不修改 Dify 任何配置。

## 背景

TX 告知"之前 AI 已经在 Dify 写过人设 prompt"，但 V2 仓内无文档化记录。
R06-3' 要求先审阅现状再决定是否补强，因此必须先抓取。

使用 **Kimi CLI 的浏览器能力**登录 Dify Web 控制台完成此任务。

## 必读上下文

1. `docs/requirements/R06-P0-quick-wins.md` § R06-3 和 R06-3'
2. `docs/PROJECT-SECRETS.md` § 2.1（Dify 账号密码）
3. `docs/PROJECT-CONTEXT.md` § 3.1（165 服务器信息）

## 前置准备

- Dify Web URL：`http://192.168.100.165:3000`
- 账号：从 `PROJECT-SECRETS.md §2.1` 取（`easten_zero@qq.com`）
- 密码：从 `PROJECT-SECRETS.md §2.1` 取

## Scout 执行步骤

### Step 1：登录 Dify

1. 打开浏览器访问 `http://192.168.100.165:3000`
2. 用邮箱 + 密码登录
3. 若登录失败（密码错误/账号不存在），立即停止并上报 TX

### Step 2：定位 Chatflow

1. 进入"应用"列表
2. 找到**当前 V2 gateway 在使用的 app**（线索：
   - gateway `.env` 里的 `DIFY_API_KEY = app-zG64GT2sQ24WPT6Y9K0Kw042`
   - 可在 Dify 应用设置 → API Keys 里反查
3. 打开该应用的 Chatflow 编辑器

### Step 3：遍历每个 LLM 节点

Chatflow 中所有 LLM 节点（非 Question Classifier）都要抓，包括但不限于：

- 意图分类后的 `kb_query` 分支最终回复节点
- `chitchat` 分支的闲聊节点
- `transfer` 分支的兜底节点（如有 LLM）
- 其他辅助节点（摘要、重写、条件分支里的 LLM 等）

**对每个 LLM 节点**，记录：

| 字段 | 来源 |
|------|------|
| 节点名 | 画布上的 label |
| 所在分支 | 从意图分类节点到本节点的路径 |
| 模型名 | 节点右侧配置面板 → 模型下拉 |
| 温度 | 同上 |
| max_tokens | 同上 |
| top_p | 同上（如有） |
| system prompt 全文 | 节点 "提示词" / "系统消息" 输入框 |
| user message 模板 | 节点 "用户消息" / "查询" 输入框 |
| 使用的变量 | 如 `{{#context#}}` `{{#sys.query#}}` 等 |

**重要**：如果 prompt 输入框默认折叠或显示省略号，**点开** / **全选复制**，确保抓的是全文。

### Step 4：顺带抓整体 Chatflow 结构

画一张简易的流程图（文字描述即可）：

```
[用户输入]
  ↓
[意图分类] (Question Classifier / LLM)
  ↓
├─ kb_query 分支 → [RAG 检索] → [最终回复 LLM] → 输出
├─ chitchat 分支 → [闲聊 LLM] → 输出
├─ transfer 分支 → [转人工提示] → 输出
└─ 其他兜底 → ...
```

### Step 5：写产出文档

创建 `docs/design/dify-current-prompt.md`，按以下结构写：

```markdown
# Dify Chatflow 现状（2026-04-17 抓取）

> 抓取者：T3 Kimi Scout
> 抓取方式：浏览器登录 Dify Web 控制台
> Chatflow 应用：XXX（app-zG64GT2sQ24WPT6Y9K0Kw042）

## 1. Chatflow 总览

（流程图 + 分支说明）

## 2. 节点详情

### 2.1 意图分类节点
- 节点名：...
- 类型：Question Classifier / LLM
- 模型（若为 LLM）：...
- 分类规则：...

### 2.2 kb_query 最终回复节点
- 节点名：...
- 模型：...
- 温度：...
- max_tokens：...
- top_p：...

**system prompt**：
```
（全文，原样粘贴，保留换行和格式）
```

**user message 模板**：
```
（全文）
```

**使用的变量**：{{#context#}}, {{#sys.query#}}, ...

### 2.3 chitchat 闲聊节点
...（同上结构）

### 2.4 其他节点
...

## 3. 观察与备注

- 发现的异常：...（如 prompt 似乎截断、有废弃代码块等）
- 可能风险：...
```

**顺带**创建 `docs/design/dify-current-config.md`（用于 R06-1'），只含模型 + 参数的简表，不含 prompt 全文。格式：

```markdown
# Dify LLM 节点配置一览（2026-04-17）

| 节点 | 模型 | 温度 | max_tokens | top_p |
|------|-----|-----|-----------|-------|
| ... | ... | ... | ... | ... |
```

### Step 6：不修改任何内容

⚠️ **严格只读模式**：
- 不要在 Dify 里点"保存"按钮
- 不要删除、禁用、重命名任何节点
- 不要修改模型或 prompt
- 不要点"发布"
- 如果不小心改动了什么，**立即撤销**并在报告末尾说明

## 已知陷阱

- Dify 登录可能有二次验证或验证码，遇到时暂停并请 TX 协助
- Chatflow 编辑器可能需要等节点加载完全才能点开 prompt
- 长 prompt 在输入框中会截断显示，必须**点进去看全文或复制全文**
- 不同版本 Dify 的 UI 略有差异，以实际为准
- Dify 有 "草稿" 和 "已发布" 两种状态，抓取时确认是哪一个（如果不一致，两个都抓）

## 不做的事（out_of_scope）

- 不修改 Dify 任何配置
- 不触碰 Dify Dataset（知识库）
- 不调 Dify API
- 不登录非 Dify 的系统
- 不修改 V2 仓的代码文件（只写 `docs/design/` 下的报告）

## 完成后

1. 产出 `docs/design/dify-current-prompt.md` 和 `docs/design/dify-current-config.md`
2. 向 T1 回报这两个文件的路径
3. T0 会对照 R06-3 原设计做差异分析，产出 R06-3b 审阅报告
