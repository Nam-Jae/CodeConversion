<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { getJob, rerunJob, type Job } from '@/api/client'
import ProgressTracker from '@/components/ProgressTracker.vue'
import XmlViewer from '@/components/XmlViewer.vue'

const route = useRoute()
const jobId = route.params.jobId as string
const job = ref<Job | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const activeTab = ref<'analysis' | 'code' | 'test'>('analysis')
const codeCopied = ref(false)
const rerunning = ref(false)

let pollTimer: ReturnType<typeof setInterval> | null = null

const isTerminal = computed(() => {
  if (!job.value) return false
  return job.value.status === 'completed' || job.value.status === 'failed'
})

async function fetchJob() {
  try {
    job.value = await getJob(jobId)
    error.value = null

    if (isTerminal.value && pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  } catch (e) {
    error.value = '작업 정보를 불러올 수 없습니다.'
  } finally {
    loading.value = false
  }
}

async function handleRerun() {
  rerunning.value = true
  try {
    await rerunJob(jobId)
    await fetchJob()
    if (!pollTimer) {
      pollTimer = setInterval(fetchJob, 2000)
    }
  } catch (e) {
    error.value = '재실행에 실패했습니다.'
  } finally {
    rerunning.value = false
  }
}

async function copyCode() {
  if (!job.value?.generated_code?.code) return
  try {
    await navigator.clipboard.writeText(job.value.generated_code.code)
    codeCopied.value = true
    setTimeout(() => { codeCopied.value = false }, 2000)
  } catch {
    const ta = document.createElement('textarea')
    ta.value = job.value.generated_code.code
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    codeCopied.value = true
    setTimeout(() => { codeCopied.value = false }, 2000)
  }
}

function accuracyColor(accuracy: number): string {
  if (accuracy >= 1) return 'var(--color-success)'
  if (accuracy >= 0.8) return 'var(--color-warning)'
  return 'var(--color-danger)'
}

onMounted(() => {
  fetchJob()
  pollTimer = setInterval(fetchJob, 2000)
})

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
  }
})
</script>

