/**
 * ae-render-preview.jsx
 * 渲染 SCENE_01 ~ SCENE_13 区间为 H.264 MP4 预览
 *
 * 用法: AE > File > Scripts > Run Script File...
 */

var OUTPUT_PATH = "F:\\Documents\\code\\yixiaoguan-v2\\.tasks\\preview-light-theme-v1.avi";

// 找 PREVIEW COMPS
var proj = app.project;
var mainComp = null;
for (var i = 1; i <= proj.numItems; i++) {
    if (proj.item(i) instanceof CompItem && proj.item(i).name.indexOf("PREVIEW") > -1) {
        mainComp = proj.item(i);
        break;
    }
}

if (!mainComp) {
    alert("找不到 PREVIEW COMPS 合成");
} else {
    // SCENE_01 inPoint = 0s, SCENE_13 outPoint ≈ 108.43s
    // 只渲染前 108.43s（SCENE_01 ~ SCENE_13）
    var startTime = 0;
    var endTime = 108.43;

    // 设置 Work Area
    mainComp.workAreaStart = startTime;
    mainComp.workAreaDuration = endTime - startTime;

    // 添加到渲染队列
    var rqi = app.project.renderQueue.items.add(mainComp);

    // 设置输出模块 — 用 AVI 格式（AE 原生支持，不依赖 AME）
    // 用户拿到 .avi 后可用 ffmpeg 转 mp4
    var om = rqi.outputModule(1);
    
    // 尝试用现有模板，回退到默认
    try {
        om.applyTemplate("Lossless");
    } catch (e) {
        // 中文 AE 模板名可能不同，用默认即可
    }

    om.file = new File(OUTPUT_PATH);

    alert("✅ 已添加到渲染队列\n\n" +
          "合成: " + mainComp.name + "\n" +
          "区间: 0s ~ " + endTime.toFixed(1) + "s (SCENE_01 ~ SCENE_13)\n" +
          "输出: " + OUTPUT_PATH + "\n\n" +
          "请在渲染队列中确认设置，然后点 Render。\n" +
          "渲染完成后用 ffmpeg 转 mp4:\n" +
          "ffmpeg -i preview-light-theme-v1.avi -c:v libx264 -crf 18 -preset fast preview-light-theme-v1.mp4");
}
