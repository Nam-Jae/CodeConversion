<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { createJob } from '@/api/client'

const router = useRouter()
const submitting = ref(false)
const error = ref<string | null>(null)

const sampleInput = `<?xml version="1.0" encoding="UTF-8"?>
<Order>
  <OrderHeader>
    <OrderNumber>ORD-2024-001</OrderNumber>
    <OrderDate>2024-01-15</OrderDate>
    <Customer>
      <Name>홍길동</Name>
      <Email>hong@example.com</Email>
    </Customer>
  </OrderHeader>
  <OrderItems>
    <Item>
      <ProductCode>PROD-A1</ProductCode>
      <ProductName>노트북</ProductName>
      <Quantity>2</Quantity>
      <UnitPrice>1500000</UnitPrice>
    </Item>
    <Item>
      <ProductCode>PROD-B2</ProductCode>
      <ProductName>마우스</ProductName>
      <Quantity>5</Quantity>
      <UnitPrice>25000</UnitPrice>
    </Item>
  </OrderItems>
</Order>`

const sampleOutput = `<?xml version="1.0" encoding="UTF-8"?>
<PurchaseOrder>
  <Header>
    <PONumber>ORD-2024-001</PONumber>
    <Date>2024-01-15</Date>
    <Buyer>
      <FullName>홍길동</FullName>
      <ContactEmail>hong@example.com</ContactEmail>
    </Buyer>
  </Header>
  <LineItems>
    <LineItem>
      <SKU>PROD-A1</SKU>
      <Description>노트북</Description>
      <Qty>2</Qty>
      <Price>1500000</Price>
      <Total>3000000</Total>
    </LineItem>
    <LineItem>
      <SKU>PROD-B2</SKU>
      <Description>마우스</Description>
      <Qty>5</Qty>
      <Price>25000</Price>
      <Total>125000</Total>
    </LineItem>
  </LineItems>
  <OrderTotal>3125000</OrderTotal>
</PurchaseOrder>`

interface PairEntry {
  id: number
  inputXml: string
  outputXml: string
}

let nextId = 2
const pairs = ref<PairEntry[]>([
  { id: 1, inputXml: sampleInput, outputXml: sampleOutput }
])

function addPair() {
  pairs.value.push({ id: nextId++, inputXml: '', outputXml: '' })
}

function removePair(id: number) {
  if (pairs.value.length > 1) {
    pairs.value = pairs.value.filter(p => p.id !== id)
  }
}

async function submit() {
  error.value = null

  const xmlPairs = pairs.value.map(p => ({
    inputXml: p.inputXml.trim(),
    outputXml: p.outputXml.trim()
  }))

  const hasEmpty = xmlPairs.some(p => !p.inputXml || !p.outputXml)
  if (hasEmpty) {
    error.value = '모든 XML 필드를 입력해주세요.'
    return
  }

  submitting.value = true
  try {
    const job = await createJob(xmlPairs)
    router.push(`/result/${job.job_id}`)
  } catch (e) {
    error.value = '작업 생성에 실패했습니다. 서버 상태를 확인해주세요.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="upload">
    <div class="page-header">
      <h1 class="page-title">XML 변환 쌍 업로드</h1>
      <p class="page-desc">입력 XML과 기대 출력 XML 쌍을 입력하세요. 여러 쌍을 추가할 수 있습니다.</p>
    </div>

    <div v-if="error" class="error-banner">
      <span class="error-icon">&#x26A0;</span>
      {{ error }}
    </div>

    <div class="pairs-list">
      <div v-for="(pair, index) in pairs" :key="pair.id" class="pair-card">
        <div class="pair-header">
          <span class="pair-label">쌍 #{{ index + 1 }}</span>
          <button
            v-if="pairs.length > 1"
            class="btn-remove"
            @click="removePair(pair.id)"
            title="쌍 삭제"
          >
            &#x2715;
          </button>
        </div>
        <div class="pair-body">
          <div class="xml-input-group">
            <label class="xml-label">
              <span class="label-dot input-dot"></span>
              입력 XML
            </label>
            <textarea
              v-model="pair.inputXml"
              class="xml-textarea"
              placeholder="입력 XML을 붙여넣으세요..."
              spellcheck="false"
            ></textarea>
          </div>
          <div class="pair-arrow">&#x2192;</div>
          <div class="xml-input-group">
            <label class="xml-label">
              <span class="label-dot output-dot"></span>
              출력 XML
            </label>
            <textarea
              v-model="pair.outputXml"
              class="xml-textarea"
              placeholder="기대 출력 XML을 붙여넣으세요..."
              spellcheck="false"
            ></textarea>
          </div>
        </div>
      </div>
    </div>

    <div class="actions">
      <button class="btn btn-secondary" @click="addPair">
        <span class="btn-icon">+</span>
        쌍 추가
      </button>
      <button
        class="btn btn-primary btn-lg"
        @click="submit"
        :disabled="submitting"
      >
        <span v-if="submitting" class="spinner-sm"></span>
        <span v-else class="btn-icon">&#x25B6;</span>
        {{ submitting ? '생성 중...' : '분석 시작' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.upload {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  margin-bottom: 8px;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-bottom: 8px;
}

.page-desc {
  color: var(--color-text-secondary);
  font-size: 0.95rem;
}

.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--color-danger-soft);
  color: var(--color-danger);
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  font-weight: 500;
}

.error-icon {
  font-size: 1.1rem;
}

.pairs-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.pair-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.pair-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
}

.pair-label {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--color-text-secondary);
}

.btn-remove {
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-size: 0.9rem;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: all 0.15s ease;
}

.btn-remove:hover {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.pair-body {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 0;
  padding: 20px;
  align-items: start;
}

.pair-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 12px;
  margin-top: 36px;
  font-size: 1.3rem;
  color: var(--color-text-muted);
}

.xml-input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.xml-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.label-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.input-dot {
  background: var(--color-primary);
}

.output-dot {
  background: var(--color-success);
}

.xml-textarea {
  width: 100%;
  min-height: 300px;
  padding: 14px;
  background: var(--color-bg);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 0.82rem;
  line-height: 1.6;
  resize: vertical;
  transition: border-color 0.15s ease;
}

.xml-textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}

.xml-textarea::placeholder {
  color: var(--color-text-muted);
}

.actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 8px;
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

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
  box-shadow: var(--shadow-md);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text);
}

.btn-lg {
  padding: 12px 28px;
  font-size: 1rem;
}

.btn-icon {
  font-size: 1.1rem;
}

.spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .pair-body {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .pair-arrow {
    transform: rotate(90deg);
    margin-top: 0;
    padding: 4px 0;
  }
}
</style>
