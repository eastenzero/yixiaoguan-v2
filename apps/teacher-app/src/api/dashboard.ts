import request from '@/utils/request'

// 获取工作台统计数据
export function getDashboardStats() {
  return request({
    url: '/api/v1/dashboard/stats',
    method: 'GET'
  })
}

// 获取工作台聚合数据（一次请求获取所有数据）
export function getDashboardOverview() {
  return request({
    url: '/api/v1/dashboard/overview',
    method: 'GET'
  })
}
