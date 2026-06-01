/**
 * ae-render-5scenes.jsx
 * Render 5 primary SCENE segments from PREVIEW COMPS
 * S28 swapped to S27 per user preference
 *
 * Time allocation (director, 34s total):
 *   S23=6s, S11=8s, S18=8s, S27=6s, S30=6s
 *
 * Output: H.264 mp4 per director spec
 * Note: AE render queue outputs AVI/MOV; ffmpeg converts to H.264 mp4
 */
(function () {
    var REPO = "F:\\Documents\\code\\yixiaoguan-v2";
    var OUTPUT_DIR = REPO + "\\.tasks\\ae-theme\\render-segments";
    var OUT = REPO + "\\.tasks\\ae-theme\\render-queue-result.txt";

    var TARGET_SCENES = [
        "SCENE_23", "SCENE_11", "SCENE_18", "SCENE_27", "SCENE_30"
    ];

    var proj = app.project;

    var mainComp = null;
    for (var i = 1; i <= proj.numItems; i++) {
        if (proj.item(i) instanceof CompItem && proj.item(i).name === "PREVIEW COMPS") {
            mainComp = proj.item(i);
            break;
        }
    }

    if (!mainComp) { alert("PREVIEW COMPS not found"); return; }

    var segments = [];
    for (var s = 0; s < TARGET_SCENES.length; s++) {
        var sceneName = TARGET_SCENES[s];
        for (var j = 1; j <= mainComp.numLayers; j++) {
            if (mainComp.layer(j).name === sceneName) {
                var lyr = mainComp.layer(j);
                segments.push({
                    name: sceneName,
                    inPoint: lyr.inPoint,
                    outPoint: lyr.outPoint,
                    duration: lyr.outPoint - lyr.inPoint
                });
                break;
            }
        }
    }

    if (segments.length === 0) { alert("No target SCENE layers found"); return; }

    var outFolder = new Folder(OUTPUT_DIR);
    if (!outFolder.exists) outFolder.create();

    // Output filenames per director spec
    var OUTPUT_NAMES = {
        "SCENE_23": "ae-scene-23",
        "SCENE_11": "ae-scene-11",
        "SCENE_18": "ae-scene-18",
        "SCENE_27": "ae-scene-27",
        "SCENE_30": "ae-scene-30"
    };

    var lines = [];
    lines.push("== Render Queue: 5 Scenes (Final) ==");
    lines.push("Generated: " + new Date().toString());
    lines.push("Time budget: S23=6s, S11=8s, S18=8s, S27=6s, S30=6s (34s total)");
    lines.push("");

    for (var m = 0; m < segments.length; m++) {
        var seg = segments[m];
        var rqi = proj.renderQueue.items.add(mainComp);
        rqi.timeSpanStart = seg.inPoint;
        rqi.timeSpanDuration = seg.duration;

        var om = rqi.outputModule(1);
        try { om.applyTemplate("Lossless"); } catch (e) { }
        var outName = OUTPUT_NAMES[seg.name] || seg.name;
        var outFile = OUTPUT_DIR + "\\" + outName + ".avi";
        om.file = new File(outFile);

        lines.push(seg.name + " | " + seg.inPoint.toFixed(1) + "s - " + seg.outPoint.toFixed(1) + "s"
            + " (" + seg.duration.toFixed(1) + "s) -> " + outName + ".avi");
    }

    lines.push("");
    lines.push("Total: " + segments.length + " segments queued");
    lines.push("");
    lines.push("After render, convert to H.264 mp4:");
    lines.push("");
    var names = ["ae-scene-23", "ae-scene-11", "ae-scene-18", "ae-scene-27", "ae-scene-30"];
    for (var n = 0; n < names.length; n++) {
        lines.push("ffmpeg -i \"" + OUTPUT_DIR + "\\" + names[n] + ".avi\" -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -r 30 \"" + OUTPUT_DIR + "\\" + names[n] + ".mp4\"");
    }
    lines.push("");
    lines.push("Steps:");
    lines.push("1. Ctrl+Alt+0 -> Render Queue");
    lines.push("2. Click Render");
    lines.push("3. Run ffmpeg commands above");

    var outFile = new File(OUT);
    outFile.open("w");
    outFile.encoding = "UTF-8";
    outFile.write(lines.join("\n"));
    outFile.close();

    alert("Queued " + segments.length + " segments!\nDetails: " + OUT);
})();
