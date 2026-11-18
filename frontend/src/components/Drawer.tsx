import { useEffect, useRef, useState } from 'react'
import { money, timeOnly } from '../api'
import type { Agent, Approval, ExecutionInfo, Message, PackageEvent, Run } from '../types'
import { IconClose, IconSend } from './Icons'

const senderLabel = (sender: string, agents: Agent[]) => {
  if (sender === 'user') return '你'
  const a = agents.find((x) => x.id === sender)
  return a ? `${a.code} · ${a.name}` : sender
}

export function Transcript({ messages, agents }: { messages: Message[]; agents: Agent[] }) {
  return (
    <div className="transcript">
      {messages.map((m) => (
        <div key={m.id} className={`msg ${m.sender === 'user' ? 'mine' : 'theirs'}`}>
          <div className="who">
            <span className="k">{senderLabel(m.sender, agents)}</span>
            <span>{timeOnly(m.ts)}</span>
            {m.kind === 'sandbox' && <span className="tag warn">沙箱</span>}
            {m.kind === 'real' && <span className="tag seal">真实执行</span>}
            {m.kind === 'seed' && <span className="tag">示例</span>}
          </div>
          <p style={{ whiteSpace: 'pre-wrap' }}>{m.body}</p>
        </div>
      ))}
    </div>
  )
}

export function Composer({
  agent,
  onSend,
  compact = false,
}: {
  agent: Agent
  onSend: (body: string) => Promise<void>
  compact?: boolean
}) {
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const ref = useRef<HTMLTextAreaElement>(null)

  const submit = async () => {
    const body = text.trim()
    if (!body || busy) return
    setBusy(true)
    try {
      await onSend(body)
      setText('')
    } finally {
      setBusy(false)
      ref.current?.focus()
    }
  }

  return (
    <div className="composer">
      <textarea
        ref={ref}
        value={text}
        placeholder={compact ? `给 ${agent.code} 一句话` : `给 ${agent.code} 下指令、问进度、要一份材料`}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            void submit()
          }
        }}
      />
      <div className="row">
        <span className="tiny">Enter 发送 · Shift+Enter 换行</span>
        <button className="btn primary" onClick={() => void submit()} disabled={!text.trim() || busy}>
          <IconSend /> {busy ? '发送中' : '发送'}
        </button>
      </div>
    </div>
  )
}

