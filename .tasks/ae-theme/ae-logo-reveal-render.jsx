/**
 * Render Quick Logo Reveal to MP4
 * Run after ae-logo-reveal-replace.jsx
 */
(function () {
    var OUTPUT_DIR = "F:\\Documents\\code\\yixiaoguan-v2\\.tasks\\ae-theme\\render-segments\\";
    var OUTPUT_FILE = "logo-reveal.avi";
    var proj = app.project;

    // Find the render comp
    var renderComp = null;
    for (var i = 1; i <= proj.numItems; i++) {
        var item = proj.item(i);
        if (item instanceof CompItem && item.name === "quick_logo_reveal_2160p") {
            renderComp = item;
            break;
        }
    }

    if (!renderComp) {
        alert("Render comp 'quick_logo_reveal_2160p' not found!");
        return;
    }

    // Clear existing render queue
    while (app.project.renderQueue.numItems > 0) {
        app.project.renderQueue.item(1).remove();
    }

    // Add to render queue
    var rqItem = app.project.renderQueue.items.add(renderComp);

    // Set output module (AVI for max quality, convert to MP4 via ffmpeg after)
    var om = rqItem.outputModule(1);
    var outputPath = OUTPUT_DIR + OUTPUT_FILE;

    // Create output directory
    var dir = new Folder(OUTPUT_DIR);
    if (!dir.exists) dir.create();

    om.file = new File(outputPath);

    alert("Render queued!\n\nComp: " + renderComp.name + "\nSize: " + renderComp.width + "x" + renderComp.height + "\nDuration: " + renderComp.duration.toFixed(1) + "s\nOutput: " + outputPath + "\n\nClick 'Render' in the Render Queue to start.\n\nAfter render, convert to MP4 with:\nffmpeg -i \"" + outputPath + "\" -c:v libx264 -crf 18 -pix_fmt yuv420p \"" + OUTPUT_DIR + "logo-reveal.mp4\"");
})();
