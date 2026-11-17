import { useState } from 'react'
import { clock } from '../api'
import type { Agent, AuditRow } from '../types'

const FILTERS = ['全部', 'allow', 'pending', 'deny'] as const

const DECISION: Record<string, string> = {
  allow: '放行',
  approved: '已批',
  pending: '待批',
  deny: '拒绝',
  rejected: '驳回',
}

export default function AuditView({ rows, agents }: { rows: AuditRow[]; agents: Agent[] }) {
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>('全部')
  const shown = filter === '全部' ? rows : rows.filter((r) => r.decision === filter)

  const name = (actor: string) => {
    if (actor === 'system') return '系统'
    if (actor === 'ceo-a') return '你'
    return agents.find((a) => a.id === actor)?.code ?? actor
  }

  return (
    <div className="view">
      <div className="filterbar">
        {FILTERS.map((f) => (
          <button key={f} onClick={() => setFilter(f)} aria-pressed={filter === f}>
            {f === '全部' ? '全部' : DECISION[f]}
          </button>
        ))}
        <span className="tiny" style={{ marginLeft: 'auto' }}>
          {shown.length} 条 · 只增不改
        </span>
      </div>

      <table className="ledger">
        <caption>审计日志</caption>
        <thead>
          <tr>
            <th>#</th>
            <th>时间</th>
            <th>谁</th>
            <th>做了什么</th>
            <th>对象</th>
            <th>策略</th>
            <th className="r">判定</th>
          </tr>
        </thead>
        <tbody>
          {shown.map((r) => (
            <tr key={r.id}>
              <td className="idx num">{String(r.id).padStart(3, '0')}</td>
              <td className="num muted" style={{ whiteSpace: 'nowrap' }}>
                {clock(r.ts)}
              </td>
              <td>{name(r.actor)}</td>
              <td>
                <span className="mono" style={{ fontSize: 11.5 }}>
                  {r.action}
                </span>
                {r.meta && <div className="tiny" style={{ marginTop: 2 }}>{r.meta}</div>}
              </td>
              <td className="muted">{r.target ?? '—'}</td>
              <td className="mono muted" style={{ fontSize: 11 }}>
                {r.policy ?? '—'}
              </td>
              <td className="r">
                <span className={`tag ${r.decision === 'allow' || r.decision === 'approved' ? 'ok' : r.decision === 'pending' ? 'warn' : 'seal'}`}>
                  {DECISION[r.decision] ?? r.decision}
                </span>
              </td>
            </tr>
          ))}
          {shown.length === 0 && (
            <tr>
              <td colSpan={7} className="muted" style={{ padding: '24px 0' }}>
                这个判定下还没有记录。
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <p className="note" style={{ marginTop: 18 }}>
        这张表是老板唯一不能改写的东西。审批、对外动作、花钱、改权限，全部落在这里；
        人可读，但只增不删。
      </p>
    </div>
  )
}
