# 医小管全库精确化 v3

这是一个可回滚的候选包，不直接替换线上 Dify 数据集。它将现有 990 条学校与学院候选资料统一清洗，并把 v2 的“分层长回答”方法从奖学金扩展到全库。

## 目标

- 数量不等于可回答：保留全部资料，但区分规则证据、办事证据、结果参考和历史背景。
- 先回答再限定：已有证据先说清，仅对当年名额、截止日期和学院口径标注需核实。
- 每个结论可追溯：显示正式中文标题、发布单位、日期、时效状态和原文链接。
- 回答可继续：一次回答后给 2–3 个与上下文相关的追问，引导到学院、材料、流程或影响判断。

## 文件

- `topic-taxonomy.json`：全库主题与子主题。
- `curated-library-hours.json`：两校区图书馆 07:00—22:00 日常开放口径。
- `knowledge-card-schema.json`：统一知识卡结构。
- `answer-patterns.md`：政策、办事、比较、时间、个人影响等问题的回答契约。
- `interaction-benchmark-v2.md`：6 个高校官方智能问答案例与本轮交互取舍。
- `clean_catalog.py`：使用 Python 标准库从候选资料生成可治理目录。
- `catalog.jsonl`：全量清洗后目录。
- `topic-index.json`：面向检索与人工审核的主题索引。
- `quality-report.json`：条目数、时效、证据角色与复核队列。
- `evaluation.jsonl`：跨主题长回答验收问题。
- `validate_v3.py`：结构、覆盖和答案契约检查。
- `shadow-release.json`：影子发布、门禁和回滚方案。

## 生成与校验

```bash
python3 knowledge-pilot/comprehensive-v3/clean_catalog.py \
  --input /Users/gongzhen/Documents/医小管/yixiaoguan-v2/knowledge-pilot/campus/candidate-triage-20260809.json \
  --output-dir knowledge-pilot/comprehensive-v3
python3 knowledge-pilot/comprehensive-v3/validate_v3.py
```

## 上线边界

`catalog.jsonl` 是入库前治理层，不是把 990 条全部当成当前规则。仅 `answer_ready` 和人工复核通过的 `review_required` 条目可进入正式答案索引；`context_only` 与 `archive_only` 只能说明历史活动、项目存在或往年流程。
