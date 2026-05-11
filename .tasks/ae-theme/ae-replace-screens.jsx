/**
 * ae-replace-screens.jsx
 * 医小管演示视频 T10 — 把 4 个 SCENE 的 placeholder 屏幕替换为医小管真截图
 *
 * 模板: App Promo Phone 14 Pro Mockup Pack (Videohive 40526693)
 * 前置: 已跑过 ae-light-theme.jsx（亮色主题已应用）
 *
 * 用法: AE > File > Scripts > Run Script File... > 选本文件
 * 回滚: Ctrl+Z（整体在一个 Undo Group 内）
 *
 * 兼容性: CS6 ~ CC 2024（仅使用稳定 ExtendScript API）
 *
 * ✦ 同时 dump 每个 SCENE 的图层结构到 alert，方便排查 Bug 2（logo 漏网）
 */

// ============================================================
// 路径配置（根据实际仓库位置调整）
// ============================================================
var REPO_ROOT = "F:\\Documents\\code\\yixiaoguan-v2";
var TEA_DIR = REPO_ROOT + "\\.tasks\\teacher-ui-audit-2026-05-11\\after-avatar";
var STU_DIR = REPO_ROOT + "\\.tasks\\student-ui-audit-2026-05-11\\after-avatar";

// 替换映射表：(剧本 04 §2.2 决策)
// SCENE_01: 学生端 home 首屏 单屏
// SCENE_05: 学生端 chat 流式回答 单屏
// SCENE_10: 学生端 chat × 教师端 dashboard 双屏
// SCENE_13: 学生端 services × 教师端 analytics 双屏
var REPLACEMENTS = [
    { scene: "SCENE_01", screen: "Screen 01", image: STU_DIR + "\\02-home.png", role: "学生 home" },
    { scene: "SCENE_05", screen: "Screen 01", image: STU_DIR + "\\04-chat-with-conv.png", role: "学生 chat 流答" },
    { scene: "SCENE_10", screen: "Screen 01", image: STU_DIR + "\\03-chat-empty.png", role: "SCENE_10 左·学生 chat" },
    { scene: "SCENE_10", screen: "Screen 02", image: TEA_DIR + "\\02-dashboard.png", role: "SCENE_10 右·教师 dashboard" },
    { scene: "SCENE_13", screen: "Screen 01", image: STU_DIR + "\\06-services.png", role: "SCENE_13 左·学生 services" },
    { scene: "SCENE_13", screen: "Screen 02", image: TEA_DIR + "\\09-analytics.png", role: "SCENE_13 右·教师 analytics" }
];

// ============================================================
// 辅助函数
// ============================================================
function findCompByKeyword(keyword) {
    for (var i = 1; i <= app.project.numItems; i++) {
        var item = app.project.item(i);
        if (item instanceof CompItem && item.name.toLowerCase().indexOf(keyword.toLowerCase()) > -1) {
            return item;
        }
    }
    return null;
}

function findLayerByKeyword(comp, keyword) {
    for (var i = 1; i <= comp.numLayers; i++) {
        if (comp.layer(i).name.toLowerCase().indexOf(keyword.toLowerCase()) > -1) {
            return comp.layer(i);
        }
    }
    return null;
}

function dumpLayers(comp) {
    var lines = [];
    for (var i = 1; i <= comp.numLayers; i++) {
        var l = comp.layer(i);
        var marker = l.enabled ? " " : "✗"; // ✗ = disabled
        var srcInfo = "";
        if (l.source) {
            if (l.source instanceof CompItem) srcInfo = "[comp] " + l.source.name;
            else if (l.source instanceof FootageItem) srcInfo = "[footage] " + l.source.name;
            else srcInfo = "[?] " + l.source.name;
        }
        lines.push("  " + marker + " #" + l.index + " " + l.name + " " + srcInfo);
    }
    return lines.join("\n");
}

function importAndReplace(layer, imagePath) {
    var file = new File(imagePath);
    if (!file.exists) {
        return { ok: false, error: "file not found: " + imagePath };
    }
    try {
        var importOptions = new ImportOptions(file);
        var item = app.project.importFile(importOptions);
        if (!item) return { ok: false, error: "importFile returned null" };
        layer.replaceSource(item, false);
        return { ok: true, itemName: item.name };
    } catch (e) {
        return { ok: false, error: String(e) };
    }
}

// ============================================================
// 主流程
// ============================================================
app.beginUndoGroup("Replace SCENE screens with yixiaoguan UI captures");

var report = [];
var sceneLayerDumps = {}; // sceneName -> layer dump string（去重）

for (var i = 0; i < REPLACEMENTS.length; i++) {
    var r = REPLACEMENTS[i];
    var comp = findCompByKeyword(r.scene);
    if (!comp) {
        report.push({ ok: false, role: r.role, error: "scene comp not found: " + r.scene });
        continue;
    }

    // dump 图层结构（仅 dump 一次/scene）
    if (!sceneLayerDumps[r.scene]) {
        sceneLayerDumps[r.scene] = "── " + comp.name + " 图层结构 ──\n" + dumpLayers(comp);
    }

    var layer = findLayerByKeyword(comp, r.screen);
    if (!layer) {
        report.push({
            ok: false, role: r.role,
            error: "screen layer not found: " + r.screen + " in " + comp.name
        });
        continue;
    }

    var result = importAndReplace(layer, r.image);
    report.push({
        ok: result.ok, role: r.role,
        comp: comp.name, layer: layer.name,
        replaced_with: result.itemName,
        error: result.error,
        image: r.image
    });
}

app.endUndoGroup();

// ============================================================
// 报告
// ============================================================
var msg = "✦ 屏幕替换完成 ✦\n\n── 替换结果 ──\n";
for (var j = 0; j < report.length; j++) {
    var rp = report[j];
    msg += (rp.ok ? "✓ " : "✗ ") + rp.role + "\n";
    if (rp.ok) {
        msg += "    [" + rp.comp + " > " + rp.layer + "] ← " + rp.replaced_with + "\n";
    } else {
        msg += "    错误: " + rp.error + "\n";
    }
}

msg += "\n── 4 个 SCENE 图层结构（用于排查 Bug 2 logo） ──\n";
for (var k in sceneLayerDumps) {
    msg += "\n" + sceneLayerDumps[k] + "\n";
}

msg += "\n如需回滚: Ctrl+Z";

alert(msg);
