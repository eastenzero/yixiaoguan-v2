/**
 * ae-fix-screen-top-align.jsx
 * After ae-replace-screens-v2.jsx, fix tall images to show from the TOP
 * instead of being centered (which would show the middle of a long page).
 *
 * Sets anchor point to top-center and position to top-center of precomp.
 * Run AFTER ae-replace-screens-v2.jsx.
 */

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

app.beginUndoGroup("Fix screen top-align");

var report = [];

for (var s = 0; s < SCENES.length; s++) {
    var cfg = SCENES[s];
    var sceneComp = findCompByName(cfg.scene);
    if (!sceneComp) continue;

    for (var k = 0; k < cfg.screens.length; k++) {
        var screenLayer = findLayerByKeyword(sceneComp, cfg.screens[k]);
        if (!screenLayer) continue;

        var precomp = null;
        try { precomp = screenLayer.source; } catch (e) { }
        if (!(precomp instanceof CompItem)) continue;

        var target = findReplaceable(precomp);
        if (!target) continue;

        var imgW = 0, imgH = 0;
        try { imgW = target.source.width; imgH = target.source.height; } catch (e) { continue; }

        // Anchor at top-center of image, position at top-center of precomp
        try {
            target.property("Anchor Point").setValue([imgW / 2, 0, 0]);
            target.property("Position").setValue([precomp.width / 2, 0, 0]);
        } catch (e) {
            // 2D fallback
            try {
                target.property("Anchor Point").setValue([imgW / 2, 0]);
                target.property("Position").setValue([precomp.width / 2, 0]);
            } catch (e2) { }
        }

        var scaledH = Math.round(imgH * (precomp.width / imgW));
        var overflow = scaledH - precomp.height;
        report.push("OK " + cfg.scene + " " + cfg.screens[k]
            + " | img=" + imgW + "x" + imgH
            + " | scaledH=" + scaledH
            + " | overflow=" + overflow + "px"
            + (overflow > 50 ? " (cropped from bottom)" : " (fits)"));
    }
}

app.endUndoGroup();

var msg = "== Top-Align Fix ==\n\n";
for (var m = 0; m < report.length; m++) {
    msg += report[m] + "\n";
}
alert(msg);
