import { get } from '@/utils/request'

export interface AnalyticsMetrics {
  total_questions: number
  total_questions_prev: number
  ai_rate: number
  ai_rate_prev: number
  avg_response_min: number
  avg_response_min_prev: number
  pending_count: number
}

export interface AnalyticsTrends {
  dates: string[]
  total: number[]
  ai_answered: number[]
}

export interface AiQuality {
  hit_rate: number
  score_low: number
  score_mid: number
  score_high: number
}

export interface HotQuestion {
  id: number
  text: string
  count: number
}

export interface CollegeItem {
  name: string
  count: number
}

export interface AnalyticsData {
  metrics: AnalyticsMetrics
  trends: AnalyticsTrends
  ai_quality: AiQuality
  hot_unanswered: HotQuestion[]
  college_distribution: CollegeItem[]
  heatmap: number[][]  // 7×24
}

export function getAnalytics(period: '7d' | '30d' | 'all' = '7d'): Promise<AnalyticsData> {
  return get<AnalyticsData>('/api/analytics', { period })
}
