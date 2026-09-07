export type JobStatus =
  | 'discovered' | 'analyzing' | 'review_required' | 'tailoring'
  | 'ready_to_apply' | 'applying' | 'applied' | 'waiting_input'
  | 'failed' | 'skipped' | 'interview' | 'rejected'

export type Platform = 'linkedin' | 'naukri' | 'indeed' | 'glassdoor' | 'manual'

export interface MatchGap {
  category: string
  gap: string
  severity: 'critical' | 'moderate' | 'minor'
  suggestion: string
}

export interface MatchDetails {
  match_score: number
  matched_skills: string[]
  missing_skills: string[]
  matched_experience: string[]
  gaps: MatchGap[]
  overall_summary: string
  recommendation: string
}

export interface Job {
  id: string
  title: string
  company: string
  platform: Platform
  location?: string
  salary_min?: number
  salary_max?: number
  salary_currency?: string
  salary_raw?: string
  job_description?: string
  requirements?: string[]
  skills_required?: string[]
  apply_url?: string
  external_id?: string
  status: JobStatus
  match_score?: number
  match_details?: MatchDetails
  is_easy_apply?: boolean
  remote_type?: string
  job_type?: string
  job_classification?: 'Internship' | 'FTE'
  posted_at?: string
  discovered_at: string
  updated_at?: string
  notes?: string
}

export interface Resume {
  id: string
  version: string
  file_path: string
  content_text?: string
  is_base: boolean
  tailored_for_job?: string
  diff_summary?: string
  created_at: string
}

export interface Application {
  id: string
  job_id: string
  resume_id?: string
  status: JobStatus
  result: string
  applied_at?: string
  confirmation_number?: string
  screenshot_path?: string
  error_message?: string
  created_at: string
}

export interface SavedAnswer {
  id: string
  field_key: string
  field_label?: string
  answer: string
  is_sensitive: boolean
  confidence: number
  source: string
  usage_count: number
  created_at: string
}

export interface PendingField {
  id: string
  job_id: string
  field_key: string
  field_label?: string
  field_type: string
  options?: string[]
  is_resolved: boolean
  answer?: string
  created_at: string
}

export interface AgentLog {
  id: string
  job_id?: string
  event: string
  level: string
  message?: string
  agent_name?: string
  decision?: string
  decision_reason?: string
  extra?: Record<string, unknown>
  created_at: string
}

export interface AppSettings {
  user_full_name: string
  user_email: string
  user_phone: string
  user_location: string
  user_years_experience: number
  user_expected_salary_intern: string
  user_expected_salary_fte: string
  user_notice_period: string
  user_linkedin_url: string
  user_github_url: string
  user_portfolio_url: string
  user_leetcode_url: string
  auto_apply_threshold: number
  max_applications_per_day: number
  gemini_model: string
  gemini_configured: boolean
}
