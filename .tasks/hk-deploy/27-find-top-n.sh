#!/bin/bash
# Look at dify rerank logic + knowledge_retrieval node config schema
docker exec docker-api-1 sh -c 'grep -rn "top_n\|reranking_top_n\|top_k.*rerank" /app/api/core/ 2>/dev/null | head -20'
echo "---"
docker exec docker-api-1 sh -c 'grep -rn "reranking_enable" /app/api/core/workflow/nodes/knowledge_retrieval/ 2>/dev/null | head'
echo "---"
docker exec docker-api-1 sh -c 'grep -rn -B2 -A8 "MultipleRetrievalConfig\|multiple_retrieval_config" /app/api/core/workflow/nodes/knowledge_retrieval/ 2>/dev/null | head -60'
echo "---"
docker exec docker-api-1 sh -c 'find /app/api/core/workflow/nodes/knowledge_retrieval -type f -name "*.py"'
