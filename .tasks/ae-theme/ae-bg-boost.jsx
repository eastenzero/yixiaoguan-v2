/**
 * ae-bg-boost.jsx
 * 加深背景渐变 + 禁用暗色曲线
 *
 * 用法: AE > File > Scripts > Run Script File...
 */

app.beginUndoGroup("BG Boost — 加深紫色渐变");

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
    var bgLayer = mainComp.layer(mainComp.numLayers);
    var log = [];

    // 1. 禁用 fx3 曲线 — 它是给深色调的，会把浅色压白
    try {
        var fx3 = bgLayer.Effects.property(3);
        if (fx3 && fx3.matchName === "ADBE CurvesCustom") {
            fx3.enabled = false;
            log.push("✅ fx3 曲线已禁用（原深色调曲线）");
        }
    } catch (e) {
        log.push("⚠️ 禁用曲线失败: " + e.toString());
    }

    // 2. fx1 四色渐变 — 用更饱和的紫色
    //    violet-300 ~ violet-400 范围，让渐变肉眼可见
    var FX1_COLORS = {
        "ADBE 4ColorGradient-0002": [0.769, 0.710, 0.988, 1],  // #C4B5FC  左上 violet-300
        "ADBE 4ColorGradient-0004": [0.867, 0.839, 0.992, 1],  // #DDD6FD  右上 violet-200
        "ADBE 4ColorGradient-0006": [0.929, 0.914, 1.0,   1],  // #EDE9FF  左下 violet-100
        "ADBE 4ColorGradient-0008": [0.961, 0.953, 1.0,   1]   // #F5F3FF  右下 近白
    };

    // 3. fx2 第二层 — 辅助色，稍浅
    var FX2_COLORS = {
        "ADBE 4ColorGradient-0002": [0.839, 0.792, 0.992, 1],  // #D6CAFD  左上
        "ADBE 4ColorGradient-0004": [0.898, 0.867, 1.0,   1],  // #E5DDFF  右上
        "ADBE 4ColorGradient-0006": [0.949, 0.933, 1.0,   1],  // #F2EEFF  左下
        "ADBE 4ColorGradient-0008": [0.976, 0.969, 1.0,   1]   // #F9F7FF  右下
    };

    function setColors(layer, fxIdx, colorMap, label) {
        try {
            var fx = layer.Effects.property(fxIdx);
            if (fx && fx.matchName === "ADBE 4ColorGradient") {
                for (var p = 1; p <= fx.numProperties; p++) {
                    var prop = fx.property(p);
                    if (colorMap[prop.matchName]) {
                        prop.setValue(colorMap[prop.matchName]);
                    }
                }
                log.push("✅ " + label + " 颜色已更新");
            }
        } catch (e) {
            log.push("⚠️ " + label + ": " + e.toString());
        }
    }

    setColors(bgLayer, 1, FX1_COLORS, "fx1 主渐变");
    setColors(bgLayer, 2, FX2_COLORS, "fx2 辅助渐变");

    log.push("");
    log.push("配色方案:");
    log.push("  左上 #C4B5FC (violet-300) → 右上 #DDD6FD (violet-200)");
    log.push("  左下 #EDE9FF (violet-100) → 右下 #F5F3FF (近白)");
    log.push("");
    log.push("如果觉得太紫，Ctrl+Z 撤销后告诉 Cascade 调色");

    alert("═══ BG Boost ═══\n\n" + log.join("\n"));
}

app.endUndoGroup();
