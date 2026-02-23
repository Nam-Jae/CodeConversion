<script setup lang="ts">
import { ref } from 'vue'

const isDark = ref(true)

function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
}
</script>

<template>
  <div class="app" :class="{ dark: isDark }">
    <header class="navbar">
      <div class="navbar-inner">
        <router-link to="/" class="logo">
          <span class="logo-icon">&#x2B21;</span>
          <span class="logo-text">CodeConversion <sup>v1.1</sup></span>
        </router-link>
        <nav class="nav-links">
          <router-link to="/" class="nav-link">
            <span class="nav-icon">&#x2302;</span>
            홈
          </router-link>
          <router-link to="/upload" class="nav-link">
            <span class="nav-icon">&#x2B06;</span>
            업로드
          </router-link>
        </nav>
        <button class="theme-toggle" @click="toggleTheme" :title="isDark ? '라이트 모드' : '다크 모드'">
          {{ isDark ? '&#9788;' : '&#9790;' }}
        </button>
      </div>
    </header>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style>
:root {
  --color-bg: #ffffff;
  --color-bg-secondary: #f5f7fa;
  --color-bg-tertiary: #ebeef3;
  --color-surface: #ffffff;
  --color-surface-hover: #f0f2f5;
  --color-border: #dde1e7;
  --color-text: #1a1d23;
  --color-text-secondary: #5f6b7a;
  --color-text-muted: #8b95a5;
  --color-primary: #3b82f6;
  --color-primary-hover: #2563eb;
  --color-primary-soft: rgba(59, 130, 246, 0.1);
  --color-success: #10b981;
  --color-success-soft: rgba(16, 185, 129, 0.1);
  --color-warning: #f59e0b;
  --color-warning-soft: rgba(245, 158, 11, 0.1);
  --color-danger: #ef4444;
  --color-danger-soft: rgba(239, 68, 68, 0.1);
  --color-purple: #8b5cf6;
  --color-purple-soft: rgba(139, 92, 246, 0.1);
  --color-gray: #6b7280;
  --color-gray-soft: rgba(107, 114, 128, 0.1);
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.12);
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --font-mono: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
}

.dark {
  --color-bg: #0f1117;
  --color-bg-secondary: #161922;
  --color-bg-tertiary: #1e2230;
  --color-surface: #1a1e2b;
  --color-surface-hover: #232838;
  --color-border: #2a3040;
  --color-text: #e8ecf2;
  --color-text-secondary: #9ba3b5;
  --color-text-muted: #636d82;
  --color-primary: #5b9aff;
  --color-primary-hover: #4a8af0;
  --color-primary-soft: rgba(91, 154, 255, 0.12);
  --color-success: #34d399;
  --color-success-soft: rgba(52, 211, 153, 0.12);
  --color-warning: #fbbf24;
  --color-warning-soft: rgba(251, 191, 36, 0.12);
  --color-danger: #f87171;
  --color-danger-soft: rgba(248, 113, 113, 0.12);
  --color-purple: #a78bfa;
  --color-purple-soft: rgba(167, 139, 250, 0.12);
  --color-gray: #9ca3af;
  --color-gray-soft: rgba(156, 163, 175, 0.12);
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.2);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.4);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans KR', sans-serif;
  background: var(--color-bg);
  color: var(--color-text);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

a {
  color: var(--color-primary);
  text-decoration: none;
}

button {
  cursor: pointer;
  font-family: inherit;
}
</style>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  backdrop-filter: blur(12px);
}

.navbar-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  height: 60px;
  display: flex;
  align-items: center;
  gap: 32px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text);
  font-weight: 700;
  font-size: 1.1rem;
  text-decoration: none;
}

.logo-icon {
  font-size: 1.5rem;
  color: var(--color-primary);
}

.logo-text sup {
  font-size: 0.6rem;
  color: var(--color-text-muted);
  font-weight: 500;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.15s ease;
  text-decoration: none;
}

.nav-link:hover {
  color: var(--color-text);
  background: var(--color-surface-hover);
}

.nav-link.router-link-exact-active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.nav-icon {
  font-size: 1.1rem;
}

.theme-toggle {
  margin-left: auto;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  transition: all 0.15s ease;
}

.theme-toggle:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.main-content {
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 32px 24px;
}
</style>
