# R11 — 管理员用户管理（内测版）

> Status: In Progress | Priority: P0 | Est: 1 day

## 权限

所有接口仅 `role=admin` 可访问，其他角色返回 403。

## API

### 1. GET /api/admin/users — 用户列表

**Query 参数**：
| 参数 | 类型 | 说明 |
|---|---|---|
| page | int | 页码，默认 1 |
| size | int | 每页条数，默认 20 |
| role | string? | 筛选角色：student / teacher / admin |
| college_id | int? | 筛选学院 |
| class_id | int? | 筛选班级 |
| keyword | string? | 模糊搜索 staff_id 或 name |

**返回**：
```json
{
  "items": [
    {
      "id": 1,
      "staff_id": "4125150001",
      "name": "张三",
      "role": "student",
      "college_id": 17,
      "college_name": "医药管理学院",
      "class_id": 5,
      "class_name": "公共事业管理2025-1班",
      "is_active": true,
      "created_at": "2026-04-30T12:00:00"
    }
  ],
  "total": 48,
  "page": 1,
  "size": 20
}
```

### 2. POST /api/admin/users/batch-import — 批量导入

**Body** (JSON)：
```json
{
  "college_id": 17,
  "class_id": 5,
  "role": "student",
  "users": [
    { "staff_id": "4125150001", "name": "张三" },
    { "staff_id": "4125150002", "name": "李四" }
  ]
}
```

- 密码默认 = staff_id（bcrypt hash）
- staff_id 已存在则跳过（不覆盖）
- 返回 `{ "created": 45, "skipped": 3 }`

### 3. POST /api/admin/users/{user_id}/reset-password — 重置密码

重置为 staff_id，返回 `{ "ok": true }`。

### 4. PATCH /api/admin/users/{user_id}/toggle-active — 启用/禁用

翻转 is_active，返回 `{ "id": 1, "is_active": false }`。

## 前端（教师端）

在教师端增加 **管理** tab（仅 admin 角色可见）：
- `/pages/admin/users.vue` — 用户列表 + 搜索筛选 + 重置密码按钮 + 禁用按钮
- `/pages/admin/import.vue` — 批量导入表单（JSON 文本框或文件上传）

## 文件变更

| 文件 | 变更 |
|---|---|
| `services/gateway/app/routers/admin.py` | 新建，4 个 API |
| `services/gateway/app/schemas/admin.py` | 新建，请求/响应模型 |
| `services/gateway/app/main.py` | 注册 admin_router |
| `apps/teacher-app/src/pages/admin/users.vue` | 新建，用户列表页 |
| `apps/teacher-app/src/pages/admin/import.vue` | 新建，导入页 |
| `apps/teacher-app/src/pages.json` | 加路由 |
| `apps/teacher-app/src/api/admin.ts` | 新建，API 调用 |
