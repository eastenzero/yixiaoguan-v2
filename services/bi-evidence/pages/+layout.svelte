<svelte:head>
  <link rel="stylesheet" href="/bi/yxg-theme.css?v=20260510c" />
</svelte:head>

<script>
  import '@evidence-dev/tailwind/fonts.css';
  import '../app.css';
  import { EvidenceDefaultLayout } from '@evidence-dev/core-components';
  export let data;
</script>

<EvidenceDefaultLayout {data}>
  <slot slot="content" />
</EvidenceDefaultLayout>
