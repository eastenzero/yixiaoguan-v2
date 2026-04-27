# R05-4 Announcements Backend Delivery Report

## Files
- **Migration rev:** `9e879653d552` (head)
- **New files:**
  - `alembic/versions/9e879653d552_announcements.py` (60 lines)
  - `app/models/announcement.py` (39 lines)
  - `app/schemas/announcement.py` (39 lines)
  - `app/services/announcement_service.py` (196 lines)
  - `app/routers/announcements.py` (66 lines)
  - `tests/test_announcements.py` (258 lines)
- **Modified files:**
  - `app/models/__init__.py` (+1 line)
  - `app/main.py` (+2 lines)
  - `app/routers/chat.py` (+16 lines)

## Migration & Tests
- `alembic current`: `9e879653d552 (head)`
- `test_announcements.py`: **14/14 pass**
- Full suite: **76 passed, 0 failed**

## API Endpoints Shipped
| Method | Path | Auth | Desc |
|--------|------|------|------|
| POST | /api/v1/announcements | teacher/admin | 创建通知 |
| GET | /api/v1/announcements/mine | teacher/admin | 我发布的列表 |
| PATCH | /api/v1/announcements/:id | creator/admin | 更新通知 |
| DELETE | /api/v1/announcements/:id | creator/admin | 软删除 |

## Smoketest Evidence
- Teacher college announcement created: `id=1` ✓
- Teacher `all` attempt: `403` ✓
- Admin all-type: created `id=2` ✓
- Stu1 SSE first chat: announcement event delivered (`id=1`) ✓
- Stu1 SSE second chat: no announcement event (read tracking works) ✓
- Admin `all` announcement: stu1 receives it on next chat (`id=2`) ✓

## Commit
- hash: `TBD`
- 10 files
- **NOT pushed**

## Pending UI Work
- Teacher UI: 发布通知页面 + 我发的列表
- Student UI: 通知卡片组件 (chat 流中识别 `announcement` event)

## Known Limitations
- Single `target_value` v1 (no multi-target broadcast)
- No "重新置顶" / "强制再次推送" ability
