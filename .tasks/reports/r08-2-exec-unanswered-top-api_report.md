# R08-2 Executor Report · Top N 高频待补问题 API

## 改动文件

- `services/gateway/app/routers/knowledge.py`
- `services/gateway/app/schemas/knowledge.py`
- `services/gateway/app/services/knowledge_service.py`
- `services/gateway/tests/test_knowledge_unanswered_top.py`
- `.tasks/reports/r08-2-exec-unanswered-top-api_report.md`

## 核心实现

### 1. 新增 Top N API 契约

已实现只读接口：

- `GET /api/v1/knowledge/unanswered-top?limit=20`

返回结构：

- `items`
  - `id`
  - `question_text`
  - `hit_count`
  - `latest_at`
  - `college_id`
  - `class_id`
  - `sample_conv_ids`
- `total`

### 2. 权限边界

- **教师**
  - 只能看到：
    - `college_id == current_user.college_id`
    - 或 `college_id is null`
- **管理员**
  - 可看全局
- **学生**
  - `403`

### 3. 排序与过滤

服务层固定：

- `is_resolved = false`
- `ORDER BY hit_count DESC, updated_at DESC, id DESC`
- `limit` 范围由路由层限制在 `[1, 100]`

### 4. 数据来源

本接口**只消费 `UnansweredQuestion`**，没有扫描 `chat_analytics` 做实时聚类。与任务卡不变式一致。

## 与父文档 / 运行现状的偏差

### 偏差 1：本轮返回 `latest_at = updated_at`

任务卡要求返回 `latest_at`，但现有 `UnansweredQuestion` 模型里没有单独的 `last_seen_at` 字段。当前实现使用：

- `latest_at = updated_at`

理由：

- 不改 `knowledge.py` 结构可以保持 `R08-2` scope 边界干净
- 结合 `R08-1` 的 unanswered upsert，`updated_at` 已能反映最近一次命中时间

这条在 `R08-4` 如需扩模型时可再显式补 `last_seen_at`。

### 偏差 2：路由已实现，但运行入口未在本任务内挂载

当前仓库 `main.py` 尚未 include `knowledge_router`，且 `main.py` 不在 `R08-2` scope 中。为遵守任务卡边界，本任务只实现了：

- router
- schema
- service
- tests

并将“挂载入口”记录为后续总报告中的集成交付偏差项。

## 本地校验输出

### pytest

```text
PS C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway> pytest tests/test_knowledge_unanswered_top.py -q
.....                                                                                                        [100%]
5 passed in 0.57s
```

### ruff

```text
All checks passed!
```

### mypy

```text
Success: no issues found in 4 source files
```

## L0-L3 自检结论

### L0

- 已完成
- 提供了教师/管理员可访问的 Top N 高频待补问题 API
- 教师只能看到本学院 + `college_id is null` 的记录
- 管理员可看全局

### L1

- 已完成
- 覆盖：
  - 教师视角
  - 管理员视角
  - 已解决过滤
  - `limit` 生效
  - 学生越权 `403`
- `pytest / ruff / mypy` 均通过

### L2

- 本地未做远端验证
- 待 R08 全量后统一到 165 做 curl 联调

### L3

- 需要依赖后续 `R08-4 / R08-5` 完成“直发成功 / 审核通过后从待补列表消失”的真实闭环验证

## 与 R08-3 的联调注意事项

前端拉取该接口时可直接消费：

- `question_text`
- `hit_count`
- `latest_at`
- `sample_conv_ids`

无需前端自行过滤 `is_resolved`；后端已返回干净列表。

## 165 远端验证建议步骤

待知识路由挂载后执行：

```bash
curl -s "http://192.168.100.165:8100/api/v1/knowledge/unanswered-top?limit=10" \
  -H "Authorization: Bearer TEACHER_TOKEN"
```

期望：

- 稳定 JSON
- 只返回本学院 + `college_id=null` 的待补问题
- 包含 `id / question_text / hit_count / latest_at / sample_conv_ids`

## 新发现的错误模式

- **现象**：任务卡 scope 只覆盖业务层文件，但真实可用还依赖运行入口挂载；若直接越 scope 改 `main.py`，会破坏边界纪律。
- **正确做法**：先在 scope 内把能力与测试实现完整，再把“运行入口未挂载”记录为显式偏差，交由后续允许修改入口文件的批次统一集成。
