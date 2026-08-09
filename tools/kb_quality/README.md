# Dify 知识库隔离评测

这套工具只读取 PostgreSQL 与 Weaviate 快照，不调用 Dify Dataset/Chat API，也不写线上数据。

```bash
python3 tools/kb_quality/evaluate_snapshot.py \
  --postgres /tmp/dify-postgres.jsonl.gz \
  --weaviate /tmp/dify-weaviate.jsonl.gz \
  --output /tmp/kb-quality.json

python3 -m unittest tools.kb_quality.tests.test_weaviate_identity_policy
```

如需增加不依赖线上模型服务的语义对比，可在临时目录安装 `fastembed`，然后运行：

```bash
PYTHONPATH=/tmp/kb-eval-pydeps python3 tools/kb_quality/evaluate_semantic.py \
  --postgres /tmp/dify-postgres.jsonl.gz \
  --weaviate /tmp/dify-weaviate.jsonl.gz \
  --queries tools/kb_quality/golden_queries.jsonl \
  --dataset global-kb --dataset 医小管知识库 \
  --cache-dir /tmp/kb-model-cache
```

指标说明：

- `exact%`：活动 segment 的 `index_node_id` 能否精确找到同 `doc_id` 的 Weaviate 对象。
- `repr%`：即使发生重复文本覆盖，活动 segment 的正文是否仍被某个可搜索对象表示。
- `stale`：活动文档过滤后仍能搜到、但已经不对应当前 segment ID 的旧向量对象。
- `ideal@1`：假设所有活动 segment 均正确建索引时的本地 BM25 Top-1。
- `actual@1/@3`：按快照中实际可搜索的 Weaviate 对象计算的本地 BM25 命中率。

BM25 结果只用于版本间相同口径的离线对比，不等同于线上 `text-embedding-v4 + qwen3-rerank` 的端到端成绩。
