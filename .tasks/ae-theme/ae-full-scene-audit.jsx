/**
 * ae-full-scene-audit.jsx
 * Audit ALL 30 SCENEs: screen count, text holder, structure
 * Writes result to .tasks/ae-theme/scene-audit-result.txt
 */
(function () {
    var REPO = "F:\\Documents\\code\\yixiaoguan-v2";
    var OUT_PATH = REPO + "\\.tasks\\ae-theme\\scene-audit-result.txt";

    function findCompByName(name) {
        for (var i = 1; i <= app.project.numItems; i++) {
            var it = app.project.item(i);
            if (it instanceof CompItem && it.name === name) return it;
        }
        return null;
    }

    // Recursively find Screen and Text Holder comps (max 2 levels deep)
    function auditComp(comp, depth) {
        if (!depth) depth = 0;
        if (depth > 3) return { screens: [], textHolders: [], hasCamera: false };

        var result = { screens: [], textHolders: [], hasCamera: false };

        for (var i = 1; i <= comp.numLayers; i++) {
            var lyr = comp.layer(i);
            var name = lyr.name;
            var lyrSrc = null;
            try { lyrSrc = lyr.source; } catch (e) { }

            if (name.indexOf("Camera") > -1) result.hasCamera = true;

            if (lyrSrc instanceof CompItem) {
                // Check if this is a Screen precomp
                if (name.match(/^Screen \d+$/)) {
                    var screenInfo = { name: name, layers: lyrSrc.numLayers, size: lyrSrc.width + "x" + lyrSrc.height };
                    // Check what's inside
                    var hasFile = false;
                    var hasSolid = false;
                    for (var j = 1; j <= lyrSrc.numLayers; j++) {
                        var innerSrc = null;
                        try { innerSrc = lyrSrc.layer(j).source; } catch (e) { }
                        if (innerSrc instanceof FootageItem) {
                            try {
                                if (innerSrc.mainSource instanceof SolidSource) hasSolid = true;
                                else if (innerSrc.file) {
                                    hasFile = true;
                                    screenInfo.placeholder = innerSrc.file.name;
                                }
                            } catch (e) { }
                        }
                    }
                    screenInfo.type = hasFile ? "File" : (hasSolid ? "Solid" : "Other");
                    result.screens.push(screenInfo);
                }
                // Check if Text Holder
                else if (name === "Text Holder") {
                    var texts = [];
                    for (var t = 1; t <= lyrSrc.numLayers; t++) {
                        texts.push(lyrSrc.layer(t).name.substring(0, 50));
                    }
                    result.textHolders.push({ layers: lyrSrc.numLayers, texts: texts, enabled: lyr.enabled });
                }
                // Recurse into precomps
                else {
                    var sub = auditComp(lyrSrc, depth + 1);
                    result.screens = result.screens.concat(sub.screens);
                    result.textHolders = result.textHolders.concat(sub.textHolders);
                    if (sub.hasCamera) result.hasCamera = true;
                }
            }
        }
        return result;
    }

    var previewComp = findCompByName("PREVIEW COMPS");
    if (!previewComp) { alert("PREVIEW COMPS not found"); return; }

    var lines = [];
    lines.push("== Full Scene Audit ==");
    lines.push("Generated: " + new Date().toString());
    lines.push("");

    // Summary tables
    var summary1phone = [];
    var summary2phone = [];
    var summary3plus = [];

    for (var i = 1; i <= previewComp.numLayers; i++) {
        var lyr = previewComp.layer(i);
        if (lyr.name.indexOf("SCENE_") !== 0) continue;

        var lyrSrc = null;
        try { lyrSrc = lyr.source; } catch (e) { }
        if (!(lyrSrc instanceof CompItem)) continue;

        var sceneName = lyr.name;
        var inT = lyr.inPoint;
        var outT = lyr.outPoint;
        var dur = outT - inT;

        var audit = auditComp(lyrSrc, 0);
        var phoneCount = audit.screens.length;
        var hasText = audit.textHolders.length > 0;
        var has3D = audit.hasCamera;

        // Detail block
        lines.push("━━━ " + sceneName + " ━━━");
        lines.push("  Timeline: " + inT.toFixed(1) + "s - " + outT.toFixed(1) + "s (" + dur.toFixed(1) + "s)");
        lines.push("  Phones: " + phoneCount + " | 3D Camera: " + (has3D ? "YES" : "no") + " | Text Holder: " + (hasText ? "YES" : "no"));

        for (var s = 0; s < audit.screens.length; s++) {
            var sc = audit.screens[s];
            lines.push("  " + sc.name + " [" + sc.type + "] " + sc.size + " (" + sc.layers + " layers)" + (sc.placeholder ? " <- " + sc.placeholder : ""));
        }
        for (var th = 0; th < audit.textHolders.length; th++) {
            var holder = audit.textHolders[th];
            lines.push("  Text Holder [" + (holder.enabled ? "ON" : "OFF") + "] " + holder.layers + " layers:");
            for (var tt = 0; tt < holder.texts.length; tt++) {
                lines.push("    - " + holder.texts[tt]);
            }
        }
        lines.push("");

        // Summary
        var tag = sceneName + " | " + dur.toFixed(0) + "s | " + (has3D ? "3D" : "2D") + " | " + (hasText ? "TEXT" : "    ") + " | " + phoneCount + " phone(s)";
        if (phoneCount === 1) summary1phone.push(tag);
        else if (phoneCount === 2) summary2phone.push(tag);
        else summary3plus.push(tag);
    }

    // Append summary
    lines.push("");
    lines.push("========== SUMMARY ==========");
    lines.push("");
    lines.push("-- 1 PHONE (" + summary1phone.length + ") --");
    for (var a = 0; a < summary1phone.length; a++) lines.push("  " + summary1phone[a]);
    lines.push("");
    lines.push("-- 2 PHONES (" + summary2phone.length + ") --");
    for (var b = 0; b < summary2phone.length; b++) lines.push("  " + summary2phone[b]);
    lines.push("");
    lines.push("-- 3+ PHONES (" + summary3plus.length + ") --");
    for (var c = 0; c < summary3plus.length; c++) lines.push("  " + summary3plus[c]);

    // Write to file
    var outFile = new File(OUT_PATH);
    outFile.open("w");
    outFile.encoding = "UTF-8";
    outFile.write(lines.join("\n"));
    outFile.close();

    alert("Audit complete! Written to:\n" + OUT_PATH + "\n\n" + lines.length + " lines");
})();
