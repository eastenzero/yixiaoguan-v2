# Prompt：AE 模板亮色主题改造 + 镜头精选 + 预览渲染

> 派单创建：2026-05-11 晚 · Cascade 导演产出
> 上游剧本契约：`@F:\Documents\code\yixiaoguan-v2\video\04-script-plan.md`
> 上游 AE 分析：`@F:\Documents\code\yixiaoguan-v2\video\03-ae-template-analysis.md`

---

## 你的任务（3 件并行）

医小管演示视频要做亮色主题改造（之前的 royal blue 深色背景跟整片亮色基调不符）。请你：

- **Part A**：把 AE 模板的背景从深皇家蓝改成浅紫到白渐变；同时调整机身/文字配色让画面整体明亮
- **Part B**：在 17 个无 logo SCENE 里重新评估哪些"亮色背景下视觉最佳"，给出 Top 6 推荐，对比剧本现选的 SCENE_01/05/10/13 给出"保持/替换"建议
- **Part C**：用项目里现有截图占位，渲染一份 30 秒预览 mp4，让用户看亮色主题整体效果

---

## 项目背景

医小管 = 中国大学校园 AI 问答助手。当前在做 4-5 分钟产品演示长片，AE 段是开场后第二段（5-8s intro 之后），约 30 秒，由 5-6 个 iPhone 转场镜头串烧组成，每个镜头屏幕嵌入项目截图。

**整片输出**：1920×1080 横屏 30fps H.264
**主色**：`#7C3AED` 紫
**整体基调**：**亮色** （这是用户 2026-05-11 晚明确的方向修正）

---

## AE 模板信息

| 项 | 值 |
|---|---|
| 模板名 | App Promo Phone 14 Pro Mockup Pack |
| 文件 | `E:\BaiduNetdiskDownload\AE模板-手机APP展示宣传片头开场动画40526693\App Promo Phone 14 Pro Mockup Pack\Phone 14 Pro App Presentation By MotionFox\Phone 14 Pro_App Presentation_CS6.aep` |
| 分辨率 | 4K 主合成 3840×2160；HD 输出 1920×1080 |
| 帧率 | 30fps |
| 总时长 | 251 秒（30 个 SCENE） |
| 屏幕尺寸 | 1170×2532（iPhone 14 Pro 原生） |
| 渲染方式 | 预渲染 .mov（手机机身已烘焙） |
| 字体 | Lato + Montserrat（免费 Google 字体） |
| 17 个无 logo SCENE | SCENE_01/04/05/06/08/09/10/13/15/23/24/25/26/27/28/29/30 |
| 当前剧本选中 | SCENE_01 + SCENE_05 + SCENE_10 + SCENE_13（共 34s） |

主合成图层结构：
```
PREVIEW COMPS (3840×2160, 251s, 32 layers)
├── Device Color Select          ← 顶层，控制手机配色
├── SCENE_01 ~ SCENE_30          ← 30 个场景
└── Dark Royal Blue Solid        ← 背景层 ⚠️ 你要改这个
```

每个 SCENE 内部图层：
```
P01/P02 Controller            ← 3D 手机位置控制器
Camera                        ← 3D 摄像机
Screen Camera Cut             ← 屏幕追踪
Screen Frame                  ← 边框（通常 disabled）
Screen 01                     ← ⭐ 屏幕内容占位（1170×2532）
Purple / Blue / Black / Silver / Gold  ← 5 种机身配色层 ⚠️ 启用 Purple 禁用其他
Matte / Shadow                ← 遮罩和阴影
Text Holder                   ← 文字占位（部分场景有）⚠️ 文字颜色要改
```

---

## 配色规范（必须严格遵守）

| 元素 | 旧值（深色） | 新值（亮色） | 备注 |
|---|---|---|---|
| 背景 | Dark Royal Blue `#1A0F3A` | **垂直渐变 #F5F3FF → #FFFFFF** | 顶浅紫，底白；用 Solid + Gradient Ramp 效果实现 |
| 手机机身 | Black（默认） | **Purple** | 模板自带的 Purple 层，启用它禁用其他 |
| Text Holder 文字 | 白字 | **深紫 #5B21B6** | 在亮底有足够对比度 |
| Text 副字 / chip | 浅灰 | 中性灰 #6B7280 | 仅在 SCENE_04/15/23-28 有副文字时调 |
| 视频阴影 | `rgba(124,58,237,0.35)` | **保持不变** | 紫光在亮底依然出彩 |
| iPhone 周围光晕（可选） | 无 | **添加：Glow 滤镜，紫色** | 让浅底上的手机更醒目 |

---

## 操作方法（按你的能力选）

### 路径 A：你能写 .jsx + 用户在 AE 里跑（推荐）

写一份自包含的 .jsx 脚本到 `F:\Documents\code\yixiaoguan-v2\.tasks\ae-light-theme.jsx`，用户在 AE 里通过 `File > Scripts > Run Script File...` 一键应用。

