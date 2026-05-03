#!/bin/bash
# Check HK Dify dataset configuration
set -e

BASE="http://127.0.0.1:8088"
EMAIL="easten_zero@qq.com"
PASS_B64="WmhhWWVGYW4wNS4wNy4xNA=="

# Login
LOGIN_RESP=$(curl -s -X POST "$BASE/console/api/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS_B64\",\"language\":\"zh-Hans\",\"remember_me\":true}")

TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('access_token', d.get('access_token','')))" 2>/dev/null)

if [ -z "$TOKEN" ] || [ "$TOKEN" = "" ]; then
  echo "LOGIN FAILED: $LOGIN_RESP"
  exit 1
fi
echo "LOGIN OK, token=${TOKEN:0:20}..."

# List datasets
echo ""
echo "=== DATASETS ==="
curl -s "$BASE/console/api/datasets?page=1&limit=20" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for ds in data.get('data', []):
    print(f\"ID: {ds['id']}\")
    print(f\"  Name: {ds['name']}\")
    print(f\"  Doc Count: {ds.get('document_count', '?')}\")
    print(f\"  Embedding Model: {ds.get('embedding_model', '?')}\")
    print(f\"  Embedding Provider: {ds.get('embedding_model_provider', '?')}\")
    print(f\"  Retrieval Model: {json.dumps(ds.get('retrieval_model_dict', {}), indent=4)}\")
    print()
"

# Check the specific dataset used by gateway
TARGET_DS="c2363fef-405b-48ab-a0e2-9274a4186cef"
echo "=== TARGET DATASET ($TARGET_DS) ==="
curl -s "$BASE/console/api/datasets/$TARGET_DS" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "
import sys, json
ds = json.load(sys.stdin)
print(f\"Name: {ds.get('name', '?')}\")
print(f\"Doc Count: {ds.get('document_count', '?')}\")
print(f\"Word Count: {ds.get('word_count', '?')}\")
print(f\"Embedding Model: {ds.get('embedding_model', '?')}\")
print(f\"Embedding Provider: {ds.get('embedding_model_provider', '?')}\")
print(f\"Retrieval Model: {json.dumps(ds.get('retrieval_model_dict', {}), indent=2)}\")
print(f\"Indexing Tech: {ds.get('indexing_technique', '?')}\")
print(f\"Created: {ds.get('created_at', '?')}\")
print(f\"Updated: {ds.get('updated_at', '?')}\")
" 2>/dev/null || echo "Dataset not found or error"
