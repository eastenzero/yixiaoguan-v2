# 学生端事务导办外链跳转说明

本文记录学生端“事务导办”外链跳转规则，避免后续新增入口时把 SSO 参数或微信跳转参数错误地加到所有链接上。

## 相关代码

- 页面入口：`apps/student-app/src/pages/services/index.vue`
- 跳转工具：`apps/student-app/src/composables/useServiceNavigation.ts`
- 小程序兜底页：`apps/student-app/src/pages/services/webview.vue`

事务导办页面不要直接拼 SSO 登录地址，应统一调用 `openExternal(url, options)`。

## 跳转选项

`openExternal` 支持两个容易混淆的选项：

```ts
openExternal(url, {
  useSso: true,
  ssoNoAutoRedirect: true,
})
```

| 选项 | 作用 | 默认行为 |
| --- | --- | --- |
| `useSso` | 是否把目标链接包装成 `https://sso.sdfmu.edu.cn/login?service=<target>` | 未传时，`.sdfmu.edu.cn` 且不是 `www.sdfmu.edu.cn` 的域名会自动走 SSO |
| `ssoNoAutoRedirect` | 是否额外追加 `noAutoRedirect=true` | 默认不追加，必须显式 opt-in |

重点：`useSso: true` 不等于可以加 `noAutoRedirect=true`。这两个开关必须分开判断。

## 三类链接

### 1. 直接打开

适用于学校官网、校内普通内容页、第三方直播页、IP 地址站点等不需要统一认证的链接。

```ts
openExternal('https://www.sdfmu.edu.cn')
openExternal('https://metc.sdfmu.edu.cn/info/1073/1954.htm', { useSso: false })
openExternal('http://202.194.232.127/index.html')
```

注意：普通校内内容页如果域名是 `.sdfmu.edu.cn`，要显式传 `useSso: false`，否则会被自动识别为 SSO 链接。

### 2. 只走 SSO，不加 `noAutoRedirect`

适用于教务、邮箱、学术讲座等校内业务系统。

```ts
openExternal('http://jwc.sdfmu.edu.cn', { useSso: true })
openExternal('https://mail.sdfmu.edu.cn/', { useSso: true })
```

生成结果应类似：

```text
https://sso.sdfmu.edu.cn/login?service=http%3A%2F%2Fjwc.sdfmu.edu.cn
```

不要额外加 `noAutoRedirect=true`，除非已经确认该系统需要这个参数。

注意：`app.sdfmu.edu.cn` 系列移动应用入口（如学生课表、个人日程）不能直接作为 CAS `service`，否则会出现“服务未授权”。代码会自动转换为：

```text
https://app.sdfmu.edu.cn/a_sdfmu/api/sso/index?redirect=<target>&from=wap
```

再交给统一身份认证登录，并追加 `noAutoRedirect=1`。

### 3. 走 SSO，并显式加 `noAutoRedirect`

目前只给信息门户和 ehall 系列入口使用，主要用于微信内跳转时保持落地行为正常。

```ts
openExternal('http://portal.sdfmu.edu.cn', {
  useSso: true,
  ssoNoAutoRedirect: true,
})

openExternal('https://ehall.sdfmu.edu.cn/v2/site/index', {
  useSso: true,
  ssoNoAutoRedirect: true,
})
```

生成结果应类似：

```text
https://sso.sdfmu.edu.cn/login?noAutoRedirect=true&service=https%3A%2F%2Fehall.sdfmu.edu.cn%2Fv2%2Fsite%2Findex
```

## 新增入口检查清单

新增事务导办链接时，先按下面顺序判断：

1. 这是普通网页还是需要登录的业务系统？
2. 如果是普通网页，是否因为 `.sdfmu.edu.cn` 域名会被自动 SSO？需要时加 `useSso: false`。
3. 如果是业务系统，先只加 `useSso: true`。
4. 只有信息门户或 ehall 系列、且已验证微信内必须如此时，才加 `ssoNoAutoRedirect: true`。
5. 不要手写 `https://sso.sdfmu.edu.cn/login?...`，统一走 `openExternal`。

## 验证建议

至少验证 URL 生成结果：

- 信息门户、ehall：应包含 `noAutoRedirect=true`。
- app.sdfmu.edu.cn：应通过 `/a_sdfmu/api/sso/index` 中转，并包含 `noAutoRedirect=1`。
- 教务、邮箱、学术讲座等：应走 SSO，但不包含 `noAutoRedirect=true`。
- 校园网 / VPN：`vpnportal.sdfmu.edu.cn` 不能直接作为 CAS `service`；没有可验证授权入口前，不应放成事务导办按钮。
- 网上报修、学校官网、直播等：不应被 SSO 包装。

能登录真实环境时，再分别在普通浏览器和微信内打开抽查。SSO 页面可能出现滑块安全验证，不建议把账号密码写入自动化脚本。
