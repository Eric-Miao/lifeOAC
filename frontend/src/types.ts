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
  subagents: number
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

export type Run = {
  id: number
  agent_id: string
  provider: string
  call_id: string
  workspace: string | null
  prompt: string
  status: 'running' | 'completed' | 'failed' | 'cancelled' | string
  content: string | null
  error: string | null
  session_id: string | null
  started_at: string
  finished_at: string | null
  checked_at: string | null
}

export type ExecutionInfo = {
  available: boolean
  providers: { provider: string; available: boolean; version: string | null; verified: boolean }[]
}

export type Entry = {
  id: number
  ts: string
  kind: string
  period: string | null
  actor: string
  label: string | null
  amount_cents: number
  hours: number
  section: string | null
  product_id: string | null
}

export type LlmModel = {
  providerID: string
  id: string
  name: string
  cost?: { input: number; output: number } | null
}

export type LlmInfo = {
  online: boolean
  models: LlmModel[]
  config: { default: { providerID: string; id: string }; agents: Record<string, { providerID: string; id: string }> }
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
  products: Product[]
  runs: Run[]
  entries: Entry[]
  execution: ExecutionInfo
  llm: { online: boolean; default: { providerID: string; id: string } }
  audit: AuditRow[]
}


export type Product = {
  id: string
  name: string
  kind: 'app' | 'toy' | 'media' | string
  owner: string
  stage: string
  progress: number
  milestone: string | null
  milestone_due: string | null
  price_cents: number
  unit_cost_cents: number
  inventory: number
  note: string | null
}

export type PortfolioRow = {
  id: string
  name: string
  kind: string
  owner: string
  revenue: number
  cost: number
  margin: number
  margin_pct: number
  inventory: number
  unit_cost: number
  price: number
  stock_value: number
}

export type Line = { id: number; period: string; product_id: string | null; section: string; label: string; amount_cents: number; note: string | null }

export type Finance = {
  period: string
  currency: string
  pl: {
    revenue: Line[]
    cogs: Line[]
    opex: Line[]
    total_revenue: number
    total_cogs: number
    gross: number
    gross_pct: number
    total_opex: number
    net: number
    net_pct: number
    salary_share: number
    side_revenue: number
  }
  cash: { opening: number; inflow: number; outflow: number; closing: number; monthly_burn: number; runway_months: number }
  balance: {
    assets: { label: string; amount: number }[]
    liabilities: { label: string; amount_cents: number }[]
    assets_total: number
    liabilities_total: number
    equity: number
  }
  portfolio: PortfolioRow[]
}

export type Settings = {
  billing: {
    provider: string
    model: string
    cap_cents: number
    spent_cents: number
    keys: { name: string; masked: string; status: string }[]
    by_agent: { agent: string; calls: number; cents: number }[]
  }
  memory: {
    namespaces: { name: string; docs: number; tokens: number; updated: string }[]
    dreaming: { last: string; next: string; kept: number; dropped: number }
    pending: number
  }
  plugins: { id: string; name: string; version: string; scopes: string[]; status: string; owner: string }[]
  connectors: { id: string; name: string; kind: string; status: string; last: string; detail: string }[]
  notifications: {
    brief_at: string
    channels: { name: string; level: string }[]
    sources: { name: string; level: string }[]
  }
  policy: {
    version: number
    effective: string
    folder_roots: string[]
    rules: { id: string; action: string; gate: string; approver: string | null }[]
  }
}
