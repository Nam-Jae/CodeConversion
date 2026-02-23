<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
  currentIteration: number
  maxIterations: number
}>()

interface Step {
  key: string
  label: string
  icon: string
}

const steps: Step[] = [
  { key: 'analyzing', label: '분석', icon: '&#x1F50D;' },
  { key: 'generating', label: '코드 생성', icon: '&#x2699;' },
  { key: 'testing', label: '테스트', icon: '&#x2713;' },
  { key: 'completed', label: '완료', icon: '&#x2605;' }
]

const statusOrder: Record<string, number> = {
  pending: -1,
  analyzing: 0,
  generating: 1,
  testing: 2,
  completed: 3,
  failed: -2
}

const currentStepIndex = computed(() => {
  return statusOrder[props.status] ?? -1
})

function stepState(stepIndex: number): 'completed' | 'active' | 'pending' {
  if (props.status === 'failed') {
    if (stepIndex <= currentStepIndex.value) return 'completed'
    // Mark the step where failure likely occurred
    const failIdx = Math.max(0, currentStepIndex.value)
    if (stepIndex === failIdx) return 'active'
    return 'pending'
  }
  if (stepIndex < currentStepIndex.value) return 'completed'
  if (stepIndex === currentStepIndex.value) return 'active'
  return 'pending'
}

const statusLabel = computed(() => {
  const labels: Record<string, string> = {
    pending: '대기 중',
    analyzing: 'XML 구조를 분석하고 있습니다...',
    generating: '변환 코드를 생성하고 있습니다...',
    testing: '생성된 코드를 테스트하고 있습니다...',
    completed: '모든 작업이 완료되었습니다.',
    failed: '작업 중 오류가 발생했습니다.'
  }
  return labels[props.status] || props.status
})
</script>

<template>
  <div class="progress-tracker" :class="{ failed: status === 'failed' }">
    <div class="tracker-header">
      <span class="tracker-status" :class="status">{{ statusLabel }}</span>
      <span v-if="currentIteration > 0" class="tracker-iteration">
        반복 {{ currentIteration }} / {{ maxIterations }}
      </span>
    </div>

    <div class="steps">
      <template v-for="(step, index) in steps" :key="step.key">
        <div class="step" :class="stepState(index)">
          <div class="step-indicator">
            <div class="step-circle">
              <span v-if="stepState(index) === 'completed'" class="step-check">&#x2713;</span>
              <span v-else-if="stepState(index) === 'active' && status !== 'failed'" class="step-pulse"></span>
              <span v-else-if="stepState(index) === 'active' && status === 'failed'" class="step-x">&#x2715;</span>
              <span v-else class="step-num">{{ index + 1 }}</span>
            </div>
          </div>
          <span class="step-label">{{ step.label }}</span>
        </div>
        <div v-if="index < steps.length - 1" class="step-connector" :class="{ done: stepState(index) === 'completed' }"></div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.progress-tracker {
  padding: 20px 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.progress-tracker.failed {
  border-color: rgba(239, 68, 68, 0.3);
}

.tracker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.tracker-status {
  font-size: 0.88rem;
  font-weight: 600;
}

.tracker-status.pending { color: var(--color-gray); }
.tracker-status.analyzing { color: var(--color-primary); }
.tracker-status.generating { color: var(--color-purple); }
.tracker-status.testing { color: var(--color-warning); }
.tracker-status.completed { color: var(--color-success); }
.tracker-status.failed { color: var(--color-danger); }

.tracker-iteration {
  font-size: 0.8rem;
  font-weight: 600;
  padding: 3px 10px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 99px;
  color: var(--color-text-secondary);
}

.steps {
  display: flex;
  align-items: flex-start;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  min-width: 80px;
}

.step-indicator {
  position: relative;
}

.step-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
  transition: all 0.3s ease;
}

.step.pending .step-circle {
  background: var(--color-bg-secondary);
  border: 2px solid var(--color-border);
  color: var(--color-text-muted);
}

.step.active .step-circle {
  background: var(--color-primary-soft);
  border: 2px solid var(--color-primary);
  color: var(--color-primary);
}

.progress-tracker.failed .step.active .step-circle {
  background: var(--color-danger-soft);
  border-color: var(--color-danger);
  color: var(--color-danger);
}

.step.completed .step-circle {
  background: var(--color-success);
  border: 2px solid var(--color-success);
  color: #ffffff;
}

.step-check {
  font-size: 0.9rem;
}

.step-x {
  font-size: 0.85rem;
}

.step-pulse {
  display: block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: currentColor;
  animation: stepPulse 1.2s ease-in-out infinite;
}

@keyframes stepPulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(0.6); opacity: 0.4; }
}

.step-num {
  font-size: 0.78rem;
}

.step-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--color-text-muted);
  text-align: center;
}

.step.active .step-label {
  color: var(--color-primary);
}

.step.completed .step-label {
  color: var(--color-success);
}

.progress-tracker.failed .step.active .step-label {
  color: var(--color-danger);
}

.step-connector {
  flex: 1;
  height: 2px;
  background: var(--color-border);
  margin-top: 18px;
  transition: background 0.3s ease;
}

.step-connector.done {
  background: var(--color-success);
}
</style>
