/**
 * ae-list-scenes-timeline.jsx
 * List all SCENE layers in PREVIEW COMPS with timeline position and screen count
 * Helps user pick the best-animated scenes for each layout type
 */
(function () {
    function findCompByName(name) {
        for (var i = 1; i <= app.project.numItems; i++) {
            var it = app.project.item(i);
            if (it instanceof CompItem && it.name === name) return it;
        }
        return null;
    }

    function countScreens(comp) {
        var screens = 0;
        for (var i = 1; i <= comp.numLayers; i++) {
            var lyr = comp.layer(i);
            var name = lyr.name.toLowerCase();
            if (name.indexOf("screen ") > -1 || name.indexOf("screen_") > -1) {
                var lyrSrc = null;
                try { lyrSrc = lyr.source; } catch (e) { }
                if (lyrSrc instanceof CompItem) screens++;
            }
        }
        return screens;
    }

    function countScreensDeep(comp) {
        // Check direct screens first
        var direct = countScreens(comp);
        if (direct > 0) return direct;
        // Check one level deep (PreComps layers)
        for (var i = 1; i <= comp.numLayers; i++) {
            var lyr = comp.layer(i);
            var lyrSrc = null;
            try { lyrSrc = lyr.source; } catch (e) { }
            if (lyrSrc instanceof CompItem) {
                var sub = countScreens(lyrSrc);
                direct += sub;
            }
        }
        return direct;
    }

    function toTimecode(seconds) {
        var m = Math.floor(seconds / 60);
        var s = seconds - m * 60;
        return m + ":" + (s < 10 ? "0" : "") + s.toFixed(1);
    }

    var previewComp = findCompByName("PREVIEW COMPS");
    if (!previewComp) { alert("PREVIEW COMPS not found"); return; }

    var singles = [];
    var duals = [];
    var others = [];

    for (var i = 1; i <= previewComp.numLayers; i++) {
        var lyr = previewComp.layer(i);
        if (lyr.name.indexOf("SCENE_") !== 0) continue;

        var lyrSrc = null;
        try { lyrSrc = lyr.source; } catch (e) { }
        if (!(lyrSrc instanceof CompItem)) continue;

        var inTime = lyr.inPoint;
        var outTime = lyr.outPoint;
        var dur = outTime - inTime;
        var screenCount = countScreensDeep(lyrSrc);

        var line = lyr.name
            + " | " + toTimecode(inTime) + " - " + toTimecode(outTime)
            + " (" + dur.toFixed(1) + "s)"
            + " | " + screenCount + " screen"
            + (screenCount !== 1 ? "s" : "")
            + " | " + (lyr.enabled ? "ON" : "OFF");

        if (screenCount === 1) singles.push(line);
        else if (screenCount >= 2) duals.push(line);
        else others.push(line);
    }

    var msg = "== PREVIEW COMPS Scene Map ==\n\n";

    msg += "-- SINGLE SCREEN (" + singles.length + ") --\n";
    for (var s = 0; s < singles.length; s++) msg += singles[s] + "\n";

    msg += "\n-- DUAL+ SCREEN (" + duals.length + ") --\n";
    for (var d = 0; d < duals.length; d++) msg += duals[d] + "\n";

    msg += "\n-- OTHER/UNKNOWN (" + others.length + ") --\n";
    for (var o = 0; o < others.length; o++) msg += others[o] + "\n";

    msg += "\nScrub timeline to compare animations, pick favorites!";
    alert(msg);
})();