<template>
  <div class="result">
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>작업 정보를 불러오는 중...</span>
    </div>

    <div v-else-if="error && !job" class="error-state">
      <div class="error-icon">&#x26A0;</div>
      <p>{{ error }}</p>
    </div>

    <template v-else-if="job">
      <!-- Header -->
      <div class="result-header">
        <div class="header-left">
          <h1 class="page-title">작업 결과</h1>
          <span class="job-id-badge">{{ job.job_id.slice(0, 8) }}</span>
        </div>
        <div class="header-right">
          <button
            v-if="isTerminal"
            class="btn btn-secondary"
            @click="handleRerun"
            :disabled="rerunning"
          >
            {{ rerunning ? '재실행 중...' : '재실행' }}
          </button>
        </div>
      </div>

      <!-- Progress -->
      <ProgressTracker
        :status="job.status"
        :current-iteration="job.current_iteration"
        :max-iterations="job.max_iterations"
      />

      <!-- Status message -->
      <div v-if="job.status === 'failed' && job.message" class="error-banner">
        <span class="error-banner-icon">&#x26A0;</span>
        <div>
          <strong>오류 발생</strong>
          <p>{{ job.message }}</p>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button
          class="tab"
          :class="{ active: activeTab === 'analysis' }"
          @click="activeTab = 'analysis'"
        >
          분석 결과
        </button>
        <button
          class="tab"
          :class="{ active: activeTab === 'code' }"
          @click="activeTab = 'code'"
        >
          생성 코드
        </button>
        <button
          class="tab"
          :class="{ active: activeTab === 'test' }"
          @click="activeTab = 'test'"
        >
          테스트 결과
        </button>
      </div>

      <!-- Analysis Tab -->
      <div v-if="activeTab === 'analysis'" class="tab-content">
        <div v-if="!job.analysis" class="tab-empty">
          <p>분석 결과가 아직 없습니다.</p>
          <p class="tab-empty-hint" v-if="!isTerminal">분석이 완료되면 여기에 결과가 표시됩니다.</p>
        </div>
        <template v-else>
          <!-- Schema Summary -->
          <div v-if="job.analysis.input_schema_summary || job.analysis.output_schema_summary" class="content-section">
            <h3 class="content-title">스키마 요약</h3>
            <div class="schema-summaries">
              <div v-if="job.analysis.input_schema_summary" class="schema-card">
                <h4>입력 스키마</h4>
                <pre class="schema-text">{{ job.analysis.input_schema_summary }}</pre>
              </div>
              <div v-if="job.analysis.output_schema_summary" class="schema-card">
                <h4>출력 스키마</h4>
                <pre class="schema-text">{{ job.analysis.output_schema_summary }}</pre>
              </div>
            </div>
          </div>

          <!-- Field Mappings -->
          <div v-if="job.analysis.field_mappings.length > 0" class="content-section">
            <h3 class="content-title">필드 매핑</h3>
            <div class="table-wrap">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>소스 경로</th>
                    <th>대상 경로</th>
                    <th>매핑 유형</th>
                    <th>설명</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(mapping, i) in job.analysis.field_mappings" :key="i">
                    <td class="mono">{{ mapping.source_path }}</td>
                    <td class="mono">{{ mapping.target_path }}</td>
                    <td><span class="mapping-type-badge">{{ mapping.mapping_type }}</span></td>
                    <td>{{ mapping.description || '-' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Transformation Rules -->
          <div v-if="job.analysis.transformation_rules.length > 0" class="content-section">
            <h3 class="content-title">변환 규칙</h3>
            <div class="rules-list">
              <div
                v-for="(rule, i) in job.analysis.transformation_rules"
                :key="i"
                class="rule-card"
              >
                <div class="rule-header">
                  <span class="rule-type">{{ rule.rule_type }}</span>
                </div>
                <p class="rule-desc">{{ rule.description }}</p>
                <pre v-if="Object.keys(rule.details).length > 0" class="rule-logic"><code>{{ JSON.stringify(rule.details, null, 2) }}</code></pre>
              </div>
            </div>
          </div>

          <!-- Notes -->
          <div v-if="job.analysis.notes" class="content-section">
            <h3 class="content-title">분석 노트</h3>
            <pre class="notes-block">{{ job.analysis.notes }}</pre>
          </div>
        </template>
      </div>

      <!-- Code Tab -->
      <div v-if="activeTab === 'code'" class="tab-content">
        <div v-if="!job.generated_code" class="tab-empty">
          <p>생성된 코드가 아직 없습니다.</p>
          <p class="tab-empty-hint" v-if="!isTerminal">코드 생성이 완료되면 여기에 표시됩니다.</p>
        </div>
        <template v-else>
          <div class="code-section">
            <div class="code-header">
              <span class="code-title">생성된 변환 코드 ({{ job.generated_code.language }})</span>
              <div class="code-actions">
                <span v-if="job.generated_code.iteration > 0" class="iteration-badge">
                  반복 {{ job.generated_code.iteration }}
                </span>
                <button class="btn btn-sm" @click="copyCode">
                  {{ codeCopied ? '복사됨!' : '코드 복사' }}
                </button>
              </div>
            </div>
            <pre class="code-block"><code>{{ job.generated_code.code }}</code></pre>
          </div>
          <div v-if="job.generated_code.description" class="code-description">
            <h4>설명</h4>
            <p>{{ job.generated_code.description }}</p>
          </div>
        </template>
      </div>

      <!-- Test Tab -->
      <div v-if="activeTab === 'test'" class="tab-content">
        <div v-if="!job.test_result" class="tab-empty">
          <p>테스트 결과가 아직 없습니다.</p>
          <p class="tab-empty-hint" v-if="!isTerminal">테스트가 완료되면 여기에 결과가 표시됩니다.</p>
        </div>
        <template v-else>
          <!-- Accuracy Overview -->
          <div class="accuracy-card">
            <div class="accuracy-ring">
              <svg viewBox="0 0 100 100" class="accuracy-svg">
                <circle cx="50" cy="50" r="42" fill="none" stroke="var(--color-border)" stroke-width="8" />
                <circle
                  cx="50" cy="50" r="42" fill="none"
                  :stroke="accuracyColor(job.test_result.accuracy)"
                  stroke-width="8"
                  stroke-linecap="round"
                  :stroke-dasharray="`${job.test_result.accuracy * 264} 264`"
                  transform="rotate(-90 50 50)"
                />
              </svg>
              <div class="accuracy-value" :style="{ color: accuracyColor(job.test_result.accuracy) }">
                {{ (job.test_result.accuracy * 100).toFixed(0) }}%
              </div>
            </div>
            <div class="accuracy-details">
              <h3>전체 정확도</h3>
              <p>{{ job.test_result.passed_pairs }}개 통과 / {{ job.test_result.total_pairs }}개 전체</p>
              <p v-if="job.test_result.error_message" class="error-msg">{{ job.test_result.error_message }}</p>
            </div>
          </div>

          <!-- Per-pair Results -->
          <div v-if="job.test_result.details.length > 0" class="content-section">
            <h3 class="content-title">쌍별 결과</h3>
            <div class="pair-results">
              <div
                v-for="(detail, idx) in job.test_result.details"
                :key="detail.pair_id"
                class="pair-result-card"
                :class="{ passed: detail.passed, failed: !detail.passed }"
              >
                <div class="pair-result-header">
                  <span class="pair-result-label">쌍 #{{ idx + 1 }} ({{ detail.pair_id }})</span>
                  <span class="pair-result-status" :class="{ pass: detail.passed, fail: !detail.passed }">
                    {{ detail.passed ? '통과' : '실패' }}
                  </span>
                </div>
                <div v-if="!detail.passed && detail.diff" class="pair-result-diff">
                  <h4>차이점:</h4>
                  <pre class="diff-block"><code>{{ detail.diff }}</code></pre>
                </div>
                <div v-if="!detail.passed" class="pair-result-outputs">
                  <div class="output-group" v-if="detail.expected_snippet">
                    <h4>기대 출력:</h4>
                    <XmlViewer :xml="detail.expected_snippet" />
                  </div>
                  <div class="output-group" v-if="detail.actual_snippet">
                    <h4>실제 출력:</h4>
                    <XmlViewer :xml="detail.actual_snippet" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </template>
  </div>
</template>

<style scoped>
.result {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 80px 0;
  color: var(--color-text-secondary);
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2.5px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state {
  text-align: center;
  padding: 80px 0;
  color: var(--color-text-secondary);
}

.error-icon {
  font-size: 2.5rem;
  margin-bottom: 12px;
  opacity: 0.5;
}

.error-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 20px;
  background: var(--color-danger-soft);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: var(--radius-md);
  color: var(--color-danger);
}

.error-banner-icon {
  font-size: 1.3rem;
  flex-shrink: 0;
  margin-top: 2px;
}

.error-banner strong {
  display: block;
  margin-bottom: 4px;
}

.error-banner p {
  font-size: 0.9rem;
  opacity: 0.9;
}

.error-msg {
  color: var(--color-danger);
  font-size: 0.85rem;
  margin-top: 4px;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.job-id-badge {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: var(--color-text-muted);
  background: var(--color-bg-secondary);
  padding: 4px 10px;
  border-radius: 99px;
  border: 1px solid var(--color-border);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 600;
  border: none;
  transition: all 0.15s ease;
  cursor: pointer;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 0.8rem;
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}

.btn-sm:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text);
}

.btn-secondary {
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-bg-tertiary);
  color: var(--color-text);
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Tabs */
.tabs {
  display: flex;
  gap: 2px;
  background: var(--color-bg-secondary);
  padding: 4px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.tab {
  flex: 1;
  padding: 10px 16px;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  font-size: 0.88rem;
  font-weight: 600;
  transition: all 0.15s ease;
  cursor: pointer;
}

.tab:hover {
  color: var(--color-text);
}

.tab.active {
  background: var(--color-surface);
  color: var(--color-text);
  box-shadow: var(--shadow-sm);
}

/* Tab Content */
.tab-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.tab-empty {
  text-align: center;
  padding: 48px;
  color: var(--color-text-secondary);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.tab-empty-hint {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin-top: 4px;
}

/* Content Sections */
.content-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.content-title {
  font-size: 1rem;
  font-weight: 700;
}

/* Schema */
.schema-summaries {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.schema-card {
  padding: 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.schema-card h4 {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.schema-text {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  white-space: pre-wrap;
  margin: 0;
}

.notes-block {
  padding: 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 0.88rem;
  white-space: pre-wrap;
  margin: 0;
}

/* Table */
.table-wrap {
  overflow-x: auto;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.data-table th {
  text-align: left;
  padding: 12px 16px;
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  font-weight: 600;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--color-border);
}

.data-table td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border);
}

.data-table tr:last-child td {
  border-bottom: none;
}

.mono {
  font-family: var(--font-mono);
  font-size: 0.82rem;
}

.mapping-type-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 8px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  border-radius: 99px;
}

/* Rules */
.rules-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rule-card {
  padding: 16px 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.rule-header {
  margin-bottom: 8px;
}

.rule-type {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 8px;
  background: var(--color-purple-soft);
  color: var(--color-purple);
  border-radius: 99px;
  text-transform: uppercase;
}

.rule-desc {
  font-size: 0.88rem;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.rule-logic {
  padding: 10px 14px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 0.8rem;
  overflow-x: auto;
  white-space: pre-wrap;
  margin: 0;
}

/* Code Section */
.code-section {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.code-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
}

.code-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.code-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.iteration-badge {
  font-size: 0.78rem;
  font-weight: 600;
  padding: 3px 10px;
  background: var(--color-purple-soft);
  color: var(--color-purple);
  border-radius: 99px;
}

.code-block {
  padding: 20px;
  margin: 0;
  overflow-x: auto;
  font-family: var(--font-mono);
  font-size: 0.82rem;
  line-height: 1.7;
  white-space: pre;
  color: var(--color-text);
}

.code-description {
  padding: 16px 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.code-description h4 {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.code-description p {
  font-size: 0.88rem;
  color: var(--color-text-secondary);
}

/* Accuracy */
.accuracy-card {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.accuracy-ring {
  position: relative;
  width: 100px;
  height: 100px;
  flex-shrink: 0;
}

.accuracy-svg {
  width: 100%;
  height: 100%;
}

.accuracy-value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 1.4rem;
  font-weight: 800;
}

.accuracy-details h3 {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 4px;
}

.accuracy-details p {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

/* Pair Results */
.pair-results {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.pair-result-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.pair-result-card.passed {
  border-left: 3px solid var(--color-success);
}

.pair-result-card.failed {
  border-left: 3px solid var(--color-danger);
}

.pair-result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
}

.pair-result-label {
  font-weight: 600;
  font-size: 0.9rem;
}

.pair-result-status {
  font-size: 0.8rem;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: 99px;
}

.pair-result-status.pass {
  color: var(--color-success);
  background: var(--color-success-soft);
}

.pair-result-status.fail {
  color: var(--color-danger);
  background: var(--color-danger-soft);
}

.pair-result-diff {
  padding: 0 20px 16px;
}

.pair-result-diff h4 {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.diff-block {
  padding: 12px 14px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 0.78rem;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre;
  margin: 0;
}

.pair-result-outputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  padding: 0 20px 16px;
}

.output-group h4 {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

@media (max-width: 768px) {
  .pair-result-outputs {
    grid-template-columns: 1fr;
  }
  .schema-summaries {
    grid-template-columns: 1fr;
  }
}
</style>
