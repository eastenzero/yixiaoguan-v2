/**
 * ae-light-theme-fix.jsx
 * 修复两个问题：
 *   1. Device Color Select → Purple checkbox 开启（修复手机边框丢失）
 *   2. 背景四色渐变改亮色（保留流动质感，不再纯白平坦）
 *
 * 用法: AE > File > Scripts > Run Script File...
 * 回滚: Ctrl+Z
 */

app.beginUndoGroup("Light Theme Fix v2");

var proj = app.project;
var log = [];

// ─── 找 PREVIEW COMPS ──────────────────────────────────────
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

    // ═══════════════════════════════════════════════════════
    // FIX 1: Device Color Select → Purple = 1, 其他 = 0
    // ═══════════════════════════════════════════════════════

    var dcsLayer = mainComp.layer(1); // Device Color Select 是第 1 层
    if (dcsLayer && dcsLayer.name.indexOf("Device Color") > -1) {
        var colorNames = ["Gold", "Silver", "Black", "Blue", "Purple"];
        for (var c = 1; c <= dcsLayer.Effects.numProperties; c++) {
            var fx = dcsLayer.Effects.property(c);
            if (fx.matchName === "ADBE Checkbox Control") {
                // checkbox 值在 property(1)，matchName = "ADBE Checkbox Control-0001"
                var checkProp = fx.property(1);
                if (fx.name === "Purple") {
                    checkProp.setValue(1);
                    log.push("✅ Purple checkbox = 1");
                } else {
                    checkProp.setValue(0);
                    log.push("  " + fx.name + " checkbox = 0");
                }
            }
        }
    } else {
        log.push("⚠️ Device Color Select 层未在第 1 层找到");
    }

    // ═══════════════════════════════════════════════════════
    // FIX 1b: 恢复 SCENE 内被误改的 enabled 状态
    //  → 全部 Purple/Blue/Black/Silver/Gold 层恢复 enabled=true
    //  → 让 Device Color Select 的表达式控制 opacity
    // ═══════════════════════════════════════════════════════

    var bodyNames = ["Purple", "Blue", "Black", "Silver", "Gold"];
    var TARGET_SCENES = [1,4,5,6,8,9,10,13,15,23,24,25,26,27,28,29,30];
    var restoreCount = 0;

    for (var s = 0; s < TARGET_SCENES.length; s++) {
        var sn = TARGET_SCENES[s];
        var padded = sn < 10 ? "0" + sn : "" + sn;
        var sceneName = "SCENE_" + padded;

        // 找 SCENE 子合成
        var sceneComp = null;
        for (var j = 1; j <= mainComp.numLayers; j++) {
            if (mainComp.layer(j).name === sceneName && mainComp.layer(j).source instanceof CompItem) {
                sceneComp = mainComp.layer(j).source;
                break;
            }
        }
        if (!sceneComp) continue;

        for (var k = 1; k <= sceneComp.numLayers; k++) {
            var lyr = sceneComp.layer(k);
            for (var b = 0; b < bodyNames.length; b++) {
                if (lyr.name === bodyNames[b]) {
                    if (!lyr.enabled) {
                        lyr.enabled = true;
                        restoreCount++;
                    }
                }
            }
        }
    }
    log.push("✅ 恢复 " + restoreCount + " 个机身层 enabled=true（交由表达式控制）");

    // ═══════════════════════════════════════════════════════
    // FIX 2: 背景四色渐变改亮色
    // ═══════════════════════════════════════════════════════

    var bgLayer = mainComp.layer(mainComp.numLayers);

    // 2a. 移除我之前加的 Gradient Ramp (fx4)
    try {
        for (var fx = bgLayer.Effects.numProperties; fx >= 1; fx--) {
            if (bgLayer.Effects.property(fx).matchName === "ADBE Ramp") {
                bgLayer.Effects.property(fx).remove();
                log.push("✅ 移除 Gradient Ramp (梯度渐变)");
            }
        }
    } catch (e) {
        log.push("⚠️ 移除 Gradient Ramp 失败: " + e.toString());
    }

    // 2b. 修改 fx1 四色渐变的 4 个角颜色 → 亮色紫白系
    //     原值: 深蓝黑 (#22353C, #232C2D, #020609, #121615)
    //     新值: 浅紫白流动渐变
    //
    //     matchName 对应:
    //       -0002 = 颜色1 (左上)    -0004 = 颜色2 (右上)
    //       -0006 = 颜色3 (左下)    -0008 = 颜色4 (右下)

    var LIGHT_COLORS_FX1 = {
        "ADBE 4ColorGradient-0002": [0.867, 0.839, 0.992, 1],  // #DDD6FD  左上 violet-200
        "ADBE 4ColorGradient-0004": [0.929, 0.914, 1.0,   1],  // #EDE9FF  右上 violet-100
        "ADBE 4ColorGradient-0006": [0.961, 0.953, 1.0,   1],  // #F5F3FF  左下 浅紫
        "ADBE 4ColorGradient-0008": [1.0,   1.0,   1.0,   1]   // #FFFFFF  右下 白
    };

    // fx2 第二层四色渐变 — 更淡的辅助层
    var LIGHT_COLORS_FX2 = {
        "ADBE 4ColorGradient-0002": [0.914, 0.898, 1.0,   1],  // #E9E5FF  左上
        "ADBE 4ColorGradient-0004": [0.949, 0.933, 1.0,   1],  // #F2EEFF  右上
        "ADBE 4ColorGradient-0006": [0.976, 0.969, 1.0,   1],  // #F9F7FF  左下
        "ADBE 4ColorGradient-0008": [0.988, 0.984, 1.0,   1]   // #FCFBFF  右下 近白
    };

    function recolorFourColorGradient(layer, fxIndex, colorMap, label) {
        try {
            var fx = layer.Effects.property(fxIndex);
            if (fx && fx.matchName === "ADBE 4ColorGradient") {
                for (var p = 1; p <= fx.numProperties; p++) {
                    var prop = fx.property(p);
                    if (colorMap[prop.matchName]) {
                        prop.setValue(colorMap[prop.matchName]);
                    }
                }
                log.push("✅ " + label + " 四色渐变颜色已更新");
            } else {
                log.push("⚠️ " + label + " 位置不是四色渐变");
            }
        } catch (e) {
            log.push("⚠️ " + label + " 修改失败: " + e.toString());
        }
    }

    recolorFourColorGradient(bgLayer, 1, LIGHT_COLORS_FX1, "fx1");
    recolorFourColorGradient(bgLayer, 2, LIGHT_COLORS_FX2, "fx2");

    // 2c. 曲线 (fx3) — 暂不修改，保留原来的曲线调整
    log.push("ℹ️ fx3 曲线保持不变（如需提亮可手动调）");

    // 2d. Solid 底色保持 #F5F3FF
    log.push("ℹ️ Solid 底色保持 #F5F3FF");
}

app.endUndoGroup();

var report = "═══ Light Theme Fix v2 ═══\n\n" + log.join("\n") + "\n\n═══ 完成 ═══\nCtrl+Z 可撤销";
alert(report);
