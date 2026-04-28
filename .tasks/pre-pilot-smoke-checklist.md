# 内测启动前冒烟测试 checklist

> 全部勾完即可启动 50 人内测。预估 15-30 分钟走完。

## 测试账号

| 角色 | URL | staff_id | 初始密码 |
|---|---|---|---|
| 学生 | http://192.168.100.165/ | `4125150001` (黄静) | `4125150001` |
| 学生 | http://192.168.100.165/ | `4125150036` (叶涛宁，typo 已修) | `4125150036` |
| 辅导员 | http://192.168.100.165:81/ | `anjing` | `Anjing@yxg2026` |

## 学生侧（手机/电脑浏览器）

- [ ] **能登录**：学号+密码 → 进主页
- [ ] **首页加载**：4 个 tab，"我的问题" "应用" "知识" "我的"
- [ ] **AI 对话**：输入问题（如"奖学金怎么申请？"）→ AI 回答含 "公共事业管理 2025-1 班" / "医药管理学院" 关键词（验证 D1 user-context 集成）
- [ ] **拒答 sticky CTA** (P0-2)：问 AI 一个会被拒答的问题（如"教务系统的具体接口"）→ 底部出现 sticky CTA 让用户问辅导员
- [ ] **escalate 提交**：点 sticky CTA → 进 escalate 页 → 填问题 + 提交 → 跳到 my_questions
- [ ] **my_questions 列表**：看到刚提交的，状态 `pending`
- [ ] **未读角标** (P1-1)：辅导员回复后回到这里，应有红点/badge
- [ ] **退出登录**：能退到登录页，再次登录正常

## 辅导员侧（电脑浏览器）

- [ ] **能登录**：anjing/Anjing@yxg2026 → dashboard
- [ ] **question_list**：看到学生的 pending 问题，含学号 + 学生姓名
- [ ] **打开问题详情**：能看到学生原始问题 + AI 回答历史
- [ ] **写回答 + 提交**：填回答 → 提交 → 状态变 resolved/teacher_answered
- [ ] **学生端验证**：返回学生侧浏览器（同一登录），my_questions 列表显示已回答 + 红点（badge）
- [ ] **知识库** (R08 KB)：访问 /knowledge → 能看到 unanswered-top + 提交 draft

## 系统侧（指挥官检查）

- [ ] **gateway systemd**：`sudo systemctl is-active yixiaoguan-gateway` = active
- [ ] **gateway auto-restart**：`sudo kill -9 $(pgrep -f 'uvicorn.*8100')` → 8s 内自动恢复
- [ ] **DB 备份**：`ls -lh /home/easten/backups/yxgv2-*.sql.gz` 至少 1 个 ≥ 50K 文件
- [ ] **crontab 含 backup**：`crontab -l | grep pg-backup`
- [ ] **rate-limit**（codex 完成后）：6 次 wrong password from same IP → 第 6 次得 429
- [ ] **JWT 强校验**：`grep jwt_secret /home/easten/dev/yixiaoguan-v2/services/gateway/.env | wc -c` ≥ 35（包括 `jwt_secret=` 前缀）

## 已知不做（内测后跟进）

- HTTPS 自签证书（避免浏览器警告吓退测试用户；微信小程序上线时再做 LE 证书）
- ufw 端口防火墙（内网 50 人测试，收益有限；操作有锁住 ssh 风险）
- 首次登录强制改密（user 选 B 方案，依赖班级群通知改密）

## 内测启动通知（建议发到班级群）

```
@全体同学

医小管 v2 内测正式启动 ✨

学生端访问：http://192.168.100.165/
教师端访问：http://192.168.100.165:81/  (辅导员安静老师专用)

【重要】登录账号
- 账号 = 你的学号
- 初始密码 = 你的学号

【安全提醒】
所有同学**首次登录后请立刻修改密码**（点"我的"→"修改密码"）。
默认密码很弱，不改的话别人可以轻易登录你的账号。

【使用建议】
- 优先和 AI 对话尝试解决问题
- AI 答不出或回答不满意时，点底部按钮把问题转给辅导员
- 辅导员安静老师会在工作时间内回复

发现 bug、不正常或建议 → 联系班长汇总反馈给开发组
```
