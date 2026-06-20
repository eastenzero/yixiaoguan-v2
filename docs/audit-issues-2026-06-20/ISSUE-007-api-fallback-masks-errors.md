# ISSUE-007 教师端知识 API fallback 容易掩盖真实错误

## 现象

教师端知识 API 对部分接口做了 localStorage fallback。接口失败时页面可能静默展示缓存或空列表，而不是暴露真实后端错误。

## 证据

- `apps/teacher-app/src/api/knowledge.ts` 中存在 `readKnowledgeCache()`、`writeKnowledgeCache()`、`filterCachedEntries()`。
- `getKnowledgeEntries()`、`getKnowledgeDetail()`、`offlineEntry()`、审核通过/驳回等路径存在 catch fallback。
- 教师端“我的知识”当前为空，单看 UI 难判断是无数据、权限问题、接口缺失还是 fallback 后空缓存。

## 影响

- 内测时问题被静默吞掉，不利于排查。
- 老师可能以为操作成功或数据为空，实际是接口失败。
- 审核/下线这类操作如果 fallback 成功提示，会造成线上状态错觉。

## 涉及区域

- `apps/teacher-app/src/api/knowledge.ts`
- 教师端 toast/error UI

## 建议修复方向

- 内测环境关闭写操作 fallback，至少展示错误 toast。
- 对读取接口可以保留缓存，但必须标注“离线缓存/接口失败”。
- 审核、发布、下线等写操作不能本地伪成功。

