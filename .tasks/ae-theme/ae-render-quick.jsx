/**
 * ae-render-quick.jsx
 * 快速渲染 SCENE_01 + SCENE_05（共 16s）
 */

var OUTPUT = "F:\\Documents\\code\\yixiaoguan-v2\\.tasks\\preview-light-v2.avi";

var proj = app.project;
var mainComp = null;
for (var i = 1; i <= proj.numItems; i++) {
    if (proj.item(i) instanceof CompItem && proj.item(i).name === "PREVIEW COMPS") {
        mainComp = proj.item(i);
        break;
    }
}

if (!mainComp) {
    alert("找不到 PREVIEW COMPS");
} else {
    // SCENE_01: 0s ~ 8.03s
    // SCENE_05: 32.13s ~ 40.17s
    // 渲染 0s ~ 40.17s 覆盖这两个（中间 SCENE_02/03/04 也会渲，但能看到两个目标场景效果）
    mainComp.workAreaStart = 0;
    mainComp.workAreaDuration = 40.17;

    var rqi = proj.renderQueue.items.add(mainComp);
    var om = rqi.outputModule(1);
    try { om.applyTemplate("Lossless"); } catch (e) {}
    om.file = new File(OUTPUT);

    alert("✅ 已添加到渲染队列\n\n" +
          "区间: 0s ~ 40s (SCENE_01 ~ SCENE_05)\n" +
          "输出: " + OUTPUT + "\n\n" +
          "去渲染队列点 Render");
}