骨架参考：

```jsx
// ae-light-theme.jsx
app.beginUndoGroup("Light Theme Conversion");

var proj = app.project;
var mainComp = null;

// 1. 找主合成 PREVIEW COMPS
for (var i = 1; i <= proj.numItems; i++) {
  if (proj.item(i).name.indexOf("PREVIEW") > -1) {
    mainComp = proj.item(i);
    break;
  }
}
if (!mainComp) { alert("Main comp not found"); }

// 2. 找 Dark Royal Blue Solid 改为浅紫
for (var j = 1; j <= mainComp.numLayers; j++) {
  var layer = mainComp.layer(j);
  if (layer.name.indexOf("Dark Royal Blue") > -1 || layer.name.indexOf("Royal Blue") > -1) {
    var solid = layer.source;
    solid.mainSource.color = [245/255, 243/255, 255/255]; // #F5F3FF
    layer.name = "Light Lavender Solid";

    // 加 Gradient Ramp 效果（顶浅紫，底白）
    var ramp = layer.Effects.addProperty("ADBE Ramp");
    ramp.property("Start of Ramp").setValue([1920, 0]);   // 顶部
    ramp.property("End of Ramp").setValue([1920, 2160]);  // 底部
    ramp.property("Start Color").setValue([245/255, 243/255, 255/255, 1]); // #F5F3FF
    ramp.property("End Color").setValue([1, 1, 1, 1]);    // #FFFFFF
    ramp.property("Ramp Shape").setValue(1); // Linear
  }
}

// 3. 在每个 SCENE 内启用 Purple 层禁用其他
// （需要知道精确层名，建议先 inspect 一个 SCENE 用 alert 打印图层名）

// 4. Text Holder 文字颜色改深紫
// （需要遍历 Text 图层 → text.sourceText.value.fillColor）

app.endUndoGroup();
alert("Light theme applied. Check render preview.");
```

**关键：你必须先用 AE MCP（在 `F:\Documents\code\after-effects-mcp\`）或人工探查精确图层名 + 索引**，否则脚本可能找不到对应层。

如果 AE MCP Bridge 可用，调用 `getLayerInfo` 拿到所有层的真实名字，再写 .jsx 才稳。

### 路径 B：你能直接调用 AE MCP

如果 `mcp0_run-script` 或类似工具可用：
1. 先调 `getProjectInfo` + `listCompositions` 看主合成 ID
2. 调 `getLayerInfo` 拿主合成所有层
3. 用 `applyEffect` / 修改 solid color 操作背景层
4. 用 `setLayerKeyframe` / 表达式动画
5. 用 `renderFrame` 测试单帧效果

### 路径 C：你只能写文档

写一份完整的 markdown 操作指南到 `.tasks/ae-light-theme-manual-steps.md`，用户跟着一步一步在 AE 里手动改：
1. 进入主合成 PREVIEW COMPS
2. 选中 Dark Royal Blue Solid 层
3. Layer > Solid Settings 改颜色为 #F5F3FF
4. ...

---

## Part A 详细规格：背景色改造

**目标**：把主合成的纯色背景改成浅紫到白的纵向渐变。

**做法**（任选一种）：

**做法 1（推荐）**：保留 Solid 层，加 Gradient Ramp 效果
- 优点：可逆，不改原 AEP 结构
- 步骤：
  1. 找到 Dark Royal Blue Solid 层
  2. 改 Solid Color 为 `#F5F3FF`（任意亮色都行，被效果覆盖）
  3. Effect > Generate > Gradient Ramp
  4. Start Color = `#F5F3FF`（浅紫），End Color = `#FFFFFF`（白）
  5. Start of Ramp = (1920, 0)，End of Ramp = (1920, 2160)，Linear 模式

**做法 2**：直接换 Solid 颜色（无渐变）
- 优点：最简单
- 缺点：纯色会显得"扁"
- 步骤：
  1. 选中 Solid 层
  2. Layer > Solid Settings... > 颜色改 `#F5F3FF`

---

## Part B 详细规格：SCENE 在亮色背景下的视觉评估

剧本现选了 SCENE_01 + SCENE_05 + SCENE_10 + SCENE_13。但这些是基于深色背景挑的，**亮色背景下视觉权重会变**：
- 镜头依赖深色对比度的（手机暗、背景亮）会失去张力
- 高速镜头/复杂构图在亮底可能"晃眼"
- 文字 Text Holder 在亮底要重测可读性

请评估 17 个无 logo SCENE 在亮色背景下的表现，给出报告：

