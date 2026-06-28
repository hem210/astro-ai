import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, // send the HttpOnly refresh token cookie on every request
})

// Attach access token to every outgoing request
api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// On 401: refresh token, update stored token, retry original request once
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config

    if (error.response?.status === 401 && !original._retried && original.url !== '/auth/refresh') {
      original._retried = true
      try {
        const { data } = await api.post<{ access_token: string }>('/auth/refresh')
        setAccessToken(data.access_token)
        original.headers.Authorization = `Bearer ${data.access_token}`
        return api(original)
      } catch {
        // Refresh failed — clear token so AuthContext redirects to login
        setAccessToken(null)
        return Promise.reject(error)
      }
    }

    return Promise.reject(error)
  }
)

// In-memory token store — never touches localStorage or cookies
let _accessToken: string | null = null

export function getAccessToken() {
  return _accessToken
}

export function setAccessToken(token: string | null) {
  _accessToken = token
}

export async function refreshToken(): Promise<string | null> {
  try {
    const { data } = await api.post<{ access_token: string }>('/auth/refresh')
    setAccessToken(data.access_token)
    return data.access_token
  } catch {
    setAccessToken(null)
    return null
  }
}

// ---------------------------------------------------------------------------
// SSE fetch with auth + 401 retry
// ---------------------------------------------------------------------------

export async function fetchSSE(url: string, body: string): Promise<Response | null> {
  const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
  let token = getAccessToken()
  let response = await fetch(`${BASE}${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    credentials: 'include',
    body,
  })
  if (response.status === 401) {
    token = await refreshToken()
    if (!token) return null
    response = await fetch(`${BASE}${url}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      credentials: 'include',
      body,
    })
  }
  if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`)
  return response
}
