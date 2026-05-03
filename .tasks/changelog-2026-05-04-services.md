# 变更记录: 事务导办页面服务对接

> 日期: 2026-05-04
> 改动文件: `apps/student-app/src/pages/services/index.vue`
> 验证截图: `.tasks/screenshots/svc-*.png`

## 背景

事务导办页面（服务指南）有多个按钮处于"功能开发中"或仅使用 AI 兜底问答。
通过与企业微信工作台对比，将可用服务的 Web URL 接入，同时新增企业微信中有但学生端原先缺失的服务。

## 变更清单

### A. 现有按钮 URL 更新（4 处）

| 按钮 | 修改前 | 修改后 |
|------|-------|-------|
| 服务大厅 | `http://portal.sdfmu.edu.cn` | `https://ehall.sdfmu.edu.cn/v2/site/index` |
| 接诉即办 | AI 兜底 (`openAiQuestion`) | 外链 `https://ehall.sdfmu.edu.cn/v2/site/appGroup?id=3` |
| 学生课表 | AI 兜底 (`openAiQuestion`) | 外链 `https://app.sdfmu.edu.cn/site/schedule/index` |
| 个人日程 | Coming Soon (`handleComingSoon`) | 外链 `https://app.sdfmu.edu.cn/site/agenda/index` |

### B. 新增服务（5 个）

| 服务 | URL | Material Symbol |
|------|-----|----------------|
| 学术讲座 | `http://academic.sdfmu.edu.cn/index.php?redirect=apply/showlist` | `podium` |
| 预约中心 | `https://ehall.sdfmu.edu.cn/v2/reserve/special_info?id=3` | `event_available` |
| 人脸采集 | `https://fpc.sdfmu.edu.cn/#/home` | `face_retouching_natural` |
| 证件照采集 | `https://ppu.sdfmu.edu.cn` | `photo_camera` |
| 直播山一大 | `https://qjjern.vnet.weizan.cn/live/channelpage-253967?v=1764637917204` | `live_tv` |

### C. 隐藏/注释项（2 个）

| 按钮 | 处理方式 | 原因 |
|------|---------|------|
| 统一消息平台 | `v-if="false"` + HTML 注释 | 企业微信原生聊天应用，无 Web URL |
| 我的申请 | JS 注释 `// { ... }` | 暂无对接 URL |

### D. 未改动项

| 按钮 | 当前行为 | 原因 |
|------|---------|------|
| 校主页 | 外链 `sdfmu.edu.cn` | 无需修改 |
| 信息门户 | 外链 `portal.sdfmu.edu.cn` | 无需修改 |
| 网上报修 | 外链 `metc.sdfmu.edu.cn/...` | 无需修改 |
| 校园网 | 外链 `vpnportal.sdfmu.edu.cn` | 无需修改 |
| 空教室申请 | AI 兜底 | 无 Web URL，AI 问答是合理兜底 |
| 校医院 | AI 兜底 | 同上 |
| 班车查询 | AI 兜底 | 同上 |
| 更多 | AI 兜底 | 导向 AI 问答"医小管能帮什么" |
| 成绩查询 | 外链 `jwc.sdfmu.edu.cn` | 无需修改 |
| 图书馆 | 外链 `202.194.232.127` | 无需修改 |
| 学生邮箱 | 外链 `mail.sdfmu.edu.cn` | 无需修改 |
| 我的提问 | 跳转聊天历史 | 无需修改 |

## 校园服务网格布局（修改后）

```
┌──────────┬──────────┬──────────┬──────────┐
│ 空教室申请 │ 网上报修🔗 │ 接诉即办🔗 │ 校园网🔗  │
├──────────┼──────────┼──────────┼──────────┤
│ 校医院    │ 班车查询  │ 学术讲座🔗 │ 预约中心🔗 │
├──────────┼──────────┼──────────┼──────────┤
│ 人脸采集🔗 │ 证件照🔗  │ 直播山一大🔗│ 更多 ···  │
└──────────┴──────────┴──────────┴──────────┘
🔗 = 有外链 URL     无标记 = AI 问答兜底
```

## 验证

通过 Playwright 自动化截图验证：
- `svc-1-top.png` — 顶部：hero + 快捷入口 + 校园服务 Row 1-2
- `svc-2-scroll1.png` — 滚动后：校园服务 Row 3 + 学业 + 个人（完整视图）
- `svc-3-scroll2.png` — 继续滚动确认底部完整

所有按钮、图标、外链标识均显示正确。

## 已知限制

1. **学校服务凌晨不可用** — 部分 URL（如 app.sdfmu.edu.cn、ehall.sdfmu.edu.cn）在凌晨时段可能无法访问，白天正常
2. **统一消息平台/辅导员通知** — 企业微信原生应用，没有独立 Web URL，无法从 H5 对接
3. **SSO 问题** — 从 H5 打开学校系统可能需要用户手动登录（企业微信内置浏览器会自动 SSO，外部浏览器不会）
