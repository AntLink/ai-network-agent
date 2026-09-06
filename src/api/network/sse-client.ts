import { getApiBaseUrl } from 'src/api/network/backend-client'

type SSEEvent = {
  type: string
  [key: string]: unknown
}

type SSECallback = (event: SSEEvent) => void

export function connectAgentSSE(onEvent: SSECallback): () => void {
  const url = `${getApiBaseUrl()}/api/v1/agent/events/stream`
  const eventSource = new EventSource(url)

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as SSEEvent
      if (data.type !== 'heartbeat') {
        onEvent(data)
      }
    } catch {
      // ignore parse errors
    }
  }

  eventSource.onerror = () => {
    eventSource.close()
  }

  return () => {
    eventSource.close()
  }
}

export function connectTaskSSE(onEvent: SSECallback): () => void {
  const url = `${getApiBaseUrl()}/api/v1/tasks/stream`
  const eventSource = new EventSource(url)

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as SSEEvent
      if (data.type !== 'heartbeat') {
        onEvent(data)
      }
    } catch {
      // ignore parse errors
    }
  }

  eventSource.onerror = () => {
    eventSource.close()
  }

  return () => {
    eventSource.close()
  }
}
