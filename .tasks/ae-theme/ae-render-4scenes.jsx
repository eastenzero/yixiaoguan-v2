/**
 * ae-render-4scenes.jsx
 * 精确渲染 SCENE_01 / 05 / 10 / 13 四段，跳过有 logo 的中间 SCENE
 * 输出 4 个 AVI 文件（可用 ffmpeg 合并为一个 mp4）
 *
 * 用法: AE > File > Scripts > Run Script File...
 */

var OUTPUT_DIR = "F:\\Documents\\code\\yixiaoguan-v2\\.tasks\\ae-theme\\render-segments";
var TARGET_SCENES = ["SCENE_01", "SCENE_05", "SCENE_10", "SCENE_13"];

var proj = app.project;

// 找 PREVIEW COMPS
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
    // 找每个目标 SCENE 的 inPoint / outPoint
    var segments = [];
    for (var s = 0; s < TARGET_SCENES.length; s++) {
        var sceneName = TARGET_SCENES[s];
        for (var j = 1; j <= mainComp.numLayers; j++) {
            if (mainComp.layer(j).name === sceneName) {
                var lyr = mainComp.layer(j);
                segments.push({
                    name: sceneName,
                    inPoint: lyr.inPoint,
                    outPoint: lyr.outPoint,
                    duration: lyr.outPoint - lyr.inPoint
                });
                break;
            }
        }
    }

    if (segments.length === 0) {
        alert("未找到任何目标 SCENE 层");
    } else {
        // 创建输出目录
        var outFolder = new Folder(OUTPUT_DIR);
        if (!outFolder.exists) outFolder.create();

        var report = "═══ 4-Scene 精确渲染 ═══\n\n";
        report += "检测到 " + segments.length + " 个 SCENE 时间段:\n\n";

        for (var k = 0; k < segments.length; k++) {
            var seg = segments[k];
            report += "  " + seg.name + ": " +
                      seg.inPoint.toFixed(2) + "s → " +
                      seg.outPoint.toFixed(2) + "s (" +
                      seg.duration.toFixed(2) + "s)\n";
        }

        // 添加到渲染队列
        report += "\n正在添加到渲染队列...\n\n";

        for (var m = 0; m < segments.length; m++) {
            var seg2 = segments[m];
            var rqi = proj.renderQueue.items.add(mainComp);

            // 设置时间范围
            rqi.timeSpanStart = seg2.inPoint;
            rqi.timeSpanDuration = seg2.duration;

            // 设置输出
            var om = rqi.outputModule(1);
            try { om.applyTemplate("Lossless"); } catch (e) {}
            var outFile = OUTPUT_DIR + "\\" + seg2.name + ".avi";
            om.file = new File(outFile);

            report += "  ✅ " + seg2.name + " → " + seg2.name + ".avi\n";
        }

        report += "\n═══ 操作步骤 ═══\n";
        report += "1. 去渲染队列 (Ctrl+Alt+0)\n";
        report += "2. 点 Render 渲染全部 4 段\n";
        report += "3. 渲完后用 ffmpeg 合并:\n\n";
        report += "ffmpeg -i SCENE_01.avi -i SCENE_05.avi -i SCENE_10.avi -i SCENE_13.avi ";
        report += "-filter_complex \"[0:v][1:v][2:v][3:v]concat=n=4:v=1[v]\" -map \"[v]\" ";
        report += "-c:v libx264 -crf 18 -preset fast ";
        report += "\"F:\\Documents\\code\\yixiaoguan-v2\\.tasks\\ae-theme\\preview-4scenes.mp4\"";

        alert(report);
    }
}
