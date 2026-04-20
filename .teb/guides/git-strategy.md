# Git Commit 策略

## 原则

- **一个任务一个 commit**——每个 commit 对应一个 _task.md 从 pending → done
- **只 commit 验证通过的代码**——T2 说 PASS 之后再 commit
- **commit message 引用 task id**——方便回溯
- **不 commit 未验证的代码到 main**

## Commit 时机

### 本地 commit（自动，由 T2 执行）

| 触发条件 | 动作 |
|---------|------|
| T2 验证单个任务 L0-L2 全 PASS | `git add` + `git commit`（一个任务一个 commit） |
| T1 验收一个 batch L3 PASS | `git tag <batch-name>-done` |
| 集成测试任务通过 | `git tag <module>-integrated` |

本地多 commit 几次没有坏处，反而方便回溯。

### 远端 push（需要人确认）

| 触发条件 | 动作 |
|---------|------|
| 一个 batch 全部完成 + T1 验收通过 | `git push` |
| 一个里程碑完成 | `git push --tags` |

远端推送代表"这段工作对外可见"，需要你或 T1 明确触发。

## Commit Message 格式

```
<type>(<scope>): <简述> [task:<task-id>]
```

类型：
- `feat` — 新功能
- `fix` — Bug 修复
- `test` — 测试
- `refactor` — 重构
- `docs` — 文档

示例：
```
feat(auth): login API returns JWT [task:login-api]
fix(kb): knowledge base query returns empty results [task:kb-empty-fix]
test(auth): integration test for auth + session [task:auth-integration]
```

## 分支策略

```
main ← 只合并验证通过的代码
 │
 ├── feat/目标名 ← T3 在这里工作
 │     每个任务 PASS 后 commit 到这个分支
 │     batch 全部完成 + L3 通过后合并到 main
 │
 └── fix/bug名 ← bugfix 同理
```

简单项目可以直接在 main 上工作，但建议至少用 feature branch 隔离未完成的工作。

## 谁负责什么

| 角色 | 本地 commit | 远端 push |
|------|-----------|----------|
| T3 | ❌ 不 commit | ❌ |
| T2 | ✅ 验证 PASS 后自动 commit | ❌ |
| T1 | ✅ 验收后打 tag | 可以（如授权） |
| 你 | 随时可以 | ✅ 最终决定 |

## 回滚

每个 commit 对应一个任务，每个任务有 `_report.md` 作为验证证据。回滚时：
1. 找到出问题的 task id
2. `git log --grep="task:<task-id>"` 定位 commit
3. `git revert <commit>` 回滚
