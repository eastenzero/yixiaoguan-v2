const DEVICE_ID_KEY = 'v2-device-id'

function genId(): string {
  if (typeof globalThis.crypto !== 'undefined' && typeof globalThis.crypto.randomUUID === 'function') {
    return globalThis.crypto.randomUUID()
  }

  return `d-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`
}

export function getDeviceId(): string {
  let id = uni.getStorageSync(DEVICE_ID_KEY) as string | undefined
  if (!id) {
    id = genId()
    uni.setStorageSync(DEVICE_ID_KEY, id)
  }
  return id
}

export function clearDeviceId(): void {
  uni.removeStorageSync(DEVICE_ID_KEY)
}
