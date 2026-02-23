<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  xml: string
}>()

const highlightedXml = computed(() => {
  if (!props.xml) return ''

  return props.xml
    // Escape HTML entities first
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // XML declaration
    .replace(
      /(&lt;\?xml.*?\?&gt;)/g,
      '<span class="xml-declaration">$1</span>'
    )
    // Comments
    .replace(
      /(&lt;!--[\s\S]*?--&gt;)/g,
      '<span class="xml-comment">$1</span>'
    )
    // Closing tags
    .replace(
      /(&lt;\/)([\w:.-]+)(&gt;)/g,
      '<span class="xml-bracket">$1</span><span class="xml-tag">$2</span><span class="xml-bracket">$3</span>'
    )
    // Self-closing tags
    .replace(
      /(&lt;)([\w:.-]+)((?:\s+[\w:.-]+="[^"]*")*\s*\/&gt;)/g,
      '<span class="xml-bracket">$1</span><span class="xml-tag">$2</span>$3'
    )
    // Opening tags
    .replace(
      /(&lt;)([\w:.-]+)((?:\s+[\w:.-]+="[^"]*")*\s*&gt;)/g,
      '<span class="xml-bracket">$1</span><span class="xml-tag">$2</span>$3'
    )
    // Attributes
    .replace(
      /([\w:.-]+)(=)(&quot;|")([^"]*?)(&quot;|")/g,
      '<span class="xml-attr-name">$1</span><span class="xml-bracket">$2</span><span class="xml-attr-value">"$4"</span>'
    )
})
</script>

<template>
  <div class="xml-viewer">
    <pre class="xml-pre"><code v-html="highlightedXml"></code></pre>
  </div>
</template>

<style scoped>
.xml-viewer {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.xml-pre {
  margin: 0;
  padding: 14px;
  background: var(--color-bg);
  font-family: var(--font-mono);
  font-size: 0.78rem;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre;
}

:deep(.xml-declaration) {
  color: var(--color-text-muted);
}

:deep(.xml-comment) {
  color: var(--color-text-muted);
  font-style: italic;
}

:deep(.xml-bracket) {
  color: var(--color-text-muted);
}

:deep(.xml-tag) {
  color: var(--color-primary);
  font-weight: 600;
}

:deep(.xml-attr-name) {
  color: var(--color-purple);
}

:deep(.xml-attr-value) {
  color: var(--color-success);
}
</style>
