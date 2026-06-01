/**
 * ae-light-theme.jsx
 * 医小管演示视频 — AE 模板亮色主题改造
 *
 * 模板: App Promo Phone 14 Pro Mockup Pack (Videohive 40526693)
 * 目标: 深皇家蓝 → 浅紫渐变白亮色主题
 *
 * 用法: AE > File > Scripts > Run Script File... > 选本文件
 * 回滚: Ctrl+Z（整体在一个 Undo Group 内）
 *
 * 兼容性: CS6 ~ CC 2024（仅使用稳定 ExtendScript API）
 */

// ============================================================
// 配色常量
// ============================================================
var COLOR_LAVENDER = [245 / 255, 243 / 255, 255 / 255];  // #F5F3FF
var COLOR_WHITE = [1, 1, 1];                     // #FFFFFF
var COLOR_DEEP_PURPLE = [91 / 255, 33 / 255, 182 / 255];    // #5B21B6
var COLOR_NEUTRAL_GRAY = [107 / 255, 114 / 255, 128 / 255]; // #6B7280

// 机身配色层名（模板自带 5 种）
var BODY_ENABLE = "Purple";
var BODY_DISABLE = ["Blue", "Black", "Silver", "Gold"];

// 需要处理的 17 个无 logo SCENE
var TARGET_SCENES = [1, 4, 5, 6, 8, 9, 10, 13, 15, 23, 24, 25, 26, 27, 28, 29, 30];

// ============================================================
// 辅助函数
// ============================================================

/**
 * 模糊匹配层名：名称中包含 keyword 即为命中
 */
function layerNameContains(layer, keyword) {
    return layer.name.toLowerCase().indexOf(keyword.toLowerCase()) > -1;
}

/**
 * 在合成中按关键词找层（返回第一个匹配）
 */
function findLayerByKeyword(comp, keyword) {
    for (var i = 1; i <= comp.numLayers; i++) {
        if (layerNameContains(comp.layer(i), keyword)) {
            return comp.layer(i);
        }
    }
    return null;
}

/**
 * 在合成中按关键词找所有匹配层
 */
function findLayersByKeyword(comp, keyword) {
    var results = [];
    for (var i = 1; i <= comp.numLayers; i++) {
        if (layerNameContains(comp.layer(i), keyword)) {
            results.push(comp.layer(i));
        }
    }
    return results;
}

/**
 * 在项目中按名称关键词找合成
 */
function findCompByKeyword(keyword) {
    for (var i = 1; i <= app.project.numItems; i++) {
        var item = app.project.item(i);
        if (item instanceof CompItem && item.name.toLowerCase().indexOf(keyword.toLowerCase()) > -1) {
            return item;
        }
    }
    return null;
}

/**
 * 获取 SCENE_XX 子合成（在主合成中按名称查找其 source）
 */
function getSceneComp(mainComp, sceneNum) {
    var padded = sceneNum < 10 ? "0" + sceneNum : "" + sceneNum;
    var layerName = "SCENE_" + padded;
    for (var i = 1; i <= mainComp.numLayers; i++) {
        var lyr = mainComp.layer(i);
        if (lyr.name === layerName && lyr.source instanceof CompItem) {
            return lyr.source;
        }
    }
    return null;
}

/**
 * 递归查找 Text 图层并修改 fillColor
 */
function recolorTextLayers(comp, newColor, depth) {
    if (depth === undefined) depth = 0;
    if (depth > 3) return; // 防止无限递归

    for (var i = 1; i <= comp.numLayers; i++) {
        var lyr = comp.layer(i);

        // 直接是文字图层
        if (lyr instanceof TextLayer) {
            try {
                var textProp = lyr.property("ADBE Text Properties").property("ADBE Text Document");
                var textDoc = textProp.value;
                textDoc.fillColor = newColor;
                textProp.setValue(textDoc);
            } catch (e) {
                // 某些锁定/表达式驱动的文字层可能改不了，跳过
            }
        }

        // 如果是预合成，递归进去
        if (lyr.source instanceof CompItem) {
            recolorTextLayers(lyr.source, newColor, depth + 1);
        }
    }
}

/**
 * 在 SCENE 子合成中切换机身配色
 */
function switchBodyColor(sceneComp) {
    for (var i = 1; i <= sceneComp.numLayers; i++) {
        var lyr = sceneComp.layer(i);
        var name = lyr.name;

        // 启用 Purple
        if (name === BODY_ENABLE || name.toLowerCase().indexOf("purple") > -1) {
            lyr.enabled = true;
        }

        // 禁用其他配色
        for (var d = 0; d < BODY_DISABLE.length; d++) {
            if (name === BODY_DISABLE[d] || name.toLowerCase().indexOf(BODY_DISABLE[d].toLowerCase()) > -1) {
                // 仅在当前启用的情况下禁用，避免误伤同名其他层
                if (lyr.enabled) {
                    lyr.enabled = false;
                }
            }
        }
    }
}

// ============================================================
// 主流程
// ============================================================

app.beginUndoGroup("Light Theme Conversion — yixiaoguan v3.1");

var log = [];

