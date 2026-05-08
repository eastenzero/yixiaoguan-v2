import { request } from '@/utils/request'

export interface CollegeOption {
  id: number
  name: string
  campus: string | null
}

let cache: CollegeOption[] | null = null

export async function listColleges(): Promise<CollegeOption[]> {
  if (cache) {
    return cache
  }

  const list = await request<CollegeOption[]>({ url: '/api/colleges' })
  cache = list
  return list
}

export function clearCollegeCache(): void {
  cache = null
}
