/**
 * Inspect Quick Logo Reveal template structure
 * Run after opening quick_logo_reveal.aep in AE
 */
(function () {
    var OUT = "F:\\Documents\\code\\yixiaoguan-v2\\.tasks\\ae-theme\\logo-reveal-inspect.txt";
    var lines = [];
    var proj = app.project;

    lines.push("=== Quick Logo Reveal Template Inspection ===");
    lines.push("Project items: " + proj.numItems);
    lines.push("");

    for (var i = 1; i <= proj.numItems; i++) {
        var item = proj.item(i);
        var type = "";
        if (item instanceof CompItem) type = "COMP";
        else if (item instanceof FolderItem) type = "FOLDER";
        else if (item instanceof FootageItem) type = "FOOTAGE";
        else type = "OTHER";

        var info = "#" + i + " [" + type + "] " + item.name;
        if (item instanceof CompItem) {
            info += " (" + item.width + "x" + item.height + ", " + item.duration.toFixed(1) + "s, " + item.numLayers + " layers)";
        }
        if (item instanceof FootageItem && item.file) {
            info += " => " + item.file.fsName;
        }
        lines.push(info);

        // Dump layers for compositions
        if (item instanceof CompItem) {
            for (var j = 1; j <= item.numLayers; j++) {
                var lyr = item.layer(j);
                var lInfo = "  L" + j + " [" + (lyr.enabled ? "ON" : "off") + "] " + lyr.name;

                try {
                    if (lyr.source && lyr.source instanceof CompItem) {
                        lInfo += " [PreComp " + lyr.source.width + "x" + lyr.source.height + "]";
                    } else if (lyr.source && lyr.source instanceof FootageItem) {
                        lInfo += " [Footage";
                        if (lyr.source.file) lInfo += " " + lyr.source.file.name;
                        lInfo += "]";
                    }
                } catch (e) {}

                // Check if layer name hints at logo placeholder
                var n = lyr.name.toLowerCase();
                if (n.indexOf("logo") >= 0 || n.indexOf("your") >= 0 || n.indexOf("place") >= 0 || n.indexOf("edit") >= 0) {
                    lInfo += " <<< LOGO PLACEHOLDER?";
                }
                lines.push(lInfo);
            }
            lines.push("");
        }
    }

    // Write to file
    var f = new File(OUT);
    f.encoding = "UTF-8";
    f.open("w");
    f.write(lines.join("\n"));
    f.close();
    alert("Inspection saved to:\n" + OUT);
})();
