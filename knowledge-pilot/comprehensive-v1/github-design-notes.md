# GitHub RAG 案例取舍

全面版不引入新的 RAG 框架，继续使用现有 Dify 链路，只吸收已被多个项目验证的简单做法。

## 采纳

- [Weaviate Verba](https://github.com/weaviate/Verba)：多文档交叉参考、混合检索、元数据过滤和来源预览。用于设计“政策层级 + 学院 + 学年”的检索元数据。
- [RAGFlow](https://github.com/infiniflow/ragflow)：回答引用与原文切片对应。用于要求金额、日期、比例等关键事实可回到真实命中文档。
- [Quivr](https://github.com/QuivrHQ/quivr)：查询改写、检索、重排、生成的短链路。用于把“奖学金怎么评”改写成对应学生类型、学院、奖项和学年的检索问题。
- [LlamaIndex](https://github.com/run-llama/llama_index)：多来源连接与可组合检索。用于统一看待政府、学校主站、学院站和经核验的官方公众号材料。
- [rag-web-ui](https://github.com/rag-web-ui/rag-web-ui)：使用文档来源、位置和哈希作为切片元数据，前端将引用标记映射到参考详情。医小管只在内部保留 ID，用户端显示正式中文标题和原文链接。

## 不采纳

- 暂不新增知识图谱、新向量库或多代理框架：当前问题主要是资料分层、元数据和答案契约，新基础设施不会自动解决它。
- 不将搜索引擎摘要当作证据：搜索结果只用来找原文。
- 不将公众号转载当作学院正式细则：必须核验账号主体、原始链接、标题和发布日期。
