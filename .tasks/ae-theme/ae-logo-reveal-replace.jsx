/**
 * Replace logo + tagline in Quick Logo Reveal template
 * Run after opening quick_logo_reveal.aep
 */
(function () {
    var LOGO_PNG = "F:\\Documents\\code\\yixiaoguan-v2\\.tasks\\ae-theme\\logo-yxg-4k.png";
    var TAGLINE = "\u533B\u7BA1\u667A\u67A2";  // 医管智枢
    var OUT = "F:\\Documents\\code\\yixiaoguan-v2\\.tasks\\ae-theme\\logo-reveal-replace.txt";
    var lines = [];
    var proj = app.project;

    // --- Step 1: Import the logo PNG ---
    var logoFile = new File(LOGO_PNG);
    if (!logoFile.exists) {
        alert("Logo file not found:\n" + LOGO_PNG);
        return;
    }
    var importOpts = new ImportOptions(logoFile);
    var logoFootage = proj.importFile(importOpts);
    logoFootage.name = "yxg-logo";
    lines.push("[OK] Imported logo: " + LOGO_PNG);

    // --- Step 2: Replace in logo_holder comp (#53) ---
    var logoHolder = null;
    for (var i = 1; i <= proj.numItems; i++) {
        if (proj.item(i) instanceof CompItem && proj.item(i).name === "logo_holder") {
            logoHolder = proj.item(i);
            break;
        }
    }

    if (!logoHolder) {
        alert("logo_holder comp not found!");
        return;
    }

    // Disable all existing logo layers, add ours on top
    for (var j = 1; j <= logoHolder.numLayers; j++) {
        logoHolder.layer(j).enabled = false;
        lines.push("[OK] Disabled: " + logoHolder.layer(j).name);
    }

    // Add our logo
    var newLayer = logoHolder.layers.add(logoFootage);
    newLayer.name = "yxg-logo";

    // Scale to fit comp (3840x2160) while keeping aspect ratio
    var compW = logoHolder.width;
    var compH = logoHolder.height;
    var srcW = newLayer.source.width;
    var srcH = newLayer.source.height;
    var scaleW = (compW / srcW) * 100;
    var scaleH = (compH / srcH) * 100;
    // Use the smaller scale to fit inside, with some padding
    var scale = Math.min(scaleW, scaleH) * 0.7;  // 70% of comp for good framing
    newLayer.property("Scale").setValue([scale, scale]);

    // Center position
    newLayer.property("Position").setValue([compW / 2, compH / 2]);

    // Move to top
    newLayer.moveToBeginning();
    lines.push("[OK] Added yxg-logo to logo_holder, scale=" + scale.toFixed(1) + "%");

    // --- Step 3: Update tagline ---
    var taglineHolder = null;
    for (var i = 1; i <= proj.numItems; i++) {
        if (proj.item(i) instanceof CompItem && proj.item(i).name === "tagline_holder") {
            taglineHolder = proj.item(i);
            break;
        }
    }

    if (taglineHolder) {
        for (var j = 1; j <= taglineHolder.numLayers; j++) {
            var lyr = taglineHolder.layer(j);
            if (lyr instanceof TextLayer) {
                var textProp = lyr.property("Source Text");
                var textDoc = textProp.value;
                var oldText = textDoc.text;
                textDoc.text = TAGLINE;
                textDoc.fontSize = 120;
                textDoc.fillColor = [91 / 255, 33 / 255, 182 / 255];  // #5B21B6
                try {
                    textDoc.font = "AlibabaPuHuiTi-2-75-SemiBold";
                } catch (e) {
                    try { textDoc.font = "MicrosoftYaHei"; } catch (e2) { }
                }
                textProp.setValue(textDoc);
                lyr.enabled = true;
                lines.push("[OK] Tagline: '" + oldText + "' -> '" + TAGLINE + "'");
                break;
            }
        }
    }

    // --- Step 4: Log render comp info ---
    for (var i = 1; i <= proj.numItems; i++) {
        var item = proj.item(i);
        if (item instanceof CompItem && item.name === "quick_logo_reveal_2160p") {
            lines.push("");
            lines.push("[INFO] Render comp: " + item.name + " (" + item.width + "x" + item.height + ", " + item.duration.toFixed(1) + "s)");
            for (var j = 1; j <= item.numLayers; j++) {
                lines.push("  L" + j + " " + item.layer(j).name);
            }
        }
    }

    // Write log
    var f = new File(OUT);
    f.encoding = "UTF-8";
    f.open("w");
    f.write(lines.join("\n"));
    f.close();
    alert("Done! Check:\n" + OUT);
})();
