/**
 * ae-replace-v3-new-scenes.jsx
 * Replace screens + edit Text Holders for 5 new scenes
 * Duplicates Screen precomps to avoid shared-comp conflicts
 * Results -> .tasks/ae-theme/replace-v3-result.txt
 */
(function () {
    var REPO = "F:\\Documents\\code\\yixiaoguan-v2";
    var STU = REPO + "\\.tasks\\student-ui-audit-2026-05-11\\after-avatar";
    var TEA = REPO + "\\.tasks\\teacher-ui-audit-2026-05-11\\after-avatar";
    var OUT = REPO + "\\.tasks\\ae-theme\\replace-v3-result.txt";
    var PURPLE = [91 / 255, 33 / 255, 182 / 255];
    var FONTS = ["MicrosoftYaHei", "SimHei", "Arial"];

    var TARGETS = [
        {
            scene: "SCENE_23", screens: { "Screen 01": STU + "\\02-home.png" },
            title: "\u533B\u5C0F\u7BA1", sub: "\u667A\u80FD\u533B\u5B66\u95EE\u7B54\u52A9\u624B"
        },
        {
            scene: "SCENE_11", screens: { "Screen 01": STU + "\\04-chat-with-conv.png" },
            title: "AI \u5B9E\u65F6\u95EE\u7B54", sub: "\u6D41\u5F0F\u56DE\u590D \u00B7 \u667A\u80FD\u68C0\u7D22"
        },
        {
            scene: "SCENE_18", screens: { "Screen 01": STU + "\\03-chat-empty.png", "Screen 02": TEA + "\\02-dashboard.png" },
            title: "\u5B66\u751F\u63D0\u95EE \u00D7 \u6559\u5E08\u7BA1\u7406", sub: "\u53CC\u7AEF\u5B9E\u65F6\u534F\u540C"
        },
        {
            scene: "SCENE_28", screens: {
                "Screen 01": STU + "\\02-home.png", "Screen 02": STU + "\\04-chat-with-conv.png",
                "Screen 03": STU + "\\06-services.png", "Screen 04": TEA + "\\02-dashboard.png", "Screen 05": TEA + "\\09-analytics.png"
            },
            title: "\u5168\u65B9\u4F4D\u667A\u80FD\u6559\u80B2", sub: "5 \u5927\u6838\u5FC3\u529F\u80FD\u4E00\u89C8"
        },
        {
            scene: "SCENE_30", screens: { "Screen 01": STU + "\\06-services.png", "Screen 02": TEA + "\\09-analytics.png" },
            title: "\u53CC\u7AEF\u534F\u540C", sub: "\u5B9E\u65F6\u8054\u52A8"
        }
    ];

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

    // Recursively find Screen precomps: returns [{name, precomp, parentLayer}]
    function findScreens(comp, depth) {
        if (depth > 4) return [];
        var result = [];
        for (var i = 1; i <= comp.numLayers; i++) {
            var lyr = comp.layer(i);
            var src = null;
            try { src = lyr.source; } catch (e) { }
            if (!(src instanceof CompItem)) continue;
            if (lyr.name.match(/^Screen \d+$/)) {
                result.push({ name: lyr.name, precomp: src, parentLayer: lyr });
            } else {
                result = result.concat(findScreens(src, depth + 1));
            }
        }
        return result;
    }

    // Find Text Holder precomp
    function findTextHolder(comp, depth) {
        if (depth > 4) return null;
        for (var i = 1; i <= comp.numLayers; i++) {
            var lyr = comp.layer(i);
            var src = null;
            try { src = lyr.source; } catch (e) { }
            if (!(src instanceof CompItem)) continue;
            if (lyr.name === "Text Holder") return { precomp: src, layer: lyr };
            var sub = findTextHolder(src, depth + 1);
            if (sub) return sub;
        }
        return null;
    }

    // Find bottom-most FootageItem layer in a precomp
    function findReplaceable(precomp) {
        for (var j = precomp.numLayers; j >= 1; j--) {
            var src = null;
            try { src = precomp.layer(j).source; } catch (e) { }
            if (src != null && src instanceof FootageItem) return precomp.layer(j);
        }
        return null;
    }

    // Set text on a text layer with Chinese font + purple color
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
    app.beginUndoGroup("Replace v3 new scenes");

    for (var t = 0; t < TARGETS.length; t++) {
        var cfg = TARGETS[t];
        var sceneComp = findComp(cfg.scene);
        if (!sceneComp) { log.push("X " + cfg.scene + ": not found"); continue; }

        // ── 1. Replace Screens ──
        var screens = findScreens(sceneComp, 0);
        for (var s = 0; s < screens.length; s++) {
            var sc = screens[s];
            var imgPath = cfg.screens[sc.name];
            if (!imgPath) continue; // no mapping for this screen

            // Duplicate precomp to avoid shared-comp conflicts
            var newPrecomp = sc.precomp.duplicate();
            newPrecomp.name = sc.name + " - " + cfg.scene;
            sc.parentLayer.replaceSource(newPrecomp, false);

            // Find replaceable layer inside duplicated precomp
            var target = findReplaceable(newPrecomp);
            if (!target) { log.push("X " + cfg.scene + " " + sc.name + ": no replaceable layer"); continue; }

            // Import PNG
            var newItem = importOnce(imgPath);
            if (!newItem) { log.push("X " + cfg.scene + " " + sc.name + ": file missing"); continue; }

            // Replace source
            var oldName = target.name;
            target.replaceSource(newItem, false);

            // Scale to fit precomp width
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

            // Disable MOCKUP text overlay layers
            for (var d = 1; d <= newPrecomp.numLayers; d++) {
                var dn = newPrecomp.layer(d).name.toLowerCase();
                if (dn.indexOf("mockup") > -1 || dn.indexOf("motionfox") > -1) {
                    newPrecomp.layer(d).enabled = false;
                }
            }

            var scaledH = Math.round(newItem.height * (newPrecomp.width / newItem.width));
            log.push("OK " + cfg.scene + " " + sc.name + " (" + oldName + ") -> " + newItem.name
                + " | scale=" + fitScale.toFixed(1) + "% | overflow=" + (scaledH - newPrecomp.height) + "px");
        }

        // ── 2. Edit Text Holder ──
        var th = findTextHolder(sceneComp, 0);
        if (th && cfg.title) {
            var titleSet = false, subSet = false;
            for (var lt = 1; lt <= th.precomp.numLayers; lt++) {
                var txtLyr = th.precomp.layer(lt);
                txtLyr.enabled = true; // re-enable (may have been disabled by cleanup)
                var isSubLine = txtLyr.name.toLowerCase().indexOf("exclusive download only on") === 0;
                if (isSubLine && !subSet) {
                    setText(txtLyr, cfg.sub);
                    subSet = true;
                    log.push("OK " + cfg.scene + " Text sub: " + cfg.sub);
                } else if (!titleSet) {
                    setText(txtLyr, cfg.title);
                    titleSet = true;
                    log.push("OK " + cfg.scene + " Text title: " + cfg.title);
                } else if (!subSet) {
                    setText(txtLyr, cfg.sub);
                    subSet = true;
                    log.push("OK " + cfg.scene + " Text sub: " + cfg.sub);
                }
            }
        }
    }

    app.endUndoGroup();

    // ── Write results ──
    var outFile = new File(OUT);
    outFile.open("w");
    outFile.encoding = "UTF-8";
    outFile.write("== Replace v3 Results ==\n" + new Date().toString() + "\n\n");
    for (var i = 0; i < log.length; i++) outFile.write(log[i] + "\n");
    outFile.write("\nTotal: " + log.length + " operations\nCtrl+Z to undo");
    outFile.close();

    alert("Done! " + log.length + " operations.\nResults: " + OUT);
})();
