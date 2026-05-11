# 医小管 · 宣传视频工程

> 这个目录用来沉淀宣传视频/产品演示视频的全部规划、技术方案、脚本、资源、产出。
> 当前阶段：**技术可行性已验证**，进入脚本规划讨论阶段。

## 文档索引

| 序号 | 文件 | 内容 | 状态 |
|---|---|---|---|
| 01 | [`01-tech-feasibility.md`](./01-tech-feasibility.md) | 技术路线可行性分析（Playwright + Remotion + 配音 + Rotato） | ✅ 第一稿 |
| 02 | [`02-pages-inventory.md`](./02-pages-inventory.md) | 页面清单与截图（教师端） | ✅ 第一稿 |
| 03 | [`03-ae-template-analysis.md`](./03-ae-template-analysis.md) | AE 模板分析（iPhone 14 Pro，场景扫描） | ✅ 完成 |
| 04 | [`04-script-plan.md`](./04-script-plan.md) | **导演剧本契约 v3**（已敲定形态/时长/视角/分屏/录制环境/输出格式） | ✅ v3 定稿 |
| 05 | _05-asset-checklist.md_ | 资源清单（字体、音乐、配音 API、品牌） | 📋 待写 |
| 06 | _06-render-pipeline.md_ | 完整渲染流水线说明 | 📋 待写 |

## 当前进度

- ✅ **PoC v1 跑通**：Playwright 录 student-app 21s → Remotion 加 zoom/pulse/label → 渲染 1080×1920 mp4
- ✅ **可行性已验证**：见 `01-tech-feasibility.md`
- ✅ **导演剧本契约 v3 定稿**：见 `04-script-plan.md`
- 🔧 **PoC 输出**：`../.tmp/demo-video/remotion/out/final-v1.mp4`
- � **当前阻塞**：等用户单独会话完成 Phase 0 UI 优化（学生端 + 教师端演示路径）
- 📋 **UI 完成后**：按 04 文档 §6 启动信号推进 T8/T9/T10/T11/T12/T13/T14/T15

## 相关目录

- `../.tmp/demo-video/` — PoC 工程（Playwright 录制 + Remotion 后处理）
- `../apps/student-app/` — 学生端源码（UniApp Vue3）
- `../apps/teacher-app/` — 教师端源码（Vue3 + Element Plus）
