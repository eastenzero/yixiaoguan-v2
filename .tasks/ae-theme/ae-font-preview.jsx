/**
 * ae-font-preview.jsx
 * Apply different fonts to each scene's Text Holder for comparison
 * After previewing, pick your favorite and tell me
 */
(function () {
    var REPO = "F:\\Documents\\code\\yixiaoguan-v2";
    var OUT = REPO + "\\.tasks\\ae-theme\\font-preview-result.txt";
    var PURPLE = [91 / 255, 33 / 255, 182 / 255];

    // Font candidates to preview (one per scene)
    // AE uses internal PostScript names
    var FONT_OPTIONS = [
        { scene: "SCENE_23", fonts: ["SourceHanSansCN-Bold", "SourceHanSansSC-Bold", "NotoSansCJKsc-Bold", "Source Han Sans CN Bold"], label: "A: \u601D\u6E90\u9ED1\u4F53 Bold" },
        { scene: "SCENE_11", fonts: ["AlibabaPuHuiTi-2-75-SemiBold", "AlibabaPuHuiTi2.0-75SemiBold", "Alibaba-PuHuiTi-Bold", "AlibabaPuHuiTi-Bold"], label: "B: \u963F\u91CC\u5DF4\u5DF4\u666E\u60E0\u4F53 SemiBold" },
        { scene: "SCENE_18", fonts: ["YouSheBiaoTiHei", "YOUSHEBIAOTIHEI", "YouShe-BiaoTiHei"], label: "C: \u4F18\u8BBE\u6807\u9898\u9ED1" },
        { scene: "SCENE_27", fonts: ["HarmonyOS_Sans_SC_Bold", "HarmonyOS Sans SC Bold", "HarmonyOS_Sans_SC"], label: "D: HarmonyOS Sans Bold" },
        { scene: "SCENE_30", fonts: ["MicrosoftYaHei-Bold", "MicrosoftYaHei", "Microsoft-YaHei-Bold"], label: "E: \u5FAE\u8F6F\u96C5\u9ED1 Bold (\u5F53\u524D)" }
    ];

    var log = [];

    function findComp(name) {
        for (var i = 1; i <= app.project.numItems; i++) {
            var it = app.project.item(i);
            if (it instanceof CompItem && it.name === name) return it;
        }
        return null;
    }

    function findTextHolder(comp, depth) {
        if (depth > 4) return null;
        for (var i = 1; i <= comp.numLayers; i++) {
            var lyr = comp.layer(i);
            var src = null;
            try { src = lyr.source; } catch(e) {}
            if (!(src instanceof CompItem)) continue;
            if (lyr.name === "Text Holder") return src;
            var sub = findTextHolder(src, depth + 1);
            if (sub) return sub;
        }
        return null;
    }

    function trySetFont(textLayer, fontList) {
        try {
            var prop = textLayer.property("Source Text");
            var doc = prop.value;
            doc.fillColor = PURPLE;
            var applied = "NONE";
            for (var f = 0; f < fontList.length; f++) {
                try {
                    doc.font = fontList[f];
                    applied = fontList[f];
                    break;
                } catch(e) {}
            }
            prop.setValue(doc);
            return applied;
        } catch(e) { return "ERROR: " + e.message; }
    }

    app.beginUndoGroup("Font Preview");

    for (var t = 0; t < FONT_OPTIONS.length; t++) {
        var cfg = FONT_OPTIONS[t];
        var sceneComp = findComp(cfg.scene);
        if (!sceneComp) { log.push("X " + cfg.scene + ": not found"); continue; }

        var thComp = findTextHolder(sceneComp, 0);
        if (!thComp) { log.push("X " + cfg.scene + ": no Text Holder"); continue; }

        var results = [];
        for (var lt = 1; lt <= thComp.numLayers; lt++) {
            var lyr = thComp.layer(lt);
            if (!lyr.enabled) continue;
            var applied = trySetFont(lyr, cfg.fonts);
            results.push("#" + lt + "=" + applied);
        }
        log.push(cfg.label + " -> " + cfg.scene + " [" + results.join(", ") + "]");
    }

    app.endUndoGroup();

    var outFile = new File(OUT);
    outFile.open("w");
    outFile.encoding = "UTF-8";
    outFile.write("== Font Preview ==\n" + new Date().toString() + "\n\n");
    outFile.write("Each scene uses a different font for comparison:\n\n");
    for (var i = 0; i < log.length; i++) outFile.write(log[i] + "\n");
    outFile.write("\n\nCtrl+Z to undo, then tell me which you like!\n");
    outFile.write("If a font shows 'NONE', it's not installed on this machine.\n");
    outFile.close();

    alert("Font preview applied!\n\nA: \u601D\u6E90\u9ED1\u4F53 -> S23\nB: \u963F\u91CC\u666E\u60E0\u4F53 -> S11\nC: \u4F18\u8BBE\u6807\u9898\u9ED1 -> S18\nD: HarmonyOS Sans -> S27\nE: \u5FAE\u8F6F\u96C5\u9ED1 Bold -> S30\n\nDetails: " + OUT + "\nCtrl+Z to undo after picking!");
})();