```markdown
## SCENE 亮色背景视觉评估

| SCENE | 时长 | 屏幕数 | 文字区 | 在深色下评分 | **亮色下评分** | 备注 |
|---|---|---|---|---|---|---|
| SCENE_01 | 8s | 1 | 无 | 9/10 | 8/10 | 手机正面特写，亮底依然出彩 |
| SCENE_04 | 8s | 1 | 有 | 7/10 | 6/10 | 文字白字需改深紫 |
| SCENE_05 | 8s | 1 | 无 | 8/10 | **9/10** | 推 |
| ... | ... | ... | ... | ... | ... | ... |

## 亮色下推荐 Top 6

1. **SCENE_05** (8s) — 理由：……
2. ...

## 与剧本现选对比
| 剧本现选 | 亮色下评分 | 建议 |
|---|---|---|
| SCENE_01 | 8/10 | 保持 |
| SCENE_05 | 9/10 | 保持 |
| SCENE_10 | 7/10 | **建议替换为 SCENE_XX**，理由…… |
| SCENE_13 | 8/10 | 保持 |

## 总建议
（一段话总结：是否需要调整剧本，调整哪些）
```

---

## Part C 详细规格：预览渲染

**目标**：让用户看到亮色主题应用后的真实效果。

**屏幕内容占位**：项目里现有以下可用素材：
- 教师端 10 页截图：`F:\Documents\code\yixiaoguan-v2\.tmp\demo-video\out\explore-teacher\`
- 学生端 PoC 录制：`F:\Documents\code\yixiaoguan-v2\.tmp\demo-video\out\demo-trimmed.mp4` 可抽帧

**注意**：UI 还在优化中，所以这次预览**只验证亮色主题 + 镜头节奏 + 配色协调性**，不验证最终 UI 质感。等 UI polish 完成后会重新做一版正式渲染。

**渲染参数**：
- 输出：HD 合成（1920×1080）
- 时长：32-34s（剧本现选的 4 个 SCENE 总长）或 Part B 重选后的 4 个 SCENE 总长
- 帧率：30fps
- 编码：H.264 mp4
- 输出路径：`F:\Documents\code\yixiaoguan-v2\.tasks\preview-light-theme-v1.mp4`

**屏幕内容占位策略（推荐）**：
- SCENE_01 屏幕 → 教师端 dashboard 截图
- SCENE_05 屏幕 → 教师端 knowledge 截图（或学生端抽帧）
- SCENE_10 双屏 → 教师端 analytics + 学生端抽帧
- SCENE_13 双屏 → 教师端 profile + 学生端抽帧

如果配占位太麻烦，**保底用纯灰块 #E5E7EB 占位** 也可以（用户能看出主题效果，只是看不出最终质感）。

---

## 必须输出的 Deliverables

1. ✅ `F:\Documents\code\yixiaoguan-v2\.tasks\ae-light-theme.jsx` — 改造脚本（应用 undo group，可重复运行）
2. ✅ `F:\Documents\code\yixiaoguan-v2\.tasks\ae-light-theme-report.md` — 报告，结构：
   - Part A：背景色改造做了什么
   - Part B：SCENE 亮色评估表 + Top 6 推荐 + 与剧本对比
   - Part C：渲染预览说明（参数、占位策略、文件位置）
3. ✅ `F:\Documents\code\yixiaoguan-v2\.tasks\preview-light-theme-v1.mp4` — 预览视频（如果你能跑 AE/ffmpeg；不能就给用户操作步骤让他自己渲）
4. ✅ `F:\Documents\code\yixiaoguan-v2\.tasks\ae-light-theme-manual-steps.md` — 备用手动操作指南（万一 .jsx 在用户的 AE 版本上跑不动）

---

## 验收硬条件

- ✅ 背景色应用后，主合成首帧截图必须看起来**明显是亮色主题**（不是深色调淡化）
- ✅ Purple 机身 + 浅紫底必须协调，不能机身被背景"吃掉"
- ✅ Text Holder 文字在亮底有≥4.5:1 对比度（用 #5B21B6 或更深可达标）
- ✅ Part B 报告中至少给 1 个具体的 SCENE 替换建议（即使最终是"全部保持"，也要论证）
- ✅ 预览 mp4 时长 30-35s，无明显 glitch
- ✅ 所有 deliverables 文件实际存在于 `.tasks/` 目录

---

## 风险与回滚

- **AE 版本兼容**：模板是 CS6 时代的，用户可能用 CC 2024。.jsx 脚本要避免使用 CC 独占的 API（如某些新表达式语法）
- **图层名差异**：模板可能被本地修改过，"Dark Royal Blue Solid" 名字可能不完全一致 → 用模糊匹配（indexOf("Royal Blue") 或 indexOf("Dark") 多重 fallback）
- **回滚**：所有改动包在 `app.beginUndoGroup` 里，AE 里 Ctrl+Z 可一键撤销

---

## 完成后下一步

用户拿到 preview-light-theme-v1.mp4 → 评估 → 决定：
- 配色满意 → 锁亮色主题 v1，等 UI polish 完成后用真实截图重渲正式版
- 配色不满意 → 调具体参数（比如换更深的紫或更浅的渐变），重渲 v2

把 Part B 的报告 + 预览 mp4 一起回给用户，他会人工挑最终方案。