export function ApprovalCard({
  approval,
  onResolve,
}: {
  approval: Approval
  onResolve: (decision: 'approve' | 'reject') => Promise<void>
}) {
  const [busy, setBusy] = useState(false)
  const act = async (d: 'approve' | 'reject') => {
    setBusy(true)
    try {
      await onResolve(d)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="approval">
      <div className="who tiny">待你拍板 · {timeOnly(approval.ts)}</div>
      <div style={{ fontWeight: 500 }}>{approval.title}</div>
      {approval.detail && <p className="muted" style={{ fontSize: 12 }}>{approval.detail}</p>}
      {approval.amount_cents > 0 && <div className="amt">{money(approval.amount_cents)}</div>}
      <div className="row">
        <button className="btn seal" disabled={busy} onClick={() => void act('approve')}>
          批准
        </button>
        <button className="btn" disabled={busy} onClick={() => void act('reject')}>
          驳回
        </button>
        <span className="tiny" style={{ marginLeft: 'auto' }}>
          留痕 · 写审计
        </span>
      </div>
    </div>
  )
}

const RUN_LABEL: Record<string, string> = {
  running: '跑着',
  completed: '完成',
  failed: '失败',
  cancelled: '已取消',
}

const elapsed = (r: Run) => {
  const a = new Date(r.started_at).getTime()
  const b = r.finished_at ? new Date(r.finished_at).getTime() : Date.now()
  if (Number.isNaN(a) || Number.isNaN(b)) return ''
  const s = Math.max(0, Math.round((b - a) / 1000))
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m${s % 60}s`
}

function RunItem({ run, onCancel }: { run: Run; onCancel: (id: number) => Promise<void> }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="runitem">
      <div className="runhead">
        <span className={`dot ${run.status === 'completed' ? 'working' : run.status === 'failed' ? 'blocked' : run.status === 'running' ? 'waiting' : 'idle'}`} />
        <span className="mono" style={{ fontSize: 11 }}>
          {run.provider}
        </span>
        <span className="muted" style={{ fontSize: 12 }}>{RUN_LABEL[run.status] ?? run.status}</span>
        <span className="mono" style={{ marginLeft: 'auto', fontSize: 10, color: 'var(--muted)' }}>
          {elapsed(run)}
        </span>
      </div>
      <p className="runprompt">{run.prompt}</p>
      {(run.content || run.error) && (
        <>
          <button className="btn quiet" style={{ padding: 0 }} onClick={() => setOpen(!open)}>
            {open ? '收起结果' : '看结果'}
          </button>
          {open && <pre className="runout">{run.content || run.error}</pre>}
        </>
      )}
      {run.status === 'running' && (
        <button className="btn" style={{ marginTop: 6 }} onClick={() => void onCancel(run.id)}>
          取消
        </button>
      )}
    </div>
  )
}

export default function Drawer({
  agent,
  messages,
  approvals,
  runs,
  packages,
  execution,
  onSend,
  onResolve,
  onStartRun,
  onCancelRun,
  onClose,
}: {
  agent: Agent
  messages: Message[]
  approvals: Approval[]
  runs: Run[]
  packages: PackageEvent[]
  execution: ExecutionInfo
  onSend: (body: string) => Promise<void>
  onResolve: (id: number, decision: 'approve' | 'reject') => Promise<void>
  onStartRun: (provider: string, prompt: string) => Promise<void>
  onCancelRun: (id: number) => Promise<void>
  onClose: () => void
}) {
  const [tab, setTab] = useState<'chat' | 'role' | 'task' | 'run'>('chat')
  const [prompt, setPrompt] = useState('')
  const [provider, setProvider] = useState('')
  const [busy, setBusy] = useState(false)
  const bodyRef = useRef<HTMLDivElement>(null)

  const usable = execution.providers.filter((p) => p.available)
  const mine = runs.filter((r) => r.agent_id === agent.id)

  useEffect(() => {
    setTab('chat')
    setProvider('')
  }, [agent.id])

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight
  }, [messages, tab])

  const pending = approvals.filter((a) => a.agent_id === agent.id)
  const minePkgs = packages.filter((p) => p.owner === agent.id)
  const activeProvider = provider || usable[0]?.provider || ''

  return (
    <aside className="sheet" aria-label={`${agent.code} 详情`}>
      <div className="sheet-head" style={{ position: 'relative' }}>
        <div className="who">
          <span className="code">{agent.code}</span>
          <h2>
            {tab === 'role' ? '岗位' : tab === 'task' ? '任务' : tab === 'run' ? '派活' : agent.name}
          </h2>
        </div>
        <div className="role">{agent.title}</div>
        <button className="btn quiet close" onClick={onClose} aria-label="关闭">
          <IconClose />
        </button>
      </div>

      <div className="tabs" role="tablist">
        {(
          [
            ['chat', '对话'],
            ['run', '派活'],
            ['role', '岗位'],
            ['task', '任务'],
          ] as const
        ).map(([k, label]) => (
          <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)}>
            {label}
            {k === 'task' && pending.length > 0 ? ` · ${pending.length}` : ''}
            {k === 'run' && mine.some((r) => r.status === 'running') ? ' · •' : ''}
          </button>
        ))}
      </div>

      <div className="sheet-body" ref={bodyRef}>
        {tab === 'chat' && (
          <>
            {pending.map((a) => (
              <ApprovalCard key={a.id} approval={a} onResolve={(d) => onResolve(a.id, d)} />
            ))}
            {messages.length === 0 ? (
              <p className="note">
                还没有对话。所有对外消息先过秘书；你和 {agent.code} 之间可以直接说话，不用排队。
              </p>
            ) : (
              <Transcript messages={messages} agents={[agent]} />
            )}
          </>
        )}

        {tab === 'run' && (
          <>
            <p className="note" style={{ marginBottom: 14 }}>
              {execution.available
                ? '真实执行：会把这一句交给本地 CLI，子代理在你给的工作区里动手。花模型额度。'
                : '没装 AutoSwarm，派活不可用。沙箱对话仍然能用。'}
            </p>

            <div className="providers">
              {usable.map((p) => (
                <button
                  key={p.provider}
                  className="chip"
                  aria-pressed={activeProvider === p.provider}
                  onClick={() => setProvider(p.provider)}
                >
                  {p.provider}
                </button>
              ))}
              {usable.length === 0 && <span className="tiny">没有可用的 CLI</span>}
            </div>

            <textarea
              className="runinput"
              value={prompt}
              placeholder={`让 ${agent.code} 派一个子代理去做：写清楚交付物、验收标准`}
              onChange={(e) => setPrompt(e.target.value)}
            />
            <div className="row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
              <span className="tiny">真实执行 · 会写审计</span>
              <button
                className="btn primary"
                disabled={!prompt.trim() || !activeProvider || busy}
                onClick={async () => {
                  setBusy(true)
                  try {
                    await onStartRun(activeProvider, prompt.trim())
                    setPrompt('')
                  } finally {
                    setBusy(false)
                  }
                }}
              >
                {busy ? '派发中' : '派任务'}
              </button>
            </div>

            <div style={{ marginTop: 20 }}>
              {mine.length === 0 ? (
                <p className="note">还没派过真实任务。</p>
              ) : (
                mine.map((r) => <RunItem key={r.id} run={r} onCancel={onCancelRun} />)
              )}
            </div>
          </>
        )}

        {tab === 'role' && (
          <dl className="kv">
            <dt>岗位</dt>
            <dd>{agent.title}</dd>
            <dt>汇报</dt>
            <dd>{agent.reports_to ?? '董事会'}</dd>
            <dt>范围</dt>
            <dd>{agent.scope}</dd>
            <dt>对什么负责</dt>
            <dd>{agent.kpi}</dd>
            <dt>当前</dt>
            <dd>{agent.task ?? '没有在办的任务'}</dd>
            <dt>权限</dt>
            <dd className="muted">按 policy v7：目录内可读写，对外与花钱需审批。</dd>
          </dl>
        )}

        {tab === 'task' && (
          <>
            {minePkgs.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div className="tiny" style={{ marginBottom: 6 }}>
                  任务包
                </div>
                {minePkgs.map((p) => (
                  <div key={p.id} className="runitem">
                    <div className="runhead">
                      <span className="dot waiting" />
                      <span style={{ fontSize: 12.5 }}>{p.label}</span>
                      <span className="mono" style={{ marginLeft: 'auto', fontSize: 10, color: 'var(--muted)' }}>
                        {p.deadline}
                      </span>
                    </div>
                    <p className="runprompt">验收：{p.acceptance}</p>
                    {p.go_nogo && <p className="tiny">不通过：{p.go_nogo}</p>}
                  </div>
                ))}
              </div>
            )}
            {pending.length === 0 ? (
              <p className="note">
                当前没有待批项。任务包由会议编译，{agent.code} 只负责判断与分派，不亲手执行。
              </p>
            ) : (
              pending.map((a) => (
                <ApprovalCard key={a.id} approval={a} onResolve={(d) => onResolve(a.id, d)} />
              ))
            )}
            <dl className="kv" style={{ marginTop: 16 }}>
              <dt>在办</dt>
              <dd>{agent.task ?? '—'}</dd>
              <dt>状态</dt>
              <dd>{agent.status}</dd>
            </dl>
          </>
        )}
      </div>

      {tab === 'chat' && <Composer agent={agent} onSend={async (b) => { await onSend(b) }} />}
    </aside>
  )
}
