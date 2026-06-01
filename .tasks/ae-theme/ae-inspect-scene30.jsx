/**
 * ae-inspect-scene30.jsx
 * Drill into SCENE_30 to find Screen precomps and Text Holder
 */
(function () {
    function findCompByName(name) {
        for (var i = 1; i <= app.project.numItems; i++) {
            var it = app.project.item(i);
            if (it instanceof CompItem && it.name === name) return it;
        }
        return null;
    }

    function dumpComp(comp, indent) {
        if (!indent) indent = "";
        var lines = [];
        lines.push(indent + comp.name + " (" + comp.width + "x" + comp.height + ", " + comp.numLayers + " layers):");
        for (var i = 1; i <= comp.numLayers; i++) {
            var lyr = comp.layer(i);
            var info = indent + "  #" + i + " [" + (lyr.enabled ? " " : "x") + "] " + lyr.name;
            var lyrSrc = null;
            try { lyrSrc = lyr.source; } catch (e) { }
            if (lyrSrc != null) {
                if (lyrSrc instanceof CompItem) {
                    info += " [PreComp " + lyrSrc.width + "x" + lyrSrc.height + "]";
                    lines.push(info);
                    // recurse one level
                    var sub = dumpComp(lyrSrc, indent + "    ");
                    lines.push(sub);
                    continue;
                } else if (lyrSrc instanceof FootageItem) {
                    try {
                        if (lyrSrc.mainSource instanceof SolidSource) {
                            info += " [Solid " + lyrSrc.width + "x" + lyrSrc.height + "]";
                        } else if (lyrSrc.file) {
                            info += " [File: " + lyrSrc.file.name + " " + lyrSrc.width + "x" + lyrSrc.height + "]";
                        } else {
                            info += " [Footage: " + lyrSrc.name + "]";
                        }
                    } catch (e) { info += " [Footage?]"; }
                }
            } else {
                info += " [NoSource]";
            }
            lines.push(info);
        }
        return lines.join("\n");
    }

    var comp = findCompByName("SCENE_30");
    if (!comp) { alert("SCENE_30 not found"); return; }

    var result = dumpComp(comp, "");
    alert(result);
})();
