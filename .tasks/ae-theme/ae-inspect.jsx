/**
 * ae-inspect.jsx
 * 一次性导出 AE 项目结构到 JSON，供 Cascade 诊断
 *
 * 用法: AE > File > Scripts > Run Script File...
 * 输出: F:\Documents\code\yixiaoguan-v2\.tasks\ae-inspect-result.json
 */

var OUTPUT = "F:\\Documents\\code\\yixiaoguan-v2\\.tasks\\ae-inspect-result.json";

// ============================================================

function inspectLayer(layer, depth) {
    if (depth === undefined) depth = 0;
    var info = {
        index: layer.index,
        name: layer.name,
        enabled: layer.enabled,
        type: "unknown"
    };

    if (layer instanceof TextLayer) info.type = "text";
    else if (layer instanceof ShapeLayer) info.type = "shape";
    else if (layer instanceof CameraLayer) info.type = "camera";
    else if (layer instanceof LightLayer) info.type = "light";
    else if (layer instanceof AVLayer) info.type = "av";

    // source info
    if (layer.source) {
        info.sourceName = layer.source.name;
        if (layer.source instanceof CompItem) {
            info.sourceType = "comp";
            info.sourceCompId = layer.source.id;
        } else if (layer.source instanceof FootageItem) {
            info.sourceType = "footage";
            if (layer.source.mainSource instanceof SolidSource) {
                info.sourceType = "solid";
                try {
                    var c = layer.source.mainSource.color;
                    info.solidColor = [
                        Math.round(c[0] * 255),
                        Math.round(c[1] * 255),
                        Math.round(c[2] * 255)
                    ];
                } catch (e) { }
            }
        }
    }

    // effects
    try {
        if (layer.Effects && layer.Effects.numProperties > 0) {
            info.effects = [];
            for (var e = 1; e <= layer.Effects.numProperties; e++) {
                var fx = layer.Effects.property(e);
                var fxInfo = {
                    index: e,
                    name: fx.name,
                    matchName: fx.matchName,
                    enabled: fx.enabled,
                    numProps: fx.numProperties
                };
                // dump property names + values for first 10 props
                fxInfo.props = [];
                for (var p = 1; p <= Math.min(fx.numProperties, 10); p++) {
                    var prop = fx.property(p);
                    var pInfo = {
                        index: p,
                        name: prop.name,
                        matchName: prop.matchName
                    };
                    try {
                        pInfo.value = prop.value;
                    } catch (e2) {
                        pInfo.value = "(unreadable)";
                    }
                    fxInfo.props.push(pInfo);
                }
                info.effects.push(fxInfo);
            }
        }
    } catch (e) { }

    // text content
    if (layer instanceof TextLayer) {
        try {
            var td = layer.property("ADBE Text Properties").property("ADBE Text Document").value;
            info.textContent = td.text.substring(0, 100);
            info.textFillColor = [
                Math.round(td.fillColor[0] * 255),
                Math.round(td.fillColor[1] * 255),
                Math.round(td.fillColor[2] * 255)
            ];
            info.fontSize = td.fontSize;
        } catch (e) { }
    }

    return info;
}

function inspectComp(comp, depth) {
    if (depth === undefined) depth = 0;
    var result = {
        name: comp.name,
        id: comp.id,
        width: comp.width,
        height: comp.height,
        duration: comp.duration,
        numLayers: comp.numLayers,
        layers: []
    };

    for (var i = 1; i <= comp.numLayers; i++) {
        var layerInfo = inspectLayer(comp.layer(i), depth);

        // recurse into sub-comps (max depth 2)
        if (depth < 2 && comp.layer(i).source instanceof CompItem) {
            layerInfo.subComp = inspectComp(comp.layer(i).source, depth + 1);
        }

        result.layers.push(layerInfo);
    }

    return result;
}

// ============================================================
// Main
// ============================================================

var proj = app.project;
var output = {
    projectName: proj.file ? proj.file.name : "(unsaved)",
    numItems: proj.numItems,
    timestamp: (function () { var d = new Date(); return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2) + "T" + ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2); })(),
    compositions: {}
};

// 1. Inspect PREVIEW COMPS (main comp with all SCENEs)
for (var i = 1; i <= proj.numItems; i++) {
    if (proj.item(i) instanceof CompItem && proj.item(i).name === "PREVIEW COMPS") {
        output.compositions["PREVIEW COMPS"] = inspectComp(proj.item(i), 0);
        break;
    }
}

// 2. Inspect target SCENEs individually (depth=2 to see PreComp internals)
var targets = [1, 4, 5, 6, 8, 9, 10, 13, 15, 23, 24, 25];
for (var t = 0; t < targets.length; t++) {
    var sn = targets[t];
    var padded = sn < 10 ? "0" + sn : "" + sn;
    var sceneName = "SCENE_" + padded;
    for (var j = 1; j <= proj.numItems; j++) {
        if (proj.item(j) instanceof CompItem && proj.item(j).name === sceneName) {
            output.compositions[sceneName] = inspectComp(proj.item(j), 0);
            break;
        }
    }
}

// 3. Inspect DEMO EXPORT v2 if exists
for (var k = 1; k <= proj.numItems; k++) {
    if (proj.item(k) instanceof CompItem && proj.item(k).name === "DEMO EXPORT v2") {
        output.compositions["DEMO EXPORT v2"] = inspectComp(proj.item(k), 0);
        break;
    }
}

// Write JSON
var jsonStr = "";
try {
    // ExtendScript has no JSON.stringify, manual serialize
    jsonStr = toJSON(output);
} catch (e) {
    jsonStr = '{"error": "' + e.toString().replace(/"/g, '\\"') + '"}';
}

var file = new File(OUTPUT);
file.open("w");
file.encoding = "UTF-8";
file.write(jsonStr);
file.close();

alert("✅ 诊断数据已导出\n" + OUTPUT + "\n\n共检查 " + targets.length + " 个 SCENE + PREVIEW COMPS");

// ============================================================
// Minimal JSON serializer for ExtendScript (no native JSON)
// ============================================================

function toJSON(obj) {
    if (obj === null || obj === undefined) return "null";
    if (typeof obj === "boolean") return obj ? "true" : "false";
    if (typeof obj === "number") {
        if (isNaN(obj)) return "null";
        return String(obj);
    }
    if (typeof obj === "string") {
        return '"' + obj.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n').replace(/\r/g, '\\r').replace(/\t/g, '\\t') + '"';
    }
    if (obj instanceof Array) {
        var items = [];
        for (var i = 0; i < obj.length; i++) {
            items.push(toJSON(obj[i]));
        }
        return "[" + items.join(",") + "]";
    }
    if (typeof obj === "object") {
        var pairs = [];
        for (var key in obj) {
            if (obj.hasOwnProperty(key)) {
                pairs.push('"' + key + '":' + toJSON(obj[key]));
            }
        }
        return "{" + pairs.join(",") + "}";
    }
    return "null";
}
