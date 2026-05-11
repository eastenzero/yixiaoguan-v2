# AE 模板分析 · iPhone 14 Pro App Promo

> 2026-05-11 · 模板选型与场景扫描完成
> 下一步：新对话中规划场景分配 + 截图替换

---

## 选定模板

| 属性 | 值 |
|---|---|
| **名称** | App Promo Phone 14 Pro Mockup Pack |
| **作者** | MotionFox (Videohive) |
| **Videohive ID** | 40526693 |
| **机型** | iPhone 14 Pro（灵动岛 + 三摄） |
| **分辨率** | 3840×2160 (4K) |
| **帧率** | 30fps |
| **总时长** | 251 秒 (4 分 11 秒) |
| **总场景** | 30 个 |
| **手机配色** | 5 种 (Purple / Blue / Black / Silver / Gold) |
| **屏幕尺寸** | 1170×2532 (iPhone 14 Pro 原生分辨率) |
| **字体** | Lato + Montserrat (免费 Google 字体) |
| **渲染方式** | 预渲染 .mov（手机机身烘焙在视频中） |

### 文件路径

```
AEP: E:\BaiduNetdiskDownload\AE模板-手机APP展示宣传片头开场动画40526693\
     App Promo Phone 14 Pro Mockup Pack\
     Phone 14 Pro App Presentation By MotionFox\
     Phone 14 Pro_App Presentation_CS6.aep
```

---

## 场景扫描结果

### ✅ 纯正面（无背面 logo）— 17 场景，共 140 秒

#### A. 直接有屏幕占位 — 9 场景，76 秒，11 个屏幕槽位

| 场景 | 时长 | 屏幕数 | 文字区 | 适合展示 |
|------|------|--------|--------|----------|
| SCENE_01 | 8s | 1 屏 | 无 | 单屏特写，开场 |
| SCENE_04 | 8s | 1 屏 | 有 | 单屏 + 功能说明文字 |
| SCENE_05 | 8s | 1 屏 | 无 | 单屏特写 |
| SCENE_06 | 8s | 1 屏 | 无 | 单屏特写 |
| SCENE_08 | 8s | 1 屏 | 无 | 单屏特写 |
| SCENE_09 | 10s | 1 屏 | 无 | 单屏，时间稍长 |
| SCENE_10 | 10s | 2 屏 | 无 | 双屏对比/切换 |
| SCENE_13 | 8s | 2 屏 | 无 | 双屏展示 |
| SCENE_15 | 8s | 1 屏 | 有 | 单屏 + 功能说明文字 |

#### B. 预合成场景（屏幕嵌套在 PreComp 内）— 8 场景，64 秒

| 场景 | 时长 | 嵌套屏幕数 | 文字区 | 备注 |
|------|------|------------|--------|------|
| SCENE_23 | 8s | 1 屏 | 有 | 通过 S23_PreComps |
| SCENE_24 | 8s | 2 屏 | 有 | 通过 S24_PreComps |
| SCENE_25 | 8s | 2 屏 | 有 | 通过 S25_PreComps |
| SCENE_26 | 8s | 4 屏 | 有 | 通过 S26_PreComps |
| SCENE_27 | 8s | 5 屏 | 有 | 通过 S27_PreComps |
| SCENE_28 | 8s | 5 屏 | 有 | 通过 S28_PreComps |
| SCENE_29 | 8s | 2 屏 | 无 | 通过 S29_PreComps |
| SCENE_30 | 8s | 0 | 有 | 可能是片尾/Logo 场景 |

#### 合计可用

- **17 场景**，**140 秒**素材
- 直接屏幕槽位 11 个 + 预合成嵌套屏幕 21+ 个
- 做 40-60 秒 demo 视频挑 5-8 个场景绰绰有余

### ❌ 有背面（会露出仿苹果 logo）— 13 场景，110 秒

SCENE_02 / 03 / 07 / 11 / 12 / 14 / 16 / 17 / 18 / 19 / 20 / 21 / 22

> 这些场景不建议使用。logo 烘焙在 .mov 中无法移除。

---

## 模板结构要点

### 主合成

```
PREVIEW COMPS (3840×2160, 251s, 32 layers)
├── Device Color Select    ← 顶层，控制手机配色
├── SCENE_01 ~ SCENE_30    ← 30 个场景，按时间顺序排列
└── Dark Royal Blue Solid  ← 背景色
```

### 每个 SCENE 的图层结构（以 SCENE_01 为例）

```
P01/P02 Controller   ← 3D 手机位置控制器
Camera               ← 3D 摄像机动画
Screen Camera Cut     ← 屏幕追踪
Screen Frame         ← 边框（通常 disabled）
Screen 01            ← ⭐ 屏幕内容占位（1170×2532）
Purple / Blue / Black / Silver / Gold  ← 5 种手机配色层
Matte / Shadow       ← 遮罩和阴影
Text Holder          ← 文字占位（部分场景有）
```

### 替换内容的方法

1. **替换屏幕截图**：找到对应 SCENE 的 `Screen 01` 合成 → 替换内部素材
2. **修改文字**：找到 `Text Holder` 合成 → 编辑文字内容
3. **切换手机配色**：在 `Device Color Select` 层或各 SCENE 内启用/禁用对应颜色层
4. **修改背景色**：改 `Dark Royal Blue Solid` 的颜色

### 输出合成

- `4K` (3840×2160) — 用于高质量渲染
- `HD` (1920×1080) — 用于快速预览

---

## MCP Bridge 已有能力

在 `F:\Documents\code\after-effects-mcp\` 项目中已扩展：

- `importAndReplace` — 导入文件并替换图层素材
- `renderFrame` — 渲染指定帧为 PNG 预览
- `getProjectInfo` / `listCompositions` / `getLayerInfo` — 查询项目结构

> ⚠️ MCP 通过 Windsurf 调用不太稳定（频繁超时），建议后续直接写 .jsx 脚本在 AE 中运行。

---

## 已有 App 截图资源

截图目录：`F:\Documents\code\yixiaoguan-v2\.tmp\demo-video\out\explore-teacher\`

教师端 10 个页面已截图（详见 `02-pages-inventory.md`）：
- ⭐ 数据看板 (analytics) — 最佳全屏素材
- ⭐ 知识库 (knowledge) — 展示核心功能
- ⭐ 工作台 (dashboard) — 紫粉渐变 Hero 卡
- ⭐ 个人中心 (profile) — 身份展示
- ⚠️ 学生提问 (questions) — 需要先造数据

学生端截图待补充。

---

## 下一步（新对话开始）

1. **确认可用截图数量**：教师端 + 学生端各有哪些可用
2. **规划视频脚本**：挑选 5-8 个场景，分配截图，撰写文字
3. **写批量替换脚本**：.jsx 脚本一次性把截图塞入对应 Screen 合成
4. **渲染预览**：逐帧检查效果
5. **导出成片**：选择配乐，最终渲染
