/**
 * ae-inspect-screen-precomp.jsx
 * 探测 SCENE_01/05/10/13 的 Screen 预合成内部结构
 * 纯只读，不修改任何东西
 */
(function () {
    var SCENES = [
        { scene: "SCENE_01", screens: ["Screen 01"] },
        { scene: "SCENE_05", screens: ["Screen 01"] },
        { scene: "SCENE_10", screens: ["Screen 01", "Screen 02"] },
        { scene: "SCENE_13", screens: ["Screen 01", "Screen 02"] }
    ];

    function findCompByName(name) {
        for (var i = 1; i <= app.project.numItems; i++) {
            var it = app.project.item(i);
            if (it instanceof CompItem && it.name === name) return it;
        }
        return null;
    }

    function findLayerByKeyword(comp, kw) {
        for (var i = 1; i <= comp.numLayers; i++) {
            if (comp.layer(i).name.toLowerCase().indexOf(kw.toLowerCase()) > -1)
                return comp.layer(i);
        }
        return null;
    }

    var msg = "── Screen 预合成内部结构 ──\n\n";

    for (var s = 0; s < SCENES.length; s++) {
        var cfg = SCENES[s];
        var sceneComp = findCompByName(cfg.scene);
        if (!sceneComp) { msg += cfg.scene + ": NOT FOUND\n\n"; continue; }

        for (var k = 0; k < cfg.screens.length; k++) {
            var screenName = cfg.screens[k];
            var screenLayer = findLayerByKeyword(sceneComp, screenName);
            if (!screenLayer) {
                msg += cfg.scene + " > " + screenName + ": layer NOT FOUND\n";
                continue;
            }

            var src = screenLayer.source;
            msg += cfg.scene + " > " + screenLayer.name + "\n";
            msg += "  layer source type: " + (src instanceof CompItem ? "CompItem" : src instanceof FootageItem ? "FootageItem" : "other") + "\n";
            msg += "  source name: " + (src ? src.name : "(null)") + "\n";

            if (src instanceof CompItem) {
                msg += "  precomp size: " + src.width + "x" + src.height + "\n";
                msg += "  precomp layers (" + src.numLayers + "):\n";
                for (var j = 1; j <= src.numLayers; j++) {
                    var lyr = src.layer(j);
                    var type = "?";
                    var srcName = "";
                    if (lyr.source instanceof CompItem) {
                        type = "PreComp";
                        srcName = lyr.source.name;
                    } else if (lyr.source instanceof FootageItem) {
                        if (lyr.source.mainSource instanceof SolidSource) {
                            type = "Solid";
                            srcName = "color=[" + lyr.source.mainSource.color.join(",") + "]";
                        } else if (lyr.source.file) {
                            type = "File";
                            srcName = lyr.source.file.name;
                        } else {
                            type = "Footage(other)";
                            srcName = lyr.source.name;
                        }
                    }
                    var scaleVal = "";
                    try { scaleVal = " scale=" + lyr.property("Scale").value.join(","); } catch (e) { }
                    msg += "    #" + j + " [" + (lyr.enabled ? " " : "x") + "] " + lyr.name;
                    msg += " | " + type + " | " + srcName + " | " + lyr.source.width + "x" + lyr.source.height + scaleVal + "\n";
                }
            } else if (src instanceof FootageItem) {
                msg += "  ⚠ source 已经是 FootageItem（可能被之前的脚本替换过）\n";
                if (src.file) msg += "  file: " + src.file.name + "\n";
                msg += "  size: " + src.width + "x" + src.height + "\n";
            }
            msg += "\n";
        }
    }

    msg += "把这段报告发给 Cascade，据此写 v2 替换脚本。";
    alert(msg);
})();
