type RequestHandler = (payload: any) => Promise<any> | any

const handlers = new Map<string, RequestHandler>()

export const calls: any[] = []

export function __resetRequestMock() {
  handlers.clear()
  calls.length = 0
}

export function __mockRequest(method: string, url: string, handler: RequestHandler) {
  handlers.set(`${method.toUpperCase()} ${url}`, handler)
}

function run(method: string, url: string, payload: any) {
  calls.push({ method, url, payload })
  const handler = handlers.get(`${method} ${url}`)
  if (!handler) {
    return Promise.reject(new Error(`No mock for ${method} ${url}`))
  }
  try {
    return Promise.resolve(handler(payload))
  } catch (error) {
    return Promise.reject(error)
  }
}

export default function request(options: any) {
  return run(String(options?.method || 'GET').toUpperCase(), options?.url, options)
}

export function get(url: string, params?: Record<string, any>) {
  const qs = params
    ? Object.entries(params)
      .filter(([, value]) => value !== undefined && value !== null)
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
      .join('&')
    : ''
  return run('GET', qs ? `${url}?${qs}` : url, { params })
}

export function post(url: string, data?: any) {
  return run('POST', url, { data })
}
