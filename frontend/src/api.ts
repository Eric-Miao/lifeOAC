import type { Message, State } from './types'

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}${text ? ` · ${text}` : ''}`)
  }
  return (await res.json()) as T
}

export const getState = () => fetch('/api/state').then((r) => json<State>(r))

export const getMessages = (agentId: string) =>
  fetch(`/api/agents/${agentId}/messages`)
    .then((r) => json<{ messages: Message[] }>(r))
    .then((d) => d.messages)

export const sendMessage = (agentId: string, body: string) =>
  fetch(`/api/agents/${agentId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ body }),
  })
    .then((r) => json<{ messages: Message[] }>(r))
    .then((d) => d.messages)

export const resolveApproval = (id: number, decision: 'approve' | 'reject', note = '') =>
  fetch(`/api/approvals/${id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, note }),
  }).then((r) => json<{ ok: boolean }>(r))

export const money = (cents: number) =>
  '¥' + (cents / 100).toLocaleString('zh-CN', { maximumFractionDigits: 0 })

export const clock = (iso: string) => {
  const d = new Date(iso)
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

export const timeOnly = (iso: string) => {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
