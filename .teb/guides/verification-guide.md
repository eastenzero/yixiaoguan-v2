# 验证层级指南（L0 - L3）

> 当你不确定一个任务的 done_criteria 该怎么写时，翻阅这份指南。

---

## 总览

| 层级 | 名称 | 自动化？ | 验证什么 | 可信度 |
|------|------|---------|---------|--------|
| L0 | 存在性检查 | ✅ 脚本 | 文件/函数/导出是否存在 | 最高 |
| L1 | 静态检查 | ✅ 工具 | 类型/语法/格式是否正确 | 高 |
| L2 | 运行时检查 | ✅ 测试 | 功能是否按预期运行 | 高 |
| L3 | 语义检查 | ❌ 人工 | 是否真的解决了问题 | 取决于审查者 |

**原则**：尽量把验证写到 L0-L2 层，因为它们是机器可执行的、结果确定的。L3 是兜底，不是首选。

---

## L0：存在性检查

**验证的问题**：东西在不在？

**常见写法**：

```
L0: "src/api/auth/login.ts 文件存在"
L0: "src/api/auth/login.ts 导出 loginHandler 函数"
L0: "tests/api/auth/login.test.ts 文件存在"
L0: "数据库中存在 users 表"
```

**如何手动验证**：
```bash
# 文件是否存在
test -f src/api/auth/login.ts && echo "PASS" || echo "FAIL"

# 函数是否导出（简单 grep）
grep -q "export.*loginHandler" src/api/auth/login.ts && echo "PASS" || echo "FAIL"
```

**什么时候用**：几乎所有任务都应该有 L0。它是最基础的"你至少产出了东西"的确认。

---

## L1：静态检查

**验证的问题**：东西语法上对不对？

**常见写法**：

```
L1: "tsc --noEmit 无错误"
L1: "eslint src/api/auth/ 无 error 级别报告"
L1: "python -m py_compile src/auth/login.py 成功"
L1: "mvn compile 无错误"
```

**如何验证**：
```bash
# TypeScript 类型检查
npx tsc --noEmit

# ESLint
npx eslint src/api/auth/ --max-warnings 0

# Python 语法检查
python -m py_compile src/auth/login.py
```

**什么时候用**：涉及代码修改的任务都应该有 L1。它确保新代码不会破坏项目的编译/类型安全。

---

## L2：运行时检查

**验证的问题**：东西跑起来对不对？

**常见写法**：

```
L2: "npm test -- tests/api/auth/login.test.ts 全部通过"
L2: "pytest tests/auth/test_login.py 全部通过"
L2: "curl -X POST http://localhost:3000/api/auth/login -d '{...}' 返回 200"
L2: "docker compose up -d 后所有容器状态为 healthy"
```

**如何验证**：
```bash
# 运行指定测试
npm test -- tests/api/auth/login.test.ts

# 或 Python
pytest tests/auth/test_login.py -v

# 或 API 调用
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

**什么时候用**：功能性任务必须有 L2。它是最有价值的验证层——证明功能真的能用，不是只能编译。

**写 L2 的技巧**：
- 优先写已有测试框架能跑的检查（如 Jest、Pytest）
- 如果任务本身就是写测试，L2 就是"测试本身能通过"
- 如果没有测试框架，可以用 curl / 脚本做简单的端到端检查

---

## L3：语义检查

**验证的问题**：东西在业务/用户层面对不对？

**常见写法**：

```
L3: "用户可以用邮箱+密码登录，登录成功后 JWT 包含 userId 和 exp 字段"
L3: "登录失败时返回友好的错误提示，不暴露'用户不存在'还是'密码错误'"
L3: "页面加载时间体感流畅，无明显白屏"
L3: "代码结构清晰，新开发者能在 10 分钟内理解登录流程"
```

**如何验证**：
- 人工测试（你自己用一下）
- 交给强 AI（用 T2 Reviewer 提示词）
- 代码审查

**什么时候用**：
- 涉及用户体验的任务
- 涉及安全性的任务
- L0-L2 无法覆盖的"质量"方面

**注意**：L3 是最不可靠的验证层，因为它依赖人的判断。尽量把 L3 的内容"降级"为 L2——比如把"登录失败时返回友好提示"变成一个具体的测试用例。

---

## 常见场景的 done_criteria 示例

### 场景：新建一个 API 端点

```yaml
done_criteria:
  L0: "src/api/auth/login.ts 存在且导出 loginHandler"
  L1: "tsc --noEmit 无错误"
  L2: "npm test -- tests/api/auth/login.test.ts 全部通过（至少包含成功登录和失败登录两个用例）"
  L3: "JWT 有效期为 24 小时，payload 包含 userId"
```

### 场景：新建一个前端页面

```yaml
done_criteria:
  L0: "src/pages/Login.tsx 存在"
  L1: "tsc --noEmit 无错误；eslint 无 error"
  L2: "npm run build 成功；dev server 启动后 /login 页面可访问（HTTP 200）"
  L3: "页面包含邮箱输入框、密码输入框和登录按钮；表单验证在客户端生效"
```

### 场景：修复一个 Bug

```yaml
done_criteria:
  L0: "修改的文件存在且无语法错误"
  L1: "tsc --noEmit 无错误"
  L2: "新增的回归测试通过（测试复现了原 bug 场景并验证修复）"
  L3: "原始 bug 报告中描述的现象不再出现"
```

### 场景：编写文档

```yaml
done_criteria:
  L0: "docs/api/auth.md 存在"
  L1: "markdown lint 无错误（如果有的话）"
  L2: "文档中所有代码示例可以直接复制运行"
  L3: "文档覆盖了登录、注册、登出三个流程，每个流程有请求/响应示例"
```

---

## 核心原则

1. **能写 L2 就不要只写 L3**——机器验证 > 人工判断
2. **L0-L2 是及格线，L3 是加分项**——如果 L0-L2 全 FAIL，任务一定没完成
3. **完成标准面向目标状态**——不写"实现了 loginHandler"，写"POST /api/auth/login 返回 JWT"
4. **每条标准必须是可执行的**——读完标准就知道该运行什么命令来验证
