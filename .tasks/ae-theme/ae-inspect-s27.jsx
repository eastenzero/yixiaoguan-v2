/**
 * ae-inspect-s27.jsx - Diagnose SCENE_27 screen structure
 */
(function () {
    var REPO = "F:\\Documents\\code\\yixiaoguan-v2";
    var OUT = REPO + "\\.tasks\\ae-theme\\inspect-s27-result.txt";
    var lines = [];

    function dumpComp(comp, indent, depth) {
        if (depth > 5) return;
        for (var i = 1; i <= comp.numLayers; i++) {
            var lyr = comp.layer(i);
            var src = null;
            try { src = lyr.source; } catch(e) {}
            var info = indent + "#" + i + " [" + (lyr.enabled ? "ON" : "off") + "] \"" + lyr.name + "\"";
            if (src instanceof CompItem) {
                info += " [PreComp " + src.width + "x" + src.height + " " + src.numLayers + "L]";
                lines.push(info);
                dumpComp(src, indent + "  ", depth + 1);
            } else if (src) {
                info += " [Footage " + src.width + "x" + src.height + " " + src.name + "]";
                lines.push(info);
            } else {
                info += " [NoSource]";
                lines.push(info);
            }
        }
    }

    var comp = null;
    for (var i = 1; i <= app.project.numItems; i++) {
        var it = app.project.item(i);
        if (it instanceof CompItem && it.name === "SCENE_27") { comp = it; break; }
    }

    if (!comp) { alert("SCENE_27 not found"); return; }

    lines.push("SCENE_27 (" + comp.width + "x" + comp.height + ", " + comp.numLayers + " layers)");
    dumpComp(comp, "  ", 0);

    var outFile = new File(OUT);
    outFile.open("w");
    outFile.encoding = "UTF-8";
    outFile.write(lines.join("\n"));
    outFile.close();
    alert("Done! " + OUT);
})();
