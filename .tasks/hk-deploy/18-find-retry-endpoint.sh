#!/bin/bash
# Inside HK 64. Find Dify retry endpoint for failed indexing.
docker exec docker-api-1 sh -c "grep -n -A 2 'retry' /app/api/controllers/console/datasets/datasets_document.py" | head -40
