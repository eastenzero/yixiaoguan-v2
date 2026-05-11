/**
 * ae-inspect-text-holder.jsx
 * T10 辅助脚本 — 探测模板里 Text Holder 嵌套合成的真实结构
 *
 * 目的：在写真正的"加中文字幕"脚本前，先搞清 Text Holder 内部有几层、
 *       哪一层是 TextLayer、当前文字 / 字体 / 字号是多少。
 *
 * 用法：File > Scripts > Run Script File... > 选本文件
 * 安全：纯只读，不修改任何东西
 */

(function () {
    function findCompByName(name) {
        for (var i = 1; i <= app.project.numItems; i++) {
            var it = app.project.item(i);
            if (it instanceof CompItem && it.name === name) return it;
        }
        return null;
    }

    function findLayerByKeyword(comp, kw) {
        for (var i = 1; i <= comp.numLayers; i++) {
            if (comp.layer(i).name.toLowerCase().indexOf(kw.toLowerCase()) > -1) {
                return comp.layer(i);
            }
        }
        return null;
    }

    function describeLayer(layer) {
        var type = "Other";
        if (layer instanceof TextLayer) type = "TextLayer";
        else if (layer.nullLayer) type = "Null";
        else if (layer.source instanceof CompItem) type = "PreComp(" + layer.source.name + ")";
        else if (layer.source instanceof FootageItem) type = "Footage(" + layer.source.name + ")";
        else if (layer instanceof ShapeLayer) type = "Shape";
        else if (layer instanceof CameraLayer) type = "Camera";

        var line = "  #" + layer.index + " [" + (layer.enabled ? " " : "x") + "] " + layer.name + " | " + type;

        if (layer.threeDLayer) line += " | 3D";

        if (layer instanceof TextLayer) {
            try {
                var td = layer.property("Source Text").value;
                line += "\n        text   : \"" + (td.text || "").substring(0, 80) + "\"";
                line += "\n        font   : " + td.font;
                line += "\n        size   : " + td.fontSize;
                if (td.fillColor) line += "\n        color  : [" + td.fillColor.join(", ") + "]";
            } catch (e) {
                line += " (text read err: " + e + ")";
            }
        }
        return line;
    }

    // ---- 主逻辑：扫描 SCENE_04 / 11 / 12 / 15 等带 Text Holder 的 SCENE ----
    var SCENES_WITH_TEXT_HOLDER = ["SCENE_04", "SCENE_11", "SCENE_12", "SCENE_15", "SCENE_22", "SCENE_25"];
    var msg = "── Text Holder 探测报告 ──\n\n";
    var sampledHolderComp = null;

    for (var i = 0; i < SCENES_WITH_TEXT_HOLDER.length; i++) {
        var sn = SCENES_WITH_TEXT_HOLDER[i];
        var sc = findCompByName(sn);
        if (!sc) {
            msg += "[?] " + sn + " 找不到\n";
            continue;
        }

        var holderLayer = findLayerByKeyword(sc, "Text Holder");
        if (!holderLayer) {
            msg += "[ ] " + sn + " 没有 Text Holder 层\n";
            continue;
        }

        msg += "[*] " + sn + " > " + holderLayer.name + "\n";
        msg += "        source: " + (holderLayer.source ? holderLayer.source.name : "(none)") + "\n";
        msg += "        3D    : " + (holderLayer.threeDLayer ? "yes" : "no") + "\n";

        if (!sampledHolderComp && holderLayer.source instanceof CompItem) {
            sampledHolderComp = holderLayer.source;
        }
    }

    msg += "\n";

    // ---- 深入 sample Text Holder 的内部 ----
    if (sampledHolderComp) {
        msg += "── " + sampledHolderComp.name + " 内部 (" + sampledHolderComp.numLayers + " 层) ──\n";
        for (var k = 1; k <= sampledHolderComp.numLayers; k++) {
            msg += describeLayer(sampledHolderComp.layer(k)) + "\n";
        }

        msg += "\n── Text Holder size & duration ──\n";
        msg += "  width    : " + sampledHolderComp.width + "\n";
        msg += "  height   : " + sampledHolderComp.height + "\n";
        msg += "  duration : " + sampledHolderComp.duration.toFixed(2) + " s\n";
    } else {
        msg += "✗ 没有从任何 SCENE 抓到 Text Holder comp，可能模板结构跟假设不同\n";
    }

    // ---- 字体可用性测试 ----
    msg += "\n── 中文字体探测（在临时 TextLayer 上 set/read 比对）──\n";
    var FONT_CANDIDATES = [
        "SourceHanSansCN-Bold",
        "SourceHanSansSC-Bold",
        "SourceHanSansCN-Heavy",
        "AdobeFanHeitiStd-Bold",
        "MicrosoftYaHei-Bold",
        "MicrosoftYaHeiUI-Bold",
        "MicrosoftYaHei",
        "Microsoft YaHei",
        "AlibabaPuHuiTi-3-85-Bold",
        "AlibabaPuHuiTiB",
        "SimHei",
        "SimSun"
    ];

    var tmpComp = app.project.items.addComp("__tmp_font_probe__", 100, 100, 1, 1, 24);
    var tmpText = tmpComp.layers.addText("医小管");
    var tdProbe = tmpText.property("Source Text").value;

    for (var f = 0; f < FONT_CANDIDATES.length; f++) {
        try {
            tdProbe.font = FONT_CANDIDATES[f];
            tmpText.property("Source Text").setValue(tdProbe);
            // 重读一次拿生效字体
            var actual = tmpText.property("Source Text").value.font;
            var ok = (actual === FONT_CANDIDATES[f]);
            msg += "  " + (ok ? "✓" : "?") + " " + FONT_CANDIDATES[f];
            if (!ok) msg += " (实际生效: " + actual + ")";
            msg += "\n";
        } catch (e) {
            msg += "  ✗ " + FONT_CANDIDATES[f] + " (err: " + e + ")\n";
        }
    }

    tmpComp.remove();

    msg += "\n探测完毕。把这段报告复制回主对话，Cascade 据此决定加字幕脚本里用的字体名。";
    alert(msg);
})();
