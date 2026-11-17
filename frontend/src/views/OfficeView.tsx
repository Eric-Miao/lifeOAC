import OfficeCanvas from '../components/OfficeCanvas'
import Drawer from '../components/Drawer'
import type { Agent, Approval, Message, State } from '../types'

const STATUS_LABEL: Record<string, string> = {
  working: '在办',
  idle: '空闲',
  waiting: '等你批',
  blocked: '卡住',
}

export default function OfficeView({
  state,
  selected,
  messages,
  onSelect,
  onSend,
  onResolve,
}: {
  state: State
  selected: Agent | null
  messages: Message[]
  onSelect: (id: string | null) => void
  onSend: (id: string, body: string) => Promise<void>
  onResolve: (id: number, d: 'approve' | 'reject') => Promise<void>
}) {
  const pending = state.approvals.length

  return (
    <div className="view">
      <div
        className="office-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: selected ? 'minmax(0, 1fr) 380px' : 'minmax(0, 1fr)',
          gap: 20,
          alignItems: 'start',
        }}
      >
        <div>
          <div className="stage">
            <OfficeCanvas
              agents={state.agents}
              approvals={state.approvals}
              selectedId={selected?.id ?? null}
              onSelect={onSelect}
            />
            <div className="stagebar">
              <div className="legend">
                <span>
                  <i className="dot working" /> 在办
                </span>
                <span>
                  <i className="dot idle" /> 空闲
                </span>
                <span>
                  <i className="dot waiting" /> 等你批
                </span>
                <span>
                  <i className="dot blocked" /> 卡住
                </span>
              </div>
              <span>点一个人 · 直接说话</span>
            </div>
          </div>

          <div className="roster" role="list" aria-label="高管名册">
            {state.agents.map((a) => (
              <button
                key={a.id}
                role="listitem"
                onClick={() => onSelect(a.id)}
                aria-pressed={selected?.id === a.id}
              >
                <i className={`dot ${a.status}`} />
                <span className="code num">{a.code}</span>
                <span className="nm">{a.name}</span>
                <span className="st">{STATUS_LABEL[a.status] ?? a.status}</span>
              </button>
            ))}
          </div>

          <p className="note" style={{ marginTop: 20 }}>
            {pending > 0
              ? `有 ${pending} 件事在等你。角色头顶的气泡就是它们，点开对应的人即可处理。`
              : '没有待批项。系统默认安静：没事的时候，它不找你。'}
          </p>
        </div>

        {selected && (
          <Drawer
            agent={selected}
            messages={messages}
            approvals={state.approvals as Approval[]}
            onSend={(body) => onSend(selected.id, body)}
            onResolve={onResolve}
            onClose={() => onSelect(null)}
          />
        )}
      </div>
    </div>
  )
}
