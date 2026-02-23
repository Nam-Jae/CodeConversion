import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Matches backend common.models exactly
export interface XmlPair {
  input_xml: string
  output_xml: string
  pair_id?: string
}

export interface FieldMapping {
  source_path: string
  target_path: string
  mapping_type: string
  description: string
}

export interface TransformationRule {
  rule_id: string
  rule_type: string
  description: string
  details: Record<string, unknown>
}

export interface AnalysisResult {
  field_mappings: FieldMapping[]
  transformation_rules: TransformationRule[]
  input_schema_summary: string
  output_schema_summary: string
  notes: string
}

export interface GeneratedCode {
  code: string
  language: string
  description: string
  iteration: number
}

export interface TestDetail {
  pair_id: string
  passed: boolean
  expected_snippet: string
  actual_snippet: string
  diff: string
}

export interface TestResult {
  total_pairs: number
  passed_pairs: number
  accuracy: number
  details: TestDetail[]
  error_message: string
}

export type JobStatusType =
  | 'pending'
  | 'analyzing'
  | 'generating'
  | 'testing'
  | 'iterating'
  | 'completed'
  | 'failed'

export interface JobSummary {
  job_id: string
  status: JobStatusType
  message: string
}

export interface Job {
  job_id: string
  status: JobStatusType
  created_at: string
  xml_pairs: XmlPair[]
  analysis: AnalysisResult | null
  generated_code: GeneratedCode | null
  test_result: TestResult | null
  current_iteration: number
  max_iterations: number
  accuracy_threshold: number
  message: string
}

export async function createJob(
  xmlPairs: { inputXml: string; outputXml: string }[]
): Promise<JobSummary> {
  const payload = {
    xml_pairs: xmlPairs.map((p) => ({
      input_xml: p.inputXml,
      output_xml: p.outputXml
    }))
  }
  const response = await api.post<JobSummary>('/jobs/json', payload)
  return response.data
}

export async function getJobs(): Promise<JobSummary[]> {
  const response = await api.get<JobSummary[]>('/jobs')
  return response.data
}

export async function getJob(jobId: string): Promise<Job> {
  const response = await api.get<Job>(`/jobs/${jobId}`)
  return response.data
}

export async function rerunJob(jobId: string): Promise<JobSummary> {
  const response = await api.post<JobSummary>(`/jobs/${jobId}/run`)
  return response.data
}

export default api
