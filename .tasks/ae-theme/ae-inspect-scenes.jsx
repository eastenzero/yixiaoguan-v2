/**
 * ae-inspect-scenes.jsx
 * 探查所有 30 个 SCENE 的真实结构：
 *   - 有几个 Screen 占位（正面屏幕）
 *   - 有无 Phone Back 层（背面机身）
 *   - 机身 .mov 源文件名（判断正/背面）
 *   - 是否有 logo 相关层
 *
 * 输出: .tasks/ae-theme/ae-scenes-real-structure.json
 */

var OUTPUT = "F:\\Documents\\code\\yixiaoguan-v2\\.tasks\\ae-theme\\ae-scenes-real-structure.json";
var proj = app.project;
var results = [];

for (var sceneNum = 1; sceneNum <= 30; sceneNum++) {
    var padded = sceneNum < 10 ? "0" + sceneNum : "" + sceneNum;
    var sceneName = "SCENE_" + padded;

    // 找 SCENE comp
    var sceneComp = null;
    for (var i = 1; i <= proj.numItems; i++) {
        if (proj.item(i) instanceof CompItem && proj.item(i).name === sceneName) {
            sceneComp = proj.item(i);
            break;
        }
    }
    if (!sceneComp) continue;

    var info = {
        name: sceneName,
        duration: sceneComp.duration,
        numLayers: sceneComp.numLayers,
        screens: [],           // Screen 01, Screen 02, ...
        phoneBackLayers: [],   // Phone Back 层
        bodyMovFiles: [],      // 机身 .mov 源文件
        suspectLogo: [],       // 可能有 logo 的层
        allLayers: []          // 全部图层概览
    };

    for (var j = 1; j <= sceneComp.numLayers; j++) {
        var lyr = sceneComp.layer(j);
        var lname = lyr.name;
        var srcName = lyr.source ? lyr.source.name : "";
        var srcType = "";
        if (lyr.source instanceof CompItem) srcType = "comp";
        else if (lyr.source instanceof FootageItem) srcType = "footage";

        // 全部图层
        info.allLayers.push({
            index: j,
            name: lname,
            enabled: lyr.enabled,
            srcName: srcName,
            srcType: srcType
        });

        // Screen 占位
        if (lname.indexOf("Screen") > -1 && lname.indexOf("Camera") === -1 && lname.indexOf("Frame") === -1) {
            info.screens.push({ index: j, name: lname, srcName: srcName, enabled: lyr.enabled });
        }

        // Phone Back
        if (lname.toLowerCase().indexOf("back") > -1 || lname.toLowerCase().indexOf("phone back") > -1) {
            info.phoneBackLayers.push({ index: j, name: lname, srcName: srcName, enabled: lyr.enabled });
        }

        // 机身 .mov（5 色层 + Matte + Shadow）
        if (srcName.indexOf(".mov") > -1) {
            info.bodyMovFiles.push({ index: j, name: lname, srcName: srcName, enabled: lyr.enabled });
        }

        // 可能有 logo 的层
        var lower = (lname + " " + srcName).toLowerCase();
        if (lower.indexOf("logo") > -1 || lower.indexOf("apple") > -1 || lower.indexOf("brand") > -1) {
            info.suspectLogo.push({ index: j, name: lname, srcName: srcName, enabled: lyr.enabled });
        }
    }

    // 递归检查 PreComp 子合成内部（SCENE_23~30 类型）
    info.preCompScreens = [];
    for (var k = 1; k <= sceneComp.numLayers; k++) {
        var pcLyr = sceneComp.layer(k);
        if (pcLyr.source instanceof CompItem && pcLyr.name.indexOf("PreComp") > -1) {
            var subComp = pcLyr.source;
            for (var m = 1; m <= subComp.numLayers; m++) {
                var subLyr = subComp.layer(m);
                var subName = subLyr.name;
                var subSrc = subLyr.source ? subLyr.source.name : "";

                if (subName.indexOf("Screen") > -1 && subName.indexOf("Camera") === -1 && subName.indexOf("Frame") === -1) {
                    info.preCompScreens.push({
                        preComp: pcLyr.name,
                        index: m,
                        name: subName,
                        srcName: subSrc,
                        enabled: subLyr.enabled
                    });
                }
                if (subName.toLowerCase().indexOf("back") > -1) {
                    info.phoneBackLayers.push({
                        preComp: pcLyr.name,
                        index: m,
                        name: subName,
                        srcName: subSrc,
                        enabled: subLyr.enabled
                    });
                }
            }
        }
    }

    info.screenCount = info.screens.length + info.preCompScreens.length;
    info.hasPhoneBack = info.phoneBackLayers.length > 0;
    info.hasLogoSuspect = info.suspectLogo.length > 0;

    results.push(info);
}

// 写 JSON
var file = new File(OUTPUT);
file.open("w");
file.encoding = "UTF-8";
file.write(toJSON(results));
file.close();

// 摘要 alert
var summary = "SCENE 探查完成 — " + results.length + " 个\n\n";
summary += "场景 | 屏幕数 | 背面? | Logo? | .mov数\n";
summary += "─────────────────────────────────────\n";
for (var r = 0; r < results.length; r++) {
    var s = results[r];
    summary += s.name + " | " + s.screenCount + "屏 | " +
               (s.hasPhoneBack ? "⚠有背面" : "✓正面") + " | " +
               (s.hasLogoSuspect ? "⚠logo" : "✓") + " | " +
               s.bodyMovFiles.length + "个mov\n";
}
summary += "\n详细 JSON: " + OUTPUT;
alert(summary);


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
        for (var i = 0; i < obj.length; i++) items.push(toJSON(obj[i]));
        return "[" + items.join(",") + "]";
    }
    if (typeof obj === "object") {
        var pairs = [];
        for (var key in obj) {
            if (obj.hasOwnProperty(key)) pairs.push('"' + key + '":' + toJSON(obj[key]));
        }
        return "{" + pairs.join(",") + "}";
    }
    return "null";
}
