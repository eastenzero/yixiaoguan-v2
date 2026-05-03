#!/bin/bash
# On HK 64. Dump v1 vectors from weaviate into a JSON for cosine matrix later.
set -e

DATASET=c2363fef-405b-48ab-a0e2-9274a4186cef
CLASS="Vector_index_${DATASET//-/_}_Node"
OUT=/opt/yxg-v2/scripts-kb/v1-vectors.json

echo "=== weaviate class: $CLASS ==="
# Check class exists
docker exec docker-api-1 sh -c "curl -sS http://weaviate:8080/v1/schema/$CLASS" | head -c 200
echo

echo
echo "=== object count ==="
docker exec docker-api-1 sh -c "curl -sS 'http://weaviate:8080/v1/graphql' -H 'Content-Type: application/json' -d '{\"query\":\"{ Aggregate { $CLASS { meta { count } } } }\"}'" | head -c 400
echo

echo
echo "=== fetch all objects with vectors (paginated) ==="
mkdir -p /opt/yxg-v2/scripts-kb
docker exec docker-api-1 sh -c '
  python3 - <<PY
import json, urllib.request, urllib.parse
CLASS = "'"$CLASS"'"
all_objs = []
cursor = None
while True:
    params = {"class": CLASS, "limit": "100", "include": "vector"}
    if cursor:
        params["after"] = cursor
    url = f"http://weaviate:8080/v1/objects?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as r:
        body = json.loads(r.read())
    objs = body.get("objects", [])
    if not objs:
        break
    all_objs.extend(objs)
    cursor = objs[-1]["id"]
    if len(objs) < 100:
        break
print(json.dumps({"count": len(all_objs), "objects": all_objs}, ensure_ascii=False))
PY
' > "$OUT"

echo "=== dumped ==="
ls -la "$OUT"
echo "size: $(stat -c %s $OUT) bytes"
python3 -c "import json; d=json.load(open('$OUT')); print('objects:', d['count']); o=d['objects'][0] if d['objects'] else None; print('first object keys:', list(o.keys()) if o else None); print('first vector len:', len(o.get('vector',[])) if o else 0); print('first properties keys:', list(o.get('properties',{}).keys()) if o else None)"
