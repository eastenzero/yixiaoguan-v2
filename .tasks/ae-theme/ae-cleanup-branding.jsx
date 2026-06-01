/**
 * ae-cleanup-branding.jsx
 * Disable Envato logo + MotionFox branding in ALL "Phone Back" precomps
 * Also cleans Text Holder in SCENE_30 (videohive branding text)
 *
 * Safe: only disables layers (lyr.enabled = false), no source replacement
 * Undo: Ctrl+Z
 */
(function () {
    app.beginUndoGroup("Cleanup branding");

    var cleaned = [];
    var BRANDING_KEYWORDS = ["envato", "motionfox", "videohive", "lorem ipsum"];

    // ── 1. Clean all Phone Back precomps ──
    for (var i = 1; i <= app.project.numItems; i++) {
        var it = app.project.item(i);
        if (!(it instanceof CompItem)) continue;

        if (it.name === "Phone Back") {
            for (var j = 1; j <= it.numLayers; j++) {
                var lyr = it.layer(j);
                var nameLower = lyr.name.toLowerCase();
                for (var k = 0; k < BRANDING_KEYWORDS.length; k++) {
                    if (nameLower.indexOf(BRANDING_KEYWORDS[k]) > -1) {
                        if (lyr.enabled) {
                            lyr.enabled = false;
                            cleaned.push("Phone Back #" + j + " " + lyr.name + " -> disabled");
                        } else {
                            cleaned.push("Phone Back #" + j + " " + lyr.name + " (already disabled)");
                        }
                        break;
                    }
                }
            }
        }
    }

    // ── 2. Clean Text Holder in SCENE_30 ──
    // Find SCENE_30's Text Holder and disable branding text
    for (var i = 1; i <= app.project.numItems; i++) {
        var it = app.project.item(i);
        if (!(it instanceof CompItem) || it.name !== "SCENE_30") continue;

        for (var j = 1; j <= it.numLayers; j++) {
            var lyr = it.layer(j);
            var lyrSrc = null;
            try { lyrSrc = lyr.source; } catch (e) { }
            if (lyrSrc instanceof CompItem && lyrSrc.name === "Text Holder") {
                for (var t = 1; t <= lyrSrc.numLayers; t++) {
                    var txtLyr = lyrSrc.layer(t);
                    var txtName = txtLyr.name.toLowerCase();
                    for (var k = 0; k < BRANDING_KEYWORDS.length; k++) {
                        if (txtName.indexOf(BRANDING_KEYWORDS[k]) > -1) {
                            if (txtLyr.enabled) {
                                txtLyr.enabled = false;
                                cleaned.push("Text Holder #" + t + " " + txtLyr.name + " -> disabled");
                            }
                            break;
                        }
                    }
                }
            }
        }
    }

    app.endUndoGroup();

    var msg = "== Branding Cleanup ==\n\n";
    if (cleaned.length === 0) {
        msg += "Nothing found to clean.\n";
    } else {
        for (var m = 0; m < cleaned.length; m++) {
            msg += cleaned[m] + "\n";
        }
    }
    msg += "\nTotal: " + cleaned.length + " layers affected";
    alert(msg);
})();
