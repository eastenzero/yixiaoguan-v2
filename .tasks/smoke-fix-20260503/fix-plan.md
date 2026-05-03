# 2026-05-03 冒烟问题修复落地计划

## 修复范围

基于 `analysis.md` 的验证结论，本轮修复 5 项：

---

## Step 1: Gateway 降为单 Worker（P0，影响 Issue 2 + 3）

**改动位置**：HK 服务器 `/etc/systemd/system/yxg-gateway.service`

**操作**：
```
ExecStart=... --workers 2  →  ExecStart=... --workers 1
```

**验证**：
```bash
systemctl daemon-reload && systemctl restart yxg-gateway
curl -s http://127.0.0.1:8100/health | python3 -m json.tool
```

**影响分析**：内测阶段并发量极低，单 worker 完全足够。长期方案是引入 Redis pub/sub 做跨 worker 广播。

---

## Step 2: 教师工作台添加 WS 监听（P1，Issue 2 代码修复）

**改动文件**：`apps/teacher-app/src/pages/dashboard/index.vue`

**具体改动**：
1. 导入 `wsManager`
2. `onMounted` 中注册 `escalation_notify` 和 `status_changed` 监听 → 触发 `loadPendingQuestions()`
3. `onUnmounted` 中取消监听
4. 添加 30s 轮询兜底（与 `questions/index.vue` 一致）

**验证**：
- 学生端发起转人工
- 教师端停留在工作台页面，不刷新
- 期望：工作台实时更新待处理数量和列表

---

## Step 3: nginx 添加 `/health` 精确代理（P1，Issue 1）

**改动位置**：HK 服务器 `/etc/nginx/sites-enabled/yxg-student-domain`

**具体改动**：在 `location /` 之前（或内部第一个）添加：
```nginx
location = /health {
    proxy_pass http://127.0.0.1:8100;
    proxy_set_header Host $host;
}
```

**验证**：
```bash
nginx -t && systemctl reload nginx
curl -s https://yxg.xiaoguan.site/health | python3 -m json.tool
# 期望返回 {"status":"ok","version":"2.0.0","checks":{...}}
```

---

## Step 4: 自托管 Manrope 字体 + 添加 favicon（P2，Issue 4）

### 4a: 自托管字体

**操作**：
1. 下载 Manrope woff2 到两端 `static/fonts/Manrope-Variable.woff2`
2. 修改两端 `App.vue` 的 `@font-face src` 指向本地文件

**改动文件**：
- `apps/student-app/src/App.vue`
- `apps/teacher-app/src/App.vue`

### 4b: 添加 favicon

**操作**：
1. 创建简单的医小管 favicon.ico
2. 放置到两端 `public/favicon.ico`（uni-app 构建会复制到 dist 根目录）

**验证**：H5 构建后确认 dist 中有 `fonts/` 和 `favicon.ico`

---

## Step 5: 清理测试数据（P3，Issue 5）

**操作**（HK 服务器）：
1. 数据库清理 `entry.id=7`
2. Dify 清理 document `4884e802-c199-4018-b4e0-0ddfe379ab2f`

---

## 执行顺序

```
Step 1 (workers) → Step 2 (dashboard WS) → Step 3 (nginx health) → Step 4 (font+favicon) → Step 5 (cleanup)
```

Step 1-3 为服务端改动，可先完成并验证。
Step 4 需要本地改代码 + 重新 build H5 + 部署。
Step 5 为一次性运维操作。

## 预期结果

修复完成后，所有冒烟项应为 PASS，可输出"完整冒烟测试全部通过"结论。
