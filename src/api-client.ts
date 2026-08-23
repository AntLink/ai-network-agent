const API_BASE = process.env.NETWORK_AGENT_API || "http://localhost:8000/api/v1"

export async function apiGet<T>(path: string): Promise<T> {
  const url = `${API_BASE}${path}`
  const res = await fetch(url)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API error ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const url = `${API_BASE}${path}`
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API error ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}
