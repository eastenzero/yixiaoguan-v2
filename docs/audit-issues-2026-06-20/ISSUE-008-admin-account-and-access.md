# ISSUE-008 线上账号与管理入口不稳定

## 现象

用户提供的教师账号 `anjing` 可登录，管理员账号 `admin` 登录失败。当前知识审核和用户管理相关能力无法用管理员账号完整验证。

## 证据

- 用户提供的教师内测账号可登录教师端。
- `admin / <内测管理员密码>` 曾返回 401。
- 之前线上 DB 检查显示 `admin` staff_id 可能不存在。
- 教师账号访问 `/api/v1/knowledge/reviews/pending` 返回 403，符合权限预期，但管理员路径尚未实际验证。

## 影响

- 全校级知识审核流程无法确认。
- 管理员用户管理、审核、全局发布能力不能内测。
- 群里给出的账号信息和线上实际状态不一致，会影响内测信任。

## 涉及区域

- 用户初始化/导入脚本
- `services/gateway/app/routers/auth.py`
- `services/gateway/app/routers/knowledge.py`
- `apps/teacher-app/src/pages/admin/*`

## 建议修复方向

- 查线上 users 表确认 admin 是否存在、角色是否为 admin、密码哈希是否正确。
- 修复或重建管理员账号。
- 用 admin 验证待审核、通过、驳回、全局发布流程。

## 2026-06-20 修复记录

- 线上只读确认：`users` 表中存在旧管理员 `A001`，角色为 `admin`，账号启用，密码哈希为 bcrypt；未发现 `staff_id = 'admin'`。
- 线上接口验证：`admin / <内测管理员密码>` 返回 401；旧管理员账号可登录，且可访问 `/api/v1/knowledge/reviews/pending` 和 `/api/admin/users`。
- 本地新增幂等脚本 `scripts/ensure_admin_user.py`：通过环境变量指定管理员账号和密码，创建或修复 `admin` 用户，强制角色为 `admin`、启用账号，并用 bcrypt 重新生成密码哈希；脚本不会输出哈希。

线上修复建议命令（在部署机仓库根目录执行，密码通过环境变量传入，不输出明文或哈希）：

```bash
export YXG_BOOTSTRAP_ADMIN_STAFF_ID=admin
export YXG_BOOTSTRAP_ADMIN_NAME=内测管理员
read -r -s -p "Admin password: " YXG_BOOTSTRAP_ADMIN_PASSWORD
echo
export YXG_BOOTSTRAP_ADMIN_PASSWORD
python3 scripts/ensure_admin_user.py
unset YXG_BOOTSTRAP_ADMIN_PASSWORD
```

执行后用 `admin / <内测管理员密码>` 登录教师端，并验证：

- `/api/auth/me` 返回 `role = admin`。
- `/api/v1/knowledge/reviews/pending` 返回 200。
- `/api/admin/users` 返回 200。
