import { useCallback, useEffect, useMemo, useState } from 'react'
import { cancelRun, getMessages, getState, sendMessage, resolveApproval, startRun } from './api'
import type { Message, State } from './types'
import { IconBox, IconGear, IconLog, IconMoney, IconOffice, IconOrg, IconThread } from './components/Icons'
import OfficeView from './views/OfficeView'
import OrgView from './views/OrgView'
import ThreadsView from './views/ThreadsView'
import AuditView from './views/AuditView'
import ProductsView from './views/ProductsView'
import FinanceView from './views/FinanceView'
import SettingsView from './views/SettingsView'

type ViewId = 'office' | 'org' | 'products' | 'finance' | 'threads' | 'audit' | 'settings'

const VIEWS: {
  id: ViewId
  label: string
  title: string
  lede: string
  icon: (p: { size?: number }) => React.JSX.Element
}[] = [
  {
    id: 'office',
    label: '办公室',
    title: '办公室',
    lede: '点一个人就能说话。头顶冒气泡的，是等你拍板的事。',
    icon: IconOffice,
  },
  {
    id: 'org',
    label: '组织图',
    title: '组织图',
    lede: '一位 CEO，七个直属。这张图从人事决议里长出来，不手改。',
    icon: IconOrg,
  },
  {
    id: 'products',
    label: '产品',
    title: '产品',
    lede: '公司到底在卖什么，各自走到哪一步。每行一个负责人、一个里程碑。',
    icon: IconBox,
  },
  {
    id: 'finance',
    label: '财务',
    title: '财务',
    lede: '三张表、项目成本、待批。利润不是现金，主业是现金牛。',
    icon: IconMoney,
  },
  {
    id: 'threads',
    label: '对话',
    title: '对话',
    lede: '你和每一位 CxO 的直线。秘书只在产出要回到你这里时才介入。',
    icon: IconThread,
  },
  {
    id: 'audit',
    label: '审计',
    title: '审计',
    lede: '谁、在什么时候、依据哪条策略、做了什么。只增不改。',
    icon: IconLog,
  },
  {
    id: 'settings',
    label: '设置',
    title: '设置',
    lede: '系统自己怎么跑：权限、billing、记忆、插件、连接、打扰强度。',
    icon: IconGear,
  },
]

export default function App() {
  const [view, setView] = useState<ViewId>('office')
  const [data, setData] = useState<State | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [activeThread, setActiveThread] = useState('sec')
  const [messages, setMessages] = useState<Message[]>([])

  const load = useCallback(async () => {
    try {
      const next = await getState()
      setData(next)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : '连接失败')
    }
  }, [])

  useEffect(() => {
    void load()
    const id = window.setInterval(() => void load(), 4000)
    return () => window.clearInterval(id)
  }, [load])

  const threadId = view === 'office' ? selectedId : activeThread

  useEffect(() => {
    if (!threadId) {
      setMessages([])
      return
    }
    let alive = true
    getMessages(threadId)
      .then((m) => alive && setMessages(m))
      .catch(() => alive && setMessages([]))
    return () => {
      alive = false
    }
  }, [threadId])

  const send = useCallback(
    async (agentId: string, body: string) => {
      const next = await sendMessage(agentId, body)
      setMessages(next)
      void load()
    },
    [load],
  )

  const start = useCallback(
    async (agentId: string, provider: string, prompt: string) => {
      await startRun(agentId, provider, prompt)
      void load()
    },
    [load],
  )

  const stop = useCallback(
    async (runId: number) => {
      await cancelRun(runId)
      void load()
    },
    [load],
  )

  const resolve = useCallback(
    async (id: number, decision: 'approve' | 'reject') => {
      await resolveApproval(id, decision)
      if (threadId) setMessages(await getMessages(threadId))
      void load()
    },
    [load, threadId],
  )

  const selected = useMemo(
    () => data?.agents.find((a) => a.id === selectedId) ?? null,
    [data, selectedId],
  )

  const meta = VIEWS.find((v) => v.id === view)!
  const pending = data?.approvals.length ?? 0

  if (!data) {
    return (
      <div className="app">
        <aside className="rail">
          <div className="brand">
            <span className="wordmark">lifeOAC</span>
            <span className="sub">counting house</span>
          </div>
        </aside>
        <main className="main">
          <header className="top">
            <div>
              <h1>{error ? '接不上后端' : '正在开机'}</h1>
              <p className="lede">
                {error
                  ? `${error} · 先确认 backend 在 8000 端口跑着（cd backend && uv run uvicorn app.main:app --port 8000）`
                  : '载入组织图与空账本。'}
              </p>
            </div>
          </header>
        </main>
      </div>
    )
  }

  return (
    <div className="app">
      <aside className="rail">
        <div className="brand">
          <span className="mark" aria-hidden="true">
            <i />
            <i />
            <i />
            <i />
          </span>
          <span className="wordmark">lifeOAC</span>
          <span className="sub">counting house</span>
        </div>

        <nav aria-label="主导航">
          {VIEWS.map((v) => {
            const Icon = v.icon
            return (
              <button
                key={v.id}
                className="navitem"
                aria-current={view === v.id ? 'page' : undefined}
                onClick={() => setView(v.id)}
              >
                <Icon />
                <span className="label">{v.label}</span>
                {v.id === 'office' && pending > 0 && <span className="count hot">{pending}</span>}
                {v.id === 'threads' && <span className="count">{data.agents.length}</span>}
              </button>
            )
          })}
        </nav>

        <div className="railfoot">
          <span className="sandbox">
            <span>
              {data.llm.online ? '对话接模型' : '沙箱对话'} · {data.execution.available ? '执行真实' : '执行未接'}
            </span>
          </span>
          <span className="mono" style={{ fontSize: 10, color: 'var(--muted)' }}>
            v0.1 · {data.server_time.slice(11, 16)}
          </span>
        </div>
      </aside>

      <main className="main">
        <header className="top">
          <div>
            <h1>{meta.title}</h1>
            <p className="lede">{meta.lede}</p>
          </div>
          <div className="topmeta">
            <span>
              {data.agents.length} 个席位 · 你 1 人
            </span>
            <span className="tag">{pending > 0 ? `${pending} 待批` : '无待批'}</span>
          </div>
        </header>

        {view === 'office' && (
          <OfficeView
            state={data}
            selected={selected}
            messages={messages}
            runs={data.runs}
            packages={data.packages}
            execution={data.execution}
            onSelect={setSelectedId}
            onSend={send}
            onResolve={resolve}
            onStartRun={start}
            onCancelRun={stop}
          />
        )}

        {view === 'org' && (
          <OrgView
            agents={data.agents}
            selectedId={selectedId}
            onOpen={(id) => {
              setSelectedId(id)
              setView('office')
            }}
          />
        )}

        {view === 'threads' && (
          <ThreadsView
            agents={data.agents}
            threads={data.threads}
            activeId={activeThread}
            messages={messages}
            onSelect={setActiveThread}
            onSend={send}
          />
        )}

        {view === 'products' && <ProductsView products={data.products} agents={data.agents} />}

        {view === 'finance' && (
          <FinanceView
            approvals={data.approvals}
            agents={data.agents}
            decisions={data.decisions}
            onResolve={resolve}
          />
        )}

        {view === 'audit' && <AuditView rows={data.audit} agents={data.agents} />}
        {view === 'settings' && <SettingsView />}
      </main>
    </div>
  )
}