// ─── Step 1: 找主合成 ────────────────────────────────────
var mainComp = findCompByKeyword("PREVIEW");
if (!mainComp) {
    // 回退：试找 "4K" 或 "HD"
    mainComp = findCompByKeyword("4K");
}
if (!mainComp) {
    mainComp = findCompByKeyword("HD");
}
if (!mainComp) {
    alert("❌ 找不到主合成（搜索关键词: PREVIEW / 4K / HD）。\n请确认已打开正确的 AEP 文件。");
} else {
    log.push("✅ 主合成: " + mainComp.name + " (" + mainComp.width + "×" + mainComp.height + ")");

    // ─── Step 2: 改背景层 ─────────────────────────────────
    var bgLayer = findLayerByKeyword(mainComp, "Royal Blue");
    if (!bgLayer) bgLayer = findLayerByKeyword(mainComp, "Dark");
    if (!bgLayer) {
        // 最后手段：找最底层的 Solid
        var bottomLayer = mainComp.layer(mainComp.numLayers);
        if (bottomLayer.source instanceof FootageItem && bottomLayer.source.mainSource instanceof SolidSource) {
            bgLayer = bottomLayer;
        }
    }

    if (bgLayer) {
        // 2a. 修改 Solid 颜色
        try {
            bgLayer.source.mainSource.color = COLOR_LAVENDER;
        } catch (e) {
            log.push("⚠️ 无法直接改 Solid 颜色（可能是 Footage），跳过 mainSource.color");
        }

        // 2b. 添加 Gradient Ramp 效果
        var existingRamp = null;
        try {
            for (var fx = 1; fx <= bgLayer.Effects.numProperties; fx++) {
                if (bgLayer.Effects.property(fx).matchName === "ADBE Ramp") {
                    existingRamp = bgLayer.Effects.property(fx);
                    break;
                }
            }
        } catch (e) { }

        var ramp = null;
        if (existingRamp) {
            ramp = existingRamp;
            log.push("ℹ️ 背景层已有 Gradient Ramp，复用并更新参数");
        } else {
            try {
                ramp = bgLayer.Effects.addProperty("ADBE Ramp");
                log.push("✅ 背景层添加 Gradient Ramp 效果");
            } catch (e) {
                log.push("⚠️ addProperty('ADBE Ramp') 失败: " + e.toString());
            }
        }

        if (ramp) {
            // 使用 property index（1-based）而非 display name，避免中文 AE locale 问题
            // Gradient Ramp 属性顺序：
            //   (1) Start of Ramp  (2) Start Color
            //   (3) End of Ramp    (4) End Color
            //   (5) Ramp Shape     (6) Ramp Scatter  (7) Blend With Original
            var compW = mainComp.width;
            var compH = mainComp.height;
            ramp.property(1).setValue([compW / 2, 0]);          // Start of Ramp
            ramp.property(3).setValue([compW / 2, compH]);      // End of Ramp
            ramp.property(2).setValue(COLOR_LAVENDER);           // Start Color
            ramp.property(4).setValue(COLOR_WHITE);              // End Color
            ramp.property(5).setValue(1);                        // Ramp Shape = Linear

            // 重命名
            bgLayer.name = "Light Lavender Gradient";
            log.push("✅ 背景: #F5F3FF → #FFFFFF 垂直线性渐变 (comp " + compW + "×" + compH + ")");
        } else {
            log.push("⚠️ Gradient Ramp 效果添加失败，请手动操作：Effect > Generate > Gradient Ramp");
        }
    } else {
        log.push("⚠️ 未找到背景 Solid 层，请手动修改");
    }

    // ─── Step 3: 遍历目标 SCENE，切机身 + 改文字 ──────────
    var sceneCount = 0;
    var textCount = 0;

    for (var s = 0; s < TARGET_SCENES.length; s++) {
        var sceneNum = TARGET_SCENES[s];
        var sceneComp = getSceneComp(mainComp, sceneNum);

        if (!sceneComp) {
            log.push("⚠️ SCENE_" + (sceneNum < 10 ? "0" + sceneNum : sceneNum) + " 子合成未找到");
            continue;
        }

        // 3a. 切换机身颜色
        switchBodyColor(sceneComp);
        sceneCount++;

        // 3b. 改 Text Holder 文字颜色
        // Text Holder 可能是直接文字层，也可能嵌套在 Text Holder 子合成中
        var textHolders = findLayersByKeyword(sceneComp, "Text");
        for (var t = 0; t < textHolders.length; t++) {
            var th = textHolders[t];
            if (th instanceof TextLayer) {
                try {
                    var tdoc = th.property("ADBE Text Properties").property("ADBE Text Document").value;
                    tdoc.fillColor = COLOR_DEEP_PURPLE;
                    th.property("ADBE Text Properties").property("ADBE Text Document").setValue(tdoc);
                    textCount++;
                } catch (e) { }
            } else if (th.source instanceof CompItem) {
                recolorTextLayers(th.source, COLOR_DEEP_PURPLE);
                textCount++;
            }
        }
    }

    log.push("✅ 机身切换 Purple: " + sceneCount + " / " + TARGET_SCENES.length + " SCENE");
    log.push("✅ 文字改色 #5B21B6: " + textCount + " 处");

    // ─── Step 4: Device Color Select 全局控制器 ───────────
    var deviceSelect = findLayerByKeyword(mainComp, "Device Color");
    if (deviceSelect) {
        // 这个层通常是一个引导层或控制层，尝试设置
        log.push("ℹ️ 检测到 Device Color Select 层（" + deviceSelect.name + "），请手动确认全局配色已设为 Purple");
    }

    // ─── Step 5: 可选 — 给手机添加紫色光晕 ──────────────
    // 光晕效果需要谨慎，仅在有 Shadow 层的 SCENE 上添加
    // 这里不自动加，留给用户手动决策
    log.push("ℹ️ 紫色光晕（可选）：建议在预览后手动对需要的 SCENE 添加 Glow 效果");
}

app.endUndoGroup();

// ─── 输出日志 ─────────────────────────────────────────────
var report = "═══ Light Theme Conversion Report ═══\n\n" + log.join("\n") + "\n\n═══ 完成 ═══\nCtrl+Z 可一键撤销所有改动";
alert(report);
