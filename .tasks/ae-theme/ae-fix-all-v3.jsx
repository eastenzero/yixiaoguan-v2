/**
 * ae-fix-all-v3.jsx
 * 1. Disable "SCREEN MOCKUP" text in ALL Screen precomps
 * 2. Update Text Holder with better placeholder copy
 * Results -> file
 */
(function () {
    var REPO = "F:\\Documents\\code\\yixiaoguan-v2";
    var OUT = REPO + "\\.tasks\\ae-theme\\fix-all-v3-result.txt";
    var PURPLE = [91 / 255, 33 / 255, 182 / 255];
    var FONTS = ["MicrosoftYaHei", "SimHei", "Arial"];

    var TEXT_MAP = [
        {
            scene: "SCENE_23",
            title: "\u533B\u5C0F\u7BA1 \u00B7 \u667A\u6167\u6821\u56ED\u52A9\u7406",
            sub: "\u57FA\u4E8E\u5927\u8BED\u8A00\u6A21\u578B\u7684\u533B\u5B66\u6559\u80B2\u667A\u80FD\u95EE\u7B54\u5E73\u53F0"
        },
        {
            scene: "SCENE_11",
            title: "AI \u5B9E\u65F6\u95EE\u7B54 \u00B7 \u79D2\u7EA7\u54CD\u5E94",
            sub: "\u652F\u6301\u4E0A\u4E0B\u6587\u7406\u89E3 \u00B7 RAG\u77E5\u8BC6\u68C0\u7D22\u589E\u5F3A"
        },
        {
            scene: "SCENE_18",
            title: "\u5B66\u751F\u7AEF \u00D7 \u6559\u5E08\u7AEF \u53CC\u5411\u534F\u540C",
            sub: "\u95EE\u9898\u81EA\u52A8\u5206\u53D1 \u00B7 \u6559\u5E08\u5B9E\u65F6\u4ECB\u5165 \u00B7 \u5168\u7A0B\u53EF\u8FFD\u6EAF"
        },
        {
            scene: "SCENE_28",
            title: "\u516D\u5927\u6838\u5FC3\u6A21\u5757 \u4E00\u7AD9\u5F0F\u8986\u76D6",
            sub: "\u667A\u80FD\u95EE\u7B54 \u00B7 \u77E5\u8BC6\u5E93 \u00B7 \u670D\u52A1\u4E2D\u5FC3 \u00B7 \u6570\u636E\u5206\u6790 \u00B7 \u6D88\u606F\u7BA1\u7406"
        },
        {
            scene: "SCENE_30",
            title: "\u533B\u5B66\u6559\u80B2\u6570\u5B57\u5316\u8F6C\u578B\u65B9\u6848",
            sub: "\u5C71\u4E1C\u7B2C\u4E00\u533B\u79D1\u5927\u5B66 \u8054\u5408\u7814\u53D1"
        }
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

    app.beginUndoGroup("Fix all v3");

    // ── 1. Disable MOCKUP text in ALL Screen precomps ──
    var mockupCount = 0;
    for (var i = 1; i <= app.project.numItems; i++) {
        var it = app.project.item(i);
        if (!(it instanceof CompItem)) continue;
        if (it.name.indexOf("Screen") !== 0) continue;
        for (var j = 1; j <= it.numLayers; j++) {
            var lyr = it.layer(j);
            var n = lyr.name.toLowerCase();
            if ((n.indexOf("mockup") > -1 || n.indexOf("motionfox") > -1) && lyr.enabled) {
                lyr.enabled = false;
                mockupCount++;
                log.push("MOCKUP " + it.name + " #" + j + " " + lyr.name + " -> disabled");
            }
        }
    }

    // ── 2. Update Text Holders ──
    for (var t = 0; t < TEXT_MAP.length; t++) {
        var cfg = TEXT_MAP[t];
        var sceneComp = findComp(cfg.scene);
        if (!sceneComp) { log.push("X " + cfg.scene + ": not found"); continue; }

        var thComp = findTextHolder(sceneComp, 0);
        if (!thComp) { log.push("X " + cfg.scene + ": no Text Holder"); continue; }

        // Use fontSize to determine which layer is title vs subtitle
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
            log.push("TEXT " + cfg.scene + " #" + titleIdx + " (title, " + Math.max(size1, size2) + "px): " + cfg.title);
            setText(subLyr, cfg.sub);
            log.push("TEXT " + cfg.scene + " #" + subIdx + " (sub, " + Math.min(size1, size2) + "px): " + cfg.sub);
        } else if (thComp.numLayers === 1) {
            thComp.layer(1).enabled = true;
            setText(thComp.layer(1), cfg.title);
            log.push("TEXT " + cfg.scene + " #1 (only): " + cfg.title);
        }
    }

    app.endUndoGroup();

    var outFile = new File(OUT);
    outFile.open("w");
    outFile.encoding = "UTF-8";
    outFile.write("== Fix All v3 ==\n" + new Date().toString() + "\n\n");
    outFile.write("Mockup layers disabled: " + mockupCount + "\n\n");
    for (var m = 0; m < log.length; m++) outFile.write(log[m] + "\n");
    outFile.write("\nTotal: " + log.length + " operations");
    outFile.close();

    alert("Done! Mockup=" + mockupCount + " + Text=" + TEXT_MAP.length + " scenes.\nDetails: " + OUT);
})();
