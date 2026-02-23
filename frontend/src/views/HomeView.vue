<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getJobs, type JobSummary } from '@/api/client'

const router = useRouter()
const jobs = ref<JobSummary[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

const statusConfig: Record<string, { label: string; color: string; bg: string }> = {
  pending: { label: '대기중', color: 'var(--color-gray)', bg: 'var(--color-gray-soft)' },
  analyzing: { label: '분석중', color: 'var(--color-primary)', bg: 'var(--color-primary-soft)' },
  generating: { label: '생성중', color: 'var(--color-purple)', bg: 'var(--color-purple-soft)' },
  testing: { label: '테스트중', color: 'var(--color-warning)', bg: 'var(--color-warning-soft)' },
  iterating: { label: '반복중', color: 'var(--color-warning)', bg: 'var(--color-warning-soft)' },
  completed: { label: '완료', color: 'var(--color-success)', bg: 'var(--color-success-soft)' },
  failed: { label: '실패', color: 'var(--color-danger)', bg: 'var(--color-danger-soft)' }
}

async function fetchJobs() {
  try {
    jobs.value = await getJobs()
    error.value = null
  } catch (e) {
    if (loading.value) {
      error.value = 'API 서버에 연결할 수 없습니다.'
    }
  } finally {
    loading.value = false
  }
}

function navigateToResult(jobId: string) {
  router.push(`/result/${jobId}`)
}

onMounted(() => {
  fetchJobs()
  pollTimer = setInterval(fetchJobs, 3000)
})

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
  }
})
</script>

<template>
  <div class="home">
    <section class="hero">
      <h1 class="hero-title">XML 변환 코드 자동 생성 시스템</h1>
      <p class="hero-desc">
        입력/출력 XML 쌍을 업로드하면 AI가 변환 규칙을 분석하고,
        변환 코드를 자동 생성한 후 테스트까지 수행합니다.
      </p>
      <router-link to="/upload" class="btn btn-primary btn-lg">
        <span class="btn-icon">+</span>
        새 변환 작업
      </router-link>
    </section>

    <section class="jobs-section">
      <div class="section-header">
        <h2 class="section-title">최근 작업</h2>
        <span v-if="!loading && jobs.length > 0" class="job-count">{{ jobs.length }}건</span>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <span>작업 목록을 불러오는 중...</span>
      </div>

      <div v-else-if="error" class="empty-state">
        <div class="empty-icon">&#x26A0;</div>
        <p>{{ error }}</p>
        <p class="empty-hint">서버가 실행 중인지 확인해주세요.</p>
      </div>

      <div v-else-if="jobs.length === 0" class="empty-state">
        <div class="empty-icon">&#x2B21;</div>
        <p>아직 작업이 없습니다.</p>
        <p class="empty-hint">새 변환 작업을 시작해보세요.</p>
      </div>

      <div v-else class="jobs-list">
        <div
          v-for="job in jobs"
          :key="job.job_id"
          class="job-card"
          @click="navigateToResult(job.job_id)"
        >
          <div class="job-card-header">
            <span
              class="status-badge"
              :style="{
                color: statusConfig[job.status]?.color,
                background: statusConfig[job.status]?.bg
              }"
            >
              <span v-if="['analyzing', 'generating', 'testing', 'iterating'].includes(job.status)" class="status-dot pulse"></span>
              <span v-else class="status-dot"></span>
              {{ statusConfig[job.status]?.label || job.status }}
            </span>
          </div>
          <div class="job-card-body">
            <div class="job-id">{{ job.job_id.slice(0, 8) }}</div>
            <div class="job-message" v-if="job.message">{{ job.message }}</div>
          </div>
          <div class="job-card-arrow">&#x203A;</div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.hero {
  text-align: center;
  padding: 48px 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.hero-title {
  font-size: 1.8rem;
  font-weight: 800;
  margin-bottom: 12px;
  letter-spacing: -0.02em;
}

.hero-desc {
  color: var(--color-text-secondary);
  font-size: 1rem;
  max-width: 540px;
  margin: 0 auto 28px;
  line-height: 1.7;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  font-weight: 600;
  border: none;
  transition: all 0.15s ease;
  text-decoration: none;
}

.btn-primary {
  background: var(--color-primary);
  color: #ffffff;
}

.btn-primary:hover {
  background: var(--color-primary-hover);
  box-shadow: var(--shadow-md);
}

.btn-lg {
  padding: 12px 28px;
  font-size: 1rem;
}

.btn-icon {
  font-size: 1.2rem;
  font-weight: 400;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.section-title {
  font-size: 1.2rem;
  font-weight: 700;
}

.job-count {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  background: var(--color-bg-secondary);
  padding: 2px 10px;
  border-radius: 99px;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px;
  color: var(--color-text-secondary);
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 48px;
  color: var(--color-text-secondary);
}

.empty-icon {
  font-size: 2.5rem;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-hint {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin-top: 4px;
}

.jobs-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.job-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s ease;
}

.job-card:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

.job-card-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 100px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 99px;
  font-size: 0.78rem;
  font-weight: 600;
  width: fit-content;
}

.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.status-dot.pulse {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.job-card-body {
  flex: 1;
}

.job-id {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 4px;
}

.job-message {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.job-card-arrow {
  font-size: 1.5rem;
  color: var(--color-text-muted);
  font-weight: 300;
}
</style>
