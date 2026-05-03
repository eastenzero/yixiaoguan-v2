# 2026-05-03 冒烟问题修复报告

> 执行时间：2026-05-03 20:00 ~ 20:15 (UTC+8)

## 修复总览

| # | 问题 | 修复方式 | 验证结果 |
|---|------|---------|---------|
| 1 | WS 广播丢失（学生收不到老师回复 + 教师工作台不刷新） | Gateway `--workers 2` → `--workers 1` | ✅ systemd 重启成功，health OK |
| 2 | 教师工作台无 WS 监听 | `dashboard/index.vue` 添加 `escalation_notify` / `status_changed` 监听 + 30s 轮询兜底 | ✅ 代码改动 + H5 build + 部署 |
| 3 | `/health` 返回前端 HTML | nginx 添加 `location = /health` 精确代理 | ✅ `curl https://yxg.xiaoguan.site/health` → JSON |
| 4 | Manrope 字体 404 | 下载 woff2 自托管到 `static/fonts/`，两端 `App.vue` 改为本地路径 | ✅ HTTP 200 |
| 5 | favicon 404 | 创建 SVG favicon 放入 `static/`，`index.html` 添加 `<link rel="icon">` | ✅ HTTP 200 |
| 6 | 测试数据残留 entry.id=7 | DB 删除 `unanswered_questions` + `kb_suggestions`，Dify 删除 document | ✅ 已清理 |

## 服务端改动明细

### HK 64.90.13.65

- `/etc/systemd/system/yxg-gateway.service`: `--workers 2` → `--workers 1`
- `/etc/nginx/sites-enabled/yxg-student-domain`: 添加 `location = /health` 代理块
- `/var/www/yxg-student/`: 重新部署 student-app H5 build（含自托管字体 + favicon）
- `/var/www/yxg-teacher/`: 重新部署 teacher-app H5 build（含自托管字体 + favicon）
- 目录权限修正：`chmod -R 755` 确保 nginx www-data 可访问新增 static 目录

### 代码改动

- `apps/teacher-app/src/pages/dashboard/index.vue` — 添加 WS 监听（+15 行）
- `apps/student-app/src/App.vue` — 字体 URL 改本地
- `apps/teacher-app/src/App.vue` — 字体 URL 改本地
- `apps/student-app/index.html` — 添加 favicon link
- `apps/teacher-app/index.html` — 添加 favicon link + title
- `apps/student-app/src/static/fonts/Manrope-Variable.woff2` — 新增（24KB）
- `apps/teacher-app/src/static/fonts/Manrope-Variable.woff2` — 新增（24KB）
- `apps/student-app/src/static/favicon.svg` — 新增
- `apps/teacher-app/src/static/favicon.svg` — 新增

## 额外修复（发现并顺带处理）

- scp 部署后 `/var/www/yxg-*` 目录权限为 700（root only），nginx www-data 无法读取 → 已 chmod 755

## 待后续验证

- **WS 实时推送**：需要实际操作"学生转人工 → 教师接单 → 教师回复"完整流程，确认学生端实时收到老师回复消息
- **教师工作台实时刷新**：需要实际操作转人工，确认工作台待处理数量实时更新

## 未修改项

- tsconfig.json 的 `importsNotUsedAsValues` / `preserveValueImports` 警告：预先存在的 TS 配置问题，与本次修复无关
- Sass `@import` deprecation 警告：预先存在，需整体迁移到 `@use`，不在本轮范围
