/**
 * ae-fix-mockup-text.jsx
 * Disable "SCREEN MOCKUP By MotionFox" text layers inside ALL Screen precomps
 * These overlay on top of our replaced screenshots
 * Results -> file
 */
(function () {
    var REPO = "F:\\Documents\\code\\yixiaoguan-v2";
    var OUT  = REPO + "\\.tasks\\ae-theme\\fix-mockup-result.txt";

    app.beginUndoGroup("Fix mockup text");

    var fixed = [];
    var KEYWORDS = ["mockup", "motionfox"];

    for (var i = 1; i <= app.project.numItems; i++) {
        var it = app.project.item(i);
        if (!(it instanceof CompItem)) continue;

        // Match Screen precomps (original or duplicated)
        if (it.name.indexOf("Screen") !== 0) continue;

        for (var j = 1; j <= it.numLayers; j++) {
            var lyr = it.layer(j);
            var nameLower = lyr.name.toLowerCase();
            for (var k = 0; k < KEYWORDS.length; k++) {
                if (nameLower.indexOf(KEYWORDS[k]) > -1) {
                    if (lyr.enabled) {
                        lyr.enabled = false;
                        fixed.push(it.name + " #" + j + " " + lyr.name + " -> disabled");
                    } else {
                        fixed.push(it.name + " #" + j + " " + lyr.name + " (already disabled)");
                    }
                    break;
                }
            }
        }
    }

    app.endUndoGroup();

    var outFile = new File(OUT);
    outFile.open("w");
    outFile.encoding = "UTF-8";
    outFile.write("== Fix Mockup Text ==\n" + new Date().toString() + "\n\n");
    for (var m = 0; m < fixed.length; m++) outFile.write(fixed[m] + "\n");
    outFile.write("\nTotal: " + fixed.length + " layers affected");
    outFile.close();

    alert("Fixed " + fixed.length + " layers.\nDetails: " + OUT);
})();
