<script>
  import '@evidence-dev/tailwind/fonts.css';
  import '../../app.css';
  import { onMount } from 'svelte';
  export let data;

  // 强制大屏页 dark 主题（让 Evidence chart 自动适配深色）
  onMount(() => {
    const html = document.documentElement;
    const prevTheme = html.getAttribute('data-theme');
    html.setAttribute('data-theme', 'dark');
    return () => {
      if (prevTheme) html.setAttribute('data-theme', prevTheme);
      else html.removeAttribute('data-theme');
    };
  });
</script>

<svelte:head>
  <link rel="stylesheet" href="/bi/yxg-wall.css" />
  <meta http-equiv="refresh" content="300" />
  <title>医小管 · 内测大屏</title>
</svelte:head>

<slot />

<style>
  :global(body),
  :global(html),
  :global(.evidence-default-layout),
  :global(.evidence-default-layout > div) {
    background: #0A0A0F !important;
  }
  /* 隐藏 Evidence 默认 sidebar / header */
  :global(.evidence-default-layout aside),
  :global(.evidence-default-layout header),
  :global(.evidence-default-layout nav) {
    display: none !important;
  }
  :global(.evidence-default-layout main) {
    padding: 0 !important;
    margin: 0 !important;
    max-width: none !important;
  }
  /* 强制图表卡片背景与大屏一致 */
  :global(.wall-card .echarts-for-react) {
    background: transparent !important;
  }
</style>
