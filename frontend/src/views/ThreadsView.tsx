import { Composer, Transcript } from '../components/Drawer'
import { clock } from '../api'
import type { Agent, Message, Thread } from '../types'

const STATUS: Record<string, string> = {
  working: '在办',
  idle: '空闲',
  waiting: '等你批',
  blocked: '卡住',
}

export default function ThreadsView({
  agents,
  threads,
  activeId,
  messages,
  onSelect,
  onSend,
}: {
  agents: Agent[]
  threads: Thread[]
  activeId: string
  messages: Message[]
  onSelect: (id: string) => void
  onSend: (id: string, body: string) => Promise<void>
}) {
  const active = agents.find((a) => a.id === activeId) ?? agents[0]
  const byThread = new Map(threads.map((t) => [t.thread, t]))

  return (
    <div className="view flush" style={{ display: 'grid', gridTemplateColumns: '300px minmax(0,1fr)', minHeight: 'calc(100vh - 96px)' }}>
      <div style={{ borderRight: '1px solid var(--rule)', padding: '16px 0' }}>
        <div className="tiny" style={{ padding: '0 18px 10px' }}>
          线程 · {threads.length}
        </div>
        {agents.map((a) => {
          const t = byThread.get(a.id)
          return (
            <button
              key={a.id}
              onClick={() => onSelect(a.id)}
              aria-current={active?.id === a.id ? 'true' : undefined}
              style={{
                display: 'block',
                width: '100%',
                textAlign: 'left',
                background: active?.id === a.id ? 'var(--surface)' : 'transparent',
                border: 0,
                borderTop: '1px solid var(--rule)',
                padding: '11px 18px',
                cursor: 'pointer',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                <span className="mono" style={{ fontSize: 10, color: 'var(--muted)', width: 34 }}>
                  {a.code}
                </span>
                <span style={{ fontSize: 13, fontWeight: 500 }}>{a.name}</span>
                <span className="mono" style={{ marginLeft: 'auto', fontSize: 10, color: 'var(--muted)' }}>
                  {t?.count ?? 0}
                </span>
              </div>
              <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 3, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {t?.last?.body ?? '还没有对话'}
              </div>
              {t?.last && (
                <div className="tiny" style={{ marginTop: 2 }}>
                  {clock(t.last.ts)}
                </div>
              )}
            </button>
          )
        })}
      </div>

      {active && (
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <div style={{ padding: '18px 22px 14px', borderBottom: '1px solid var(--rule)' }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <span className="mono" style={{ fontSize: 10, letterSpacing: '0.1em', color: 'var(--accent)' }}>
                {active.code}
              </span>
              <h2 style={{ fontFamily: 'var(--display)', fontSize: 19, fontWeight: 600, letterSpacing: '-0.02em' }}>
                {active.name}
              </h2>
              <span className="tag" style={{ marginLeft: 8 }}>
                {STATUS[active.status] ?? active.status}
              </span>
            </div>
            <div className="muted" style={{ fontSize: 12, marginTop: 3 }}>
              {active.title} · 汇报给 {active.reports_to ? (agents.find((x) => x.id === active.reports_to)?.code ?? active.reports_to) : '董事会'}
            </div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: '20px 22px' }}>
            {messages.length === 0 ? (
              <p className="note">还没有对话。你找 CxO 不必经过秘书；只有它的产出要回到你这里时，才走秘书。</p>
            ) : (
              <Transcript messages={messages} agents={agents} />
            )}
          </div>

          <div style={{ padding: '0 22px 22px' }}>
            <Composer agent={active} onSend={(b) => onSend(active.id, b)} compact />
          </div>
        </div>
      )}
    </div>
  )
}
