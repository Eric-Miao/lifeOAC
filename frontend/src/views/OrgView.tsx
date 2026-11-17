import type { Agent } from '../types'

const W = 1000
const H = 250
const CHILD_W = 120
const CHILD_H = 60

const STATUS: Record<string, string> = {
  working: '在办',
  idle: '空闲',
  waiting: '等你批',
  blocked: '卡住',
}

const tone = (s: string) =>
  s === 'waiting' ? '#8A5A12' : s === 'working' ? '#2C6A4A' : s === 'blocked' ? '#A9352B' : '#B6B2A4'

export default function OrgView({
  agents,
  onOpen,
  selectedId,
}: {
  agents: Agent[]
  onOpen: (id: string) => void
  selectedId: string | null
}) {
  const ceos = agents.filter((a) => a.tier === 0)
  const reports = agents.filter((a) => a.tier === 1)

  const gap = (W - reports.length * CHILD_W) / (reports.length + 1)
  const centers = reports.map((_, i) => Math.round(gap + i * (CHILD_W + gap) + CHILD_W / 2))
  const busY = 112
  const childY = 136

  const ceoW = 164
  const ceoGap = 20
  const ceoTotal = ceos.length * ceoW + (ceos.length - 1) * ceoGap
  const ceoStart = (W - ceoTotal) / 2

  return (
    <div className="view">
      <div className="orgwrap">
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="组织图：两位联席 CEO 与七位直属负责人">
          <title>组织图</title>

          {ceos.map((a, i) => {
            const x = ceoStart + i * (ceoW + ceoGap)
            const cx = x + ceoW / 2
            return (
              <g
                key={a.id}
                className="orgnode"
                data-selected={selectedId === a.id}
                onClick={() => onOpen(a.id)}
                style={{ cursor: 'pointer' }}
                tabIndex={0}
                role="button"
                onKeyDown={(e) => e.key === 'Enter' && onOpen(a.id)}
              >
                <rect x={x} y={16} width={ceoW} height={60} rx={3} />
                <rect x={x + 10} y={28} width={5} height={5} fill={tone(a.status)} />
                <text x={x + 22} y={33} className="code">
                  {a.code}
                </text>
                <text x={x + 10} y={54} fontWeight={500} fontSize={13}>
                  {a.name}
                </text>
                <text x={x + 10} y={68} className="role">
                  联席 CEO · 董事
                </text>
                <path className="orglink" d={`M${cx} 76 V${busY}`} />
              </g>
            )
          })}

          <path className="orglink" d={`M${Math.min(...centers)} ${busY} H${Math.max(...centers)}`} />

          {reports.map((a, i) => {
            const x = centers[i] - CHILD_W / 2
            return (
              <g
                key={a.id}
                className="orgnode"
                data-selected={selectedId === a.id}
                onClick={() => onOpen(a.id)}
                style={{ cursor: 'pointer' }}
                tabIndex={0}
                role="button"
                onKeyDown={(e) => e.key === 'Enter' && onOpen(a.id)}
              >
                <path className="orglink" d={`M${centers[i]} ${busY} V${childY}`} />
                <rect x={x} y={childY} width={CHILD_W} height={CHILD_H} rx={3} />
                <rect x={x + 10} y={childY + 12} width={5} height={5} fill={tone(a.status)} />
                <text x={x + 22} y={childY + 17} className="code">
                  {a.code}
                </text>
                <text x={x + 10} y={childY + 38} fontWeight={500} fontSize={13}>
                  {a.name}
                </text>
                <text x={x + 10} y={childY + 52} className="role">
                  {STATUS[a.status] ?? a.status}
                </text>
              </g>
            )
          })}

          <text x={20} y={H - 10} className="code" fill="#646A60">
            派生自 agents 表与人事决议日志 · 不可手改
          </text>
        </svg>
      </div>

      <p className="note" style={{ marginTop: 16 }}>
        新增一个 CxO 走两步：先和秘书或 CHRO 定义 JD 与协作面，再在系统注册。注册会写一条人事决议，这张图随之刷新。
        审计不向 CEO 汇报，所以它画在同一层，线上却独立。
      </p>
    </div>
  )
}
