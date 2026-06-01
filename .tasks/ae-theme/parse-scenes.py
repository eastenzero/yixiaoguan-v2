import json, sys

data = json.load(open(r'F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\ae-scenes-real-structure.json', 'r', encoding='utf-8'))

# Summary table
print(f"{'SCENE':<12} {'屏幕':>4} {'背面':>6} {'Logo':>6} {'mov数':>5} {'时长':>5}  mov源文件")
print("─" * 90)

for s in data:
    # unique mov filenames
    mov_files = set()
    for m in s['bodyMovFiles']:
        mov_files.add(m['srcName'])
    
    screens = s['screenCount']
    back = "⚠背面" if s['hasPhoneBack'] else "✓"
    logo = "⚠logo" if s['hasLogoSuspect'] else "✓"
    dur = f"{s['duration']:.1f}s"
    
    print(f"{s['name']:<12} {screens:>4}屏 {back:>6} {logo:>6} {len(s['bodyMovFiles']):>5}  {dur:>5}  {', '.join(sorted(mov_files))}")

# Focus on dual-screen scenes
print("\n\n=== 双屏 SCENE (screenCount >= 2) ===\n")
for s in data:
    if s['screenCount'] < 2:
        continue
    print(f"\n{s['name']} | {s['screenCount']}屏 | {s['duration']:.1f}s | 背面={s['hasPhoneBack']}")
    
    print("  Screens:")
    for sc in s['screens']:
        print(f"    [{sc['index']}] {sc['name']} src={sc['srcName']} enabled={sc['enabled']}")
    for sc in s.get('preCompScreens', []):
        print(f"    [{sc['index']}] {sc['name']} (in {sc['preComp']}) src={sc['srcName']} enabled={sc['enabled']}")
    
    if s['phoneBackLayers']:
        print("  ⚠ Phone Back:")
        for pb in s['phoneBackLayers']:
            pc = f" (in {pb['preComp']})" if 'preComp' in pb else ""
            print(f"    [{pb['index']}] {pb['name']}{pc} src={pb['srcName']} enabled={pb['enabled']}")

    if '--full' in sys.argv:
        print("  All layers:")
        for l in s['allLayers']:
            marker = " " if l['enabled'] else "✗"
            print(f"    {marker} [{l['index']}] {l['name']} ({l['srcType']}) {l['srcName']}")
