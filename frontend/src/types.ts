export type Status = 'idle' | 'working' | 'waiting' | 'blocked'

export type Palette = {
  hair: string
  skin: string
  shirt: string
  pants: string
  trim: string
}

export type Agent = {
  id: string
  code: string
  name: string
  title: string
  reports_to: string | null
  tier: number
  status: Status
  task: string | null
  scope: string
  kpi: string
  palette: Palette
  desk_x: number
  desk_y: number
  seat: number
}

export type Approval = {
  id: number
  ts: string
  agent_id: string
  title: string
  detail: string | null
  amount_cents: number
  status: string
}

export type Message = {
  id: number
  ts: string
  thread: string
  sender: string
  body: string
  kind: string
}

export type Budget = {
  id: string
  name: string
  owner: string
  period: string
  money_cents: number
  money_spent: number
  hours: number
  hours_spent: number
}

export type AuditRow = {
  id: number
  ts: string
  actor: string
  action: string
  target: string | null
  policy: string | null
  decision: string
  meta: string | null
}

export type Thread = {
  thread: string
  count: number
  last: Message
}

export type State = {
  mode: string
  server_time: string
  agents: Agent[]
  approvals: Approval[]
  threads: Thread[]
  budgets: Budget[]
  audit: AuditRow[]
}
