# AE 亮色主题改造 — 手动操作指南

> 备用方案：如 `.tasks/ae-light-theme.jsx` 脚本在你的 AE 版本上报错，按本文档逐步手动操作。
> 所有操作前请 **另存一份 AEP**（File > Save As），以便回滚。

---

## 前置：打开项目

1. 打开 AE，加载模板 `.aep`：
   ```
   E:\BaiduNetdiskDownload\AE模板-手机APP展示宣传片头开场动画40526693\
   App Promo Phone 14 Pro Mockup Pack\
   Phone 14 Pro App Presentation By MotionFox\
   Phone 14 Pro_App Presentation_CS6.aep
   ```
2. 在项目面板中找到 **PREVIEW COMPS** 主合成（3840×2160），双击打开

---

## Step 1：改背景层颜色 + 渐变

### 1a. 找到背景 Solid
- 在 PREVIEW COMPS 时间轴底部找到 **Dark Royal Blue Solid** 层（通常是最底层）

### 1b. 改 Solid 颜色
1. 选中该层
2. `Layer > Solid Settings...`（或右键 > Solid Settings）
3. 点颜色色块，输入 **#F5F3FF**
4. OK

### 1c. 添加 Gradient Ramp
1. 选中同一层
2. `Effect > Generate > Gradient Ramp`
3. 在效果控制面板中设置：

| 参数 | 值 |
|---|---|
| Start of Ramp | (1920, 0) — 即画面顶部中心 |
| End of Ramp | (1920, 2160) — 即画面底部中心 |
| Start Color | **#F5F3FF** (浅紫) |
| End Color | **#FFFFFF** (白) |
| Ramp Shape | **Linear Ramp** |

> 💡 如果是 HD 合成（1920×1080），坐标改为 (960, 0) → (960, 1080)

### 1d. 重命名（可选）
- 双击层名，改为 `Light Lavender Gradient`

---

## Step 2：切换手机机身为 Purple

需要对 **17 个目标 SCENE** 逐个操作（见列表）。

### 目标 SCENE 列表
```
SCENE_01, SCENE_04, SCENE_05, SCENE_06, SCENE_08, SCENE_09,
SCENE_10, SCENE_13, SCENE_15, SCENE_23, SCENE_24, SCENE_25,
SCENE_26, SCENE_27, SCENE_28, SCENE_29, SCENE_30
```

### 操作方法（每个 SCENE 重复一次）

1. 在 PREVIEW COMPS 时间轴中找到对应 SCENE（如 `SCENE_01`）
2. 双击进入子合成
3. 找到以下层（通常紧挨在一起）：
   - `Purple` — ✅ 确保 **眼睛图标开启**（可见）
   - `Blue` — ❌ 关闭眼睛
   - `Black` — ❌ 关闭眼睛
   - `Silver` — ❌ 关闭眼睛
   - `Gold` — ❌ 关闭眼睛
4. 返回 PREVIEW COMPS（点合成标签或 Tab 键）

> ⏱ 技巧：如果模板有 **Device Color Select** 全局控制层（PREVIEW COMPS 顶层），可能可以一键切换全部 SCENE 的机身。先试试选中它看是否有下拉选项。

---

## Step 3：改 Text Holder 文字颜色

仅限以下有文字区的 SCENE：
```
SCENE_04, SCENE_15, SCENE_23, SCENE_24, SCENE_25, SCENE_26, SCENE_27, SCENE_28, SCENE_30
```

### 操作方法

1. 双击进入目标 SCENE 子合成
2. 找到 `Text Holder` 层（可能是文字图层或子合成）
3. **如果是文字图层**：
   - 选中文字图层
   - 按 `Ctrl+A` 全选文字
   - 在字符面板（Character Panel）中修改 **Fill Color** 为 **#5B21B6**
4. **如果是子合成**（名字类似 `Text Holder`）：
   - 双击进入子合成
   - 找到文字图层，按上面方法修改
5. 如果有第二个副文字（颜色较浅的说明文字），改为 **#6B7280**

---

## Step 4：验证效果

### 快速检查
1. 回到 PREVIEW COMPS 主合成
2. 按 `Home` 键回到第 0 帧
3. 按空格预览前 40 秒
4. 检查清单：
   - [ ] 背景是浅紫到白的渐变（不是深蓝）
   - [ ] 手机机身是紫色（不是黑色）
   - [ ] 文字清晰可读（深紫色，不是白色）
   - [ ] 手机没有被背景"吃掉"（阴影层仍在工作）

### 单帧导出检查
1. 将时间指针移到 SCENE_01 中间帧（约 0:04）
2. `Composition > Save Frame As > File...`
3. 保存为 PNG，用图片查看器确认颜色

---

## Step 5：渲染预览 MP4

### 设置 Work Area（只渲染选中 SCENE）
1. 在 PREVIEW COMPS 时间轴上，按 `B` 设置工作区起点（SCENE_01 开始处）
2. 移到 SCENE_13 结束处，按 `N` 设置工作区终点
3. 如果不确定各 SCENE 位置，可以逐个点击 SCENE 层查看其 in/out point

### 添加到渲染队列
1. `Composition > Add to Render Queue`
2. **Render Settings**: Best Settings
3. **Output Module**:
   - Format: **H.264**（或 QuickTime → H.264 codec）
   - Channels: RGB
   - Audio: Off
4. **Output To**: `F:\Documents\code\yixiaoguan-v2\.tasks\preview-light-theme-v1.mp4`
5. 点 **Render**

> 如果 AE 没有 H.264 直接输出选项，用 Adobe Media Encoder：
> `Composition > Add to Adobe Media Encoder Queue` → 选 H.264 preset → Render

### 预期输出
- 分辨率：取决于用哪个合成（HD = 1920×1080，4K = 3840×2160）
- 时长：约 30-35s（4 个 SCENE 总长）
- 帧率：30fps

---

## Step 6（可选）：添加紫色光晕

如果觉得手机在浅底上不够突出：

1. 选中某个 SCENE 的手机 Purple 层（或 Shadow 层）
2. `Effect > Stylize > Glow`
3. 设置：
   - Glow Threshold: 60%
   - Glow Radius: 30
   - Glow Intensity: 0.5
   - Glow Colors: A & B Colors，A = #7C3AED（主紫色），B = #F5F3FF

> ⚠️ 光晕效果请先在一个 SCENE 上试，满意后再复制到其他 SCENE。

---

## 回滚

如果效果不满意：
- **脚本执行的改动**：`Edit > Undo Light Theme Conversion`（Ctrl+Z）
- **手动改动**：多次 Ctrl+Z，或直接关闭不保存，重新打开原 AEP

---

## 配色速查卡

| 元素 | 色值 | 用途 |
|---|---|---|
| #F5F3FF | 浅紫 | 背景渐变顶部 |
| #FFFFFF | 白 | 背景渐变底部 |
| #5B21B6 | 深紫 | Text Holder 主文字 |
| #6B7280 | 中性灰 | 副文字/说明 |
| #7C3AED | 品牌紫 | 光晕颜色（可选） |
| Purple | — | 手机机身配色层名 |
