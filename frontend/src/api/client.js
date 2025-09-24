const DEFAULT_API_PORT = 8000

function resolveDefaultApiBaseUrl() {
  const configured = import.meta.env.VITE_API_BASE_URL
  if (configured && configured.trim().length > 0) {
    return configured.trim()
  }

  if (typeof window === 'undefined') {
    return `http://localhost:${DEFAULT_API_PORT}`
  }

  const { protocol, hostname } = window.location
  if (!hostname) {
    return `http://localhost:${DEFAULT_API_PORT}`
  }

  const normalizedProtocol = protocol || 'http:'
  const isStandardPort =
    (normalizedProtocol === 'http:' && DEFAULT_API_PORT === 80) ||
    (normalizedProtocol === 'https:' && DEFAULT_API_PORT === 443)

  if (isStandardPort) {
    return `${normalizedProtocol}//${hostname}`
  }

  return `${normalizedProtocol}//${hostname}:${DEFAULT_API_PORT}`
}

const API_BASE_URL = resolveDefaultApiBaseUrl()

async function apiFetch(path, { method = 'GET', body, headers, signal } = {}) {
  const requestHeaders = {
    'Content-Type': 'application/json',
    ...(headers ?? {}),
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: requestHeaders,
    body: body ? JSON.stringify(body) : undefined,
    signal,
  })

  if (response.status === 204) {
    return null
  }

  const text = await response.text()
  const payload = text ? JSON.parse(text) : null

  if (!response.ok) {
    const detail = payload?.detail || payload?.message || response.statusText
    throw new Error(detail)
  }

  return payload
}

export function createRoom(payload) {
  return apiFetch('/rooms', { method: 'POST', body: payload })
}

export function fetchRoom(code, { signal } = {}) {
  return apiFetch(`/rooms/${encodeURIComponent(code)}`, { signal })
}

export function joinRoom(code, payload) {
  return apiFetch(`/rooms/${encodeURIComponent(code)}/join`, {
    method: 'POST',
    body: payload,
  })
}

export function startRound(code, payload) {
  return apiFetch(`/rooms/${encodeURIComponent(code)}/start_round`, {
    method: 'POST',
    body: payload,
  })
}

export async function getCurrentRound(code, { revealAnswer = false } = {}) {
  try {
    return await apiFetch(
      `/rooms/${encodeURIComponent(code)}/rounds/current?reveal_answer=${revealAnswer ? 'true' : 'false'}`,
    )
  } catch (error) {
    if (error.message.includes('No active round')) {
      return null
    }
    throw error
  }
}

export function submitGuess(code, roundId, payload) {
  return apiFetch(`/rooms/${encodeURIComponent(code)}/rounds/${roundId}/guess`, {
    method: 'POST',
    body: payload,
  })
}

export function sendSkip(code, roundId, payload) {
  return apiFetch(`/rooms/${encodeURIComponent(code)}/rounds/${roundId}/skip`, {
    method: 'POST',
    body: payload,
  })
}

export function getLeaderboard(code) {
  return apiFetch(`/rooms/${encodeURIComponent(code)}/leaderboard`)
}

export function listSongs({ status } = {}) {
  const query = status ? `?status=${encodeURIComponent(status)}` : ''
  return apiFetch(`/songs${query}`)
}

export function createSong(payload, adminToken) {
  return apiFetch('/admin/songs', {
    method: 'POST',
    body: payload,
    headers: { 'X-Admin-Token': adminToken },
  })
}

export function updateSong(songId, payload, adminToken) {
  return apiFetch(`/admin/songs/${songId}`, {
    method: 'PATCH',
    body: payload,
    headers: { 'X-Admin-Token': adminToken },
  })
}

export function approveSong(songId, adminToken) {
  return apiFetch(`/admin/songs/${songId}/approve`, {
    method: 'POST',
    headers: { 'X-Admin-Token': adminToken },
  })
}

export function rejectSong(songId, adminToken) {
  return apiFetch(`/admin/songs/${songId}/reject`, {
    method: 'POST',
    headers: { 'X-Admin-Token': adminToken },
  })
}

export { API_BASE_URL }
