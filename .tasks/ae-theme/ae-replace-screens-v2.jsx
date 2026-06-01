/**
 * ae-replace-screens-v2.jsx
 * Enter each Screen precomp and replace the inner placeholder layer
 * Preserves: rounded-corner Shape mask, MotionFox branding, layer transforms
 *
 * Precomp structure (from inspect):
 *   #1  Shape Layer 1          - rounded corners mask
 *   #2  SCREEN MOCKUP ...      - branding overlay
 *   #3  Screen Solid 2         - blue fallback solid  (1170x2532)
 *   #4  <placeholder>.png      - template screenshot  (1179x2556, scale~99.24%)
 *        (SCENE_13 has only 3 layers, no #4 file)
 *
 * Strategy:
 *   - For 4-layer precomps: replaceSource on #4 (File), set uniform scale to fit
 *   - For 3-layer precomps: replaceSource on #3 (Solid), set uniform scale to fit
 *
 * Usage: AE > File > Scripts > Run Script File...
 * Undo:  Ctrl+Z (single undo group)
 * Compat: CS6 ~ CC 2024
 */

var REPO_ROOT = "F:\\Documents\\code\\yixiaoguan-v2";
var TEA_DIR   = REPO_ROOT + "\\.tasks\\teacher-ui-audit-2026-05-11\\after-avatar";
var STU_DIR   = REPO_ROOT + "\\.tasks\\student-ui-audit-2026-05-11\\after-avatar";

var REPLACEMENTS = [
    { scene: "SCENE_01", screen: "Screen 01", image: STU_DIR + "\\02-home.png",            role: "S01 student home" },
    { scene: "SCENE_05", screen: "Screen 01", image: STU_DIR + "\\04-chat-with-conv.png",   role: "S05 student chat" },
    { scene: "SCENE_10", screen: "Screen 01", image: STU_DIR + "\\03-chat-empty.png",       role: "S10-L student chat" },
    { scene: "SCENE_10", screen: "Screen 02", image: TEA_DIR + "\\02-dashboard.png",        role: "S10-R teacher dashboard" },
    { scene: "SCENE_13", screen: "Screen 01", image: STU_DIR + "\\06-services.png",         role: "S13-L student services" },
    { scene: "SCENE_13", screen: "Screen 02", image: TEA_DIR + "\\09-analytics.png",        role: "S13-R teacher analytics" }
];

// ── helpers ──────────────────────────────────────────────────
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

// Find the bottom-most FootageItem layer in a precomp (= placeholder to replace)
function findReplaceable(precomp) {
    for (var j = precomp.numLayers; j >= 1; j--) {
        var lyr = precomp.layer(j);
        var lyrSrc = null;
        try { lyrSrc = lyr.source; } catch (e) { }
        if (lyrSrc != null && lyrSrc instanceof FootageItem) {
            return lyr;
        }
    }
    return null;
}

// ── main ─────────────────────────────────────────────────────
app.beginUndoGroup("Replace screens v2 - inside precomp");

var report = [];

for (var i = 0; i < REPLACEMENTS.length; i++) {
    var r = REPLACEMENTS[i];

    // 1. find SCENE comp
    var sceneComp = findCompByName(r.scene);
    if (!sceneComp) {
        report.push("X " + r.role + ": scene not found");
        continue;
    }

    // 2. find Screen layer in SCENE comp
    var screenLayer = findLayerByKeyword(sceneComp, r.screen);
    if (!screenLayer) {
        report.push("X " + r.role + ": layer '" + r.screen + "' not found in " + r.scene);
        continue;
    }

    // 3. get precomp source
    var precomp = null;
    try { precomp = screenLayer.source; } catch (e) { }
    if (!(precomp instanceof CompItem)) {
        report.push("X " + r.role + ": source is not CompItem");
        continue;
    }

    // 4. find replaceable layer inside precomp
    var target = findReplaceable(precomp);
    if (!target) {
        report.push("X " + r.role + ": no replaceable layer in " + precomp.name);
        continue;
    }

    // 5. import PNG
    var file = new File(r.image);
    if (!file.exists) {
        report.push("X " + r.role + ": file missing " + file.name);
        continue;
    }
    var importOpts = new ImportOptions(file);
    var newItem = app.project.importFile(importOpts);
    if (!newItem) {
        report.push("X " + r.role + ": importFile returned null");
        continue;
    }

    // 6. replace source on the inner placeholder layer
    var oldName = target.name;
    target.replaceSource(newItem, false);

    // 7. uniform scale to fit precomp width (height overflow is clipped)
    var fitScale = (precomp.width / newItem.width) * 100;
    try {
        target.property("Scale").setValue([fitScale, fitScale, 100]);
    } catch (e) {
        // 2D comp fallback
        try { target.property("Scale").setValue([fitScale, fitScale]); } catch (e2) { }
    }

    report.push("OK " + r.role + " | " + precomp.name + " #" + target.index
        + " (" + oldName + ") -> " + newItem.name
        + " | scale=" + fitScale.toFixed(1) + "%"
        + " | precomp=" + precomp.width + "x" + precomp.height
        + " img=" + newItem.width + "x" + newItem.height);
}

app.endUndoGroup();

// ── report ───────────────────────────────────────────────────
var msg = "== Screen Replace v2 ==\n\n";
for (var m = 0; m < report.length; m++) {
    msg += report[m] + "\n";
}
msg += "\nCtrl+Z to undo";
alert(msg);
