<template>
  <!-- #ifdef MP-WEIXIN -->
  <rich-text :class="['markdown-content', `markdown-${variant}`]" :nodes="html" />
  <!-- #endif -->
  <!-- #ifndef MP-WEIXIN -->
  <view :class="['markdown-content', `markdown-${variant}`]" v-html="html" />
  <!-- #endif -->
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'

const props = withDefaults(defineProps<{
  content?: string
  variant?: 'message' | 'source'
}>(), {
  content: '',
  variant: 'message',
})

const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  breaks: true,
})

const textStyle = 'font-size:14px;line-height:1.7;color:#2f2e32;'
const sourceTextStyle = 'font-size:14px;line-height:1.8;color:#475569;'

function blockTextStyle(): string {
  return props.variant === 'source' ? sourceTextStyle : textStyle
}

md.renderer.rules.paragraph_open = () => `<p style="margin:0 0 8px;${blockTextStyle()}">`
md.renderer.rules.bullet_list_open = () => '<ul style="margin:0 0 8px;padding-left:18px;">'
md.renderer.rules.ordered_list_open = () => '<ol style="margin:0 0 8px;padding-left:18px;">'
md.renderer.rules.list_item_open = () => `<li style="margin:0 0 4px;${blockTextStyle()}">`
md.renderer.rules.strong_open = () => '<strong style="font-weight:700;color:#5b21b6;">'
md.renderer.rules.em_open = () => '<em style="font-style:italic;">'
md.renderer.rules.blockquote_open = () => '<blockquote style="margin:8px 0;padding-left:12px;border-left:3px solid #5b21b6;color:#6b7280;">'
md.renderer.rules.code_inline = (tokens, idx) => {
  const content = md.utils.escapeHtml(tokens[idx].content)
  return `<code style="background:#f3f4f6;padding:2px 6px;border-radius:4px;font-size:13px;color:#374151;">${content}</code>`
}
md.renderer.rules.fence = (tokens, idx) => {
  const content = md.utils.escapeHtml(tokens[idx].content)
  return `<pre style="margin:8px 0;padding:12px;border-radius:8px;background:#f3f4f6;white-space:pre-wrap;word-break:break-word;overflow:auto;"><code style="font-size:13px;line-height:1.6;color:#374151;">${content}</code></pre>`
}
md.renderer.rules.heading_open = (tokens, idx) => {
  const tag = tokens[idx].tag
  const size = tag === 'h1' ? '18px' : tag === 'h2' ? '16px' : '15px'
  return `<${tag} style="margin:10px 0 6px;font-size:${size};line-height:1.45;font-weight:700;color:#2f2e32;">`
}
md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const token = tokens[idx]
  token.attrSet('target', '_blank')
  token.attrSet('rel', 'noopener noreferrer')
  token.attrSet('style', 'color:#5b21b6;text-decoration:underline;word-break:break-all;')
  return self.renderToken(tokens, idx, options)
}
md.renderer.rules.table_open = () => '<table style="width:100%;border-collapse:collapse;margin:8px 0;font-size:13px;">'
md.renderer.rules.th_open = () => '<th style="border:1px solid #e5e7eb;padding:6px 8px;text-align:left;font-weight:700;">'
md.renderer.rules.td_open = () => '<td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:left;">'

const html = computed(() => props.content ? md.render(props.content) : '')
</script>

<style scoped lang="scss">
.markdown-content {
  display: block;
  width: 100%;
  word-break: break-word;
}

.markdown-message {
  font-size: 0.875rem;
  line-height: 1.7;
  color: #2f2e32;
}

.markdown-source {
  font-size: 0.875rem;
  line-height: 1.8;
  color: #475569;
}
</style>