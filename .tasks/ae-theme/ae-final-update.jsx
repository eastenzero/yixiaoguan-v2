/**
 * ae-final-update.jsx
 * Final pass:
 *   1. Replace SCENE_27 screens (swap from S28)
 *   2. Update all 5 Text Holders with director's final copy
 *   3. Disable MOCKUP layers in S27
 * Results -> file
 */
(function () {
    var REPO = "F:\\Documents\\code\\yixiaoguan-v2";
    var STU = REPO + "\\.tasks\\student-ui-audit-2026-05-11\\after-avatar";
    var TEA = REPO + "\\.tasks\\teacher-ui-audit-2026-05-11\\after-avatar";
    var OUT = REPO + "\\.tasks\\ae-theme\\final-update-result.txt";
    var PURPLE = [91 / 255, 33 / 255, 182 / 255];
    var FONTS = ["AlibabaPuHuiTi-2-75-SemiBold", "AlibabaPuHuiTi-Bold", "MicrosoftYaHei"];

    // Director's final copy (2026-05-12)
    var TEXT_FINAL = [
        {
            scene: "SCENE_23",
            title: "\u6821\u56ED\u91CC\u7684\u4E8B \u00B7 \u95EE\u533B\u5C0F\u7BA1",
            sub: "\u667A\u80FD\u95EE\u7B54 \u00B7 \u79D2\u7B54\u5E38\u89C1\u95EE\u9898"
        },
        {
            scene: "SCENE_11",
            title: "AI \u6D41\u5F0F\u56DE\u7B54 \u00B7 \u6709\u636E\u53EF\u67E5",
            sub: "\u6765\u6E90\u53EF\u6EAF \u00B7 \u5386\u53F2\u53EF\u56DE"
        },
        {
            scene: "SCENE_18",
            title: "\u5B66\u751F\u6709\u95EE \u00B7 \u8001\u5E08\u5728\u573A",
            sub: "\u4E00\u952E\u8F6C\u4EBA\u5DE5 \u00B7 \u7AEF\u5230\u7AEF\u4E0D\u5230200\u6BEB\u79D2"
        },
        {
            scene: "SCENE_27",
            title: "\u5168\u573A\u666F\u6D1E\u5BDF \u00B7 \u4E00\u5C4F\u5230\u4F4D",
            sub: "\u95EE\u7B54 \u00B7 \u670D\u52A1 \u00B7 \u6570\u636E \u00B7 \u77E5\u8BC6"
        },
        {
            scene: "SCENE_30",
            title: "\u8BA9\u6BCF\u4E00\u4E2A\u95EE\u9898\u88AB\u8BA4\u771F\u5BF9\u5F85",
            sub: "\u533B\u5C0F\u7BA1 \u00B7 \u667A\u6167\u6821\u56ED\u52A9\u7406"
        }
    ];

    // S27 screen mapping: 4 screens matching subtitle "问答 · 服务 · 数据 · 知识"
    var S27_SCREENS = {
        "Screen 01": STU + "\\04-chat-with-conv.png",
        "Screen 02": STU + "\\06-services.png",
        "Screen 03": TEA + "\\09-analytics.png",
        "Screen 04": TEA + "\\06-knowledge-list.png"
    };

    var importCache = {};
    var log = [];

    function findComp(name) {
        for (var i = 1; i <= app.project.numItems; i++) {
            var it = app.project.item(i);
            if (it instanceof CompItem && it.name === name) return it;
        }
        return null;
    }

    function importOnce(path) {
        if (importCache[path]) return importCache[path];
        var f = new File(path);
        if (!f.exists) return null;
        var item = app.project.importFile(new ImportOptions(f));
        importCache[path] = item;
        return item;
    }

    function findScreens(comp, depth) {
        if (depth > 4) return [];
        var results = [];
        for (var i = 1; i <= comp.numLayers; i++) {
            var lyr = comp.layer(i);
            var src = null;
            try { src = lyr.source; } catch (e) { }
            if (!(src instanceof CompItem)) continue;
            if (lyr.name.indexOf("Screen") === 0 && lyr.name.indexOf("Screen Camera") === -1 && lyr.name.indexOf("Screen Frame") === -1) {
                results.push({ name: lyr.name, precomp: src, parentLayer: lyr });
            } else {
                var sub = findScreens(src, depth + 1);
                for (var s = 0; s < sub.length; s++) results.push(sub[s]);
            }
        }
        return results;
    }

    function findReplaceable(precomp) {
        for (var i = precomp.numLayers; i >= 1; i--) {
            var lyr = precomp.layer(i);
            var src = null;
            try { src = lyr.source; } catch (e) { }
            if (src instanceof FootageItem || (src && !(src instanceof CompItem))) return lyr;
        }
        return null;
    }

    function findTextHolder(comp, depth) {
        if (depth > 4) return null;
        for (var i = 1; i <= comp.numLayers; i++) {
            var lyr = comp.layer(i);
            var src = null;
            try { src = lyr.source; } catch (e) { }
            if (!(src instanceof CompItem)) continue;
            if (lyr.name === "Text Holder") return src;
            var sub = findTextHolder(src, depth + 1);
            if (sub) return sub;
        }
        return null;
    }

    function setText(textLayer, newText) {
        try {
            var prop = textLayer.property("Source Text");
            var doc = prop.value;
            doc.text = newText;
            doc.fillColor = PURPLE;
            for (var f = 0; f < FONTS.length; f++) {
                try { doc.font = FONTS[f]; break; } catch (e) { }
            }
            prop.setValue(doc);
            return true;
        } catch (e) { return false; }
    }

    // ── MAIN ──
    app.beginUndoGroup("Final Update");

    // ── 1. Replace SCENE_27 screens ──
    var s27Comp = findComp("SCENE_27");
    if (!s27Comp) {
        log.push("X SCENE_27: not found");
    } else {
        var screens = findScreens(s27Comp, 0);
        for (var s = 0; s < screens.length; s++) {
            var sc = screens[s];
            var imgPath = S27_SCREENS[sc.name];
            if (!imgPath) continue;

            var newPrecomp = sc.precomp.duplicate();
            newPrecomp.name = sc.name + " - SCENE_27";
            sc.parentLayer.replaceSource(newPrecomp, false);

            var target = findReplaceable(newPrecomp);
            if (!target) { log.push("X S27 " + sc.name + ": no replaceable layer"); continue; }

            var newItem = importOnce(imgPath);
            if (!newItem) { log.push("X S27 " + sc.name + ": file not found - " + imgPath); continue; }

            var oldName = target.name;
            target.replaceSource(newItem, false);

            // Scale to fit
            var fitScale = (newPrecomp.width / newItem.width) * 100;
            try { target.property("Scale").setValue([fitScale, fitScale, 100]); }
            catch (e) { try { target.property("Scale").setValue([fitScale, fitScale]); } catch (e2) { } }

            // Top-align
            try {
                target.property("Anchor Point").setValue([newItem.width / 2, 0, 0]);
                target.property("Position").setValue([newPrecomp.width / 2, 0, 0]);
            } catch (e) {
                try {
                    target.property("Anchor Point").setValue([newItem.width / 2, 0]);
                    target.property("Position").setValue([newPrecomp.width / 2, 0]);
                } catch (e2) { }
            }

            // Disable MOCKUP overlays
            for (var d = 1; d <= newPrecomp.numLayers; d++) {
                var dn = newPrecomp.layer(d).name.toLowerCase();
                if (dn.indexOf("mockup") > -1 || dn.indexOf("motionfox") > -1) {
                    newPrecomp.layer(d).enabled = false;
                }
            }

            var scaledH = Math.round(newItem.height * (newPrecomp.width / newItem.width));
            log.push("OK S27 " + sc.name + " (" + oldName + ") -> " + newItem.name
                + " | scale=" + fitScale.toFixed(1) + "% | overflow=" + (scaledH - newPrecomp.height) + "px");
        }
    }

    // ── 2. Update Text Holders (all 5 scenes) ──
    for (var t = 0; t < TEXT_FINAL.length; t++) {
        var cfg = TEXT_FINAL[t];
        var sceneComp = findComp(cfg.scene);
        if (!sceneComp) { log.push("X " + cfg.scene + ": not found"); continue; }

        var thComp = findTextHolder(sceneComp, 0);
        if (!thComp) { log.push("X " + cfg.scene + ": no Text Holder"); continue; }

        if (thComp.numLayers >= 2) {
            var lyr1 = thComp.layer(1);
            var lyr2 = thComp.layer(2);
            lyr1.enabled = true;
            lyr2.enabled = true;

            var size1 = 0, size2 = 0;
            try { size1 = lyr1.property("Source Text").value.fontSize; } catch (e) { }
            try { size2 = lyr2.property("Source Text").value.fontSize; } catch (e) { }

            var titleLyr, subLyr, titleIdx, subIdx;
            if (size1 >= size2) {
                titleLyr = lyr1; subLyr = lyr2; titleIdx = 1; subIdx = 2;
            } else {
                titleLyr = lyr2; subLyr = lyr1; titleIdx = 2; subIdx = 1;
            }

            setText(titleLyr, cfg.title);
            setText(subLyr, cfg.sub);
            log.push("TEXT " + cfg.scene + " title(#" + titleIdx + "," + Math.max(size1, size2) + "px): " + cfg.title);
            log.push("TEXT " + cfg.scene + " sub(#" + subIdx + "," + Math.min(size1, size2) + "px): " + cfg.sub);
        } else if (thComp.numLayers === 1) {
            thComp.layer(1).enabled = true;
            setText(thComp.layer(1), cfg.title);
            log.push("TEXT " + cfg.scene + " #1 (only): " + cfg.title);
        }
    }

    app.endUndoGroup();

    // ── Write results ──
    var outFile = new File(OUT);
    outFile.open("w");
    outFile.encoding = "UTF-8";
    outFile.write("== Final Update ==\n" + new Date().toString() + "\n\n");
    outFile.write("Scenes: S23, S11, S18, S27(new), S30\n");
    outFile.write("S28 -> S27 swap applied\n\n");
    for (var i = 0; i < log.length; i++) outFile.write(log[i] + "\n");
    outFile.write("\nTotal: " + log.length + " operations\nCtrl+Z to undo");
    outFile.close();

    alert("Done! " + log.length + " ops.\nS28->S27 swapped.\nDetails: " + OUT);
})();
