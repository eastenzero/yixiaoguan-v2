# 医小管 · 内测大屏 (独立页)

**地址**：https://yxg.xiaoguan.site/wall/

**栈**：纯 HTML + CSS + vanilla JS + ECharts (CDN)，**0 构建步骤**。

## 文件

```
wall-standalone/
├── index.html                # 报头 + 3 段落 + 页脚
├── assets/
│   ├── wall-tokens.css       # 米色画报设计令牌 (从 yxg-theme.css 抽出)
│   ├── wall.css              # 大屏布局/组件样式 + 1080p/2K/4K 三档自适应
│   ├── wall.js               # fetch + 时钟 + 渲染 + count-up + ECharts 折线
│   └── echarts.min.js        # 本地化 ECharts (避免 CDN 抖动)
└── README.md                 # 本文件
```

## 数据流

1. `scripts/wall_export.py` 直连 postgres → 输出 `/var/www/yixiaoguan/wall/data.json`
2. systemd timer (`yxg-wall-export.timer`) 每 5 分钟跑一次
3. 前端 `wall.js` 在 load 时 fetch + 每 5 分钟 setInterval 重新 fetch

## 本地预览

无须启 dev server，直接用浏览器打开 `index.html`（注意 `data.json` 需要先准备一份在同目录或修改 `wall.js` 的 `DATA_URL`）。

或者用任意静态 server：
```
python3 -m http.server 8888
# → http://localhost:8888/
```

## 部署

```
rsync -av --delete services/wall-standalone/ tx-new:/var/www/yixiaoguan/wall/
ssh tx-new "sudo chown -R www-data:www-data /var/www/yixiaoguan/wall"
```

nginx 已在 `yxg.xiaoguan.site` 加 `location /wall/`，无须额外配置。
