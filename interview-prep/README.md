# 医小管 v2 面试准备目录

这个目录专门服务项目面试、答辩和简历追问。它不替代真实业务代码，而是把当前项目整理成一套可以清楚讲出来的工程化方案。

## 一句话定位

医小管 v2 是一个基于 Dify Chatflow 的校园 AI 助手系统，采用 FastAPI 单体 + UniApp 双端架构，支持知识库问答、教师实时介入、意图识别和个性化回答，知识库覆盖 960+ 条校园服务知识。

## 目录说明

| 文件 | 用途 |
|---|---|
| `00-project-understanding-and-roadmap.md` | 先读总纲：项目整体理解、技术栈地图、核心业务流程、面试准备路线图 |
| `01-project-positioning.md` | 项目定位、真实边界、技术选型理由、面试表达边界 |
| `02-technical-architecture.md` | 技术架构详解、数据库设计、AI引擎架构、实时通信架构 |
| `03-interview-playbook.md` | 高频面试问答和可直接背诵的回答 |
| `04-resume-optimization.md` | 简历优化建议、亮点提炼、模板示例 |
| `05-ai-integration-deep-dive.md` | AI集成深度解析、RAG技术、Dify Chatflow、知识库管理 |

## 推荐使用方式

1. 先读 `00-project-understanding-and-roadmap.md`，把业务、代码、技术栈和面试准备路线串起来。
2. 再读 `01-project-positioning.md`，明确什么是已实现、什么是设计优化。
3. 然后读 `02-technical-architecture.md`，把 FastAPI、Dify、PostgreSQL、Redis 的关系讲顺。
4. 用 `03-interview-playbook.md` 准备高频面试问答。
5. 用 `04-resume-optimization.md` 优化简历描述。
6. 用 `05-ai-integration-deep-dive.md` 准备 AI 技术深度追问。

## 核心数据亮点

| 指标 | 数值 | 说明 |
|------|------|------|
| API 路由模块 | 14 个 | 认证、会话、消息、公告、知识库、后台管理、数据统计等 |
| 知识库条目 | 960+ 条 | 覆盖 12 个分类体系 |
| 会话状态 | 5 种 | AI 服务、待教师接入、教师服务、已解决、已关闭 |
| Chatflow 分支 | 4 个 | 闲聊、知识查询、转人工、兜底处理 |
| 前端应用 | 2 个 | 学生端 + 教师端，支持微信小程序和 H5 |
| 测试模块 | 12 个 | pytest 覆盖核心业务分支 |

## 技术栈关键词

**后端**: FastAPI、SQLAlchemy、Alembic、PostgreSQL、Redis、WebSocket、SSE  
**AI**: Dify、RAG、意图识别、qwen-plus、multimodal-embedding  
**前端**: UniApp、Vue 3、Element Plus、微信小程序、H5  
**部署**: Docker Compose、容器化

## 面试口径原则

不要说“项目已经真实抗住万级并发”。更稳的说法是：

> 当前项目实现了校园 AI 助手的核心链路。我基于实际业务场景做了生产级架构设计，系统支持知识库问答、教师实时介入、意图识别和个性化回答。在真实生产环境，需要进一步优化并发处理、缓存策略和监控告警。

这个口径既不虚夸，也能体现你知道系统怎么从课程项目演进到真实系统。

## 面试准备清单

### 技术知识点

- [ ] FastAPI 异步编程和依赖注入
- [ ] SQLAlchemy ORM 和数据库迁移
- [ ] WebSocket 原理和 Centrifugo 架构
- [ ] RAG 检索原理和向量数据库
- [ ] SSE 流式响应实现
- [ ] Docker Compose 容器化部署
- [ ] UniApp 跨平台开发

### 项目细节

- [ ] 会话状态机的设计和实现
- [ ] Dify Chatflow 的配置和调用方式
- [ ] 知识库的结构和分类体系
- [ ] 教师介入的交互流程
- [ ] 数据分析和知识库优化机制

### 面试技巧

- [ ] 使用 STAR 法则描述项目经历
- [ ] 准备 2-3 个技术难点的解决方案
- [ ] 量化项目成果（如 14 个模块、960+ 条知识）
- [ ] 准备项目改进方向的回答

---

*创建日期：2026-06-02*
*基于医小管 v2 项目代码和文档整理*
