import { money } from '../api'
import type { Agent, Budget } from '../types'

const pct = (a: number, b: number) => (b > 0 ? Math.min(100, (a / b) * 100) : 0)

export default function BillingView({ budgets, agents }: { budgets: Budget[]; agents: Agent[] }) {
  const owner = (id: string) => agents.find((a) => a.id === id)?.code ?? id
  const moneyTotal = budgets.reduce((s, b) => s + b.money_cents, 0)
  const moneySpent = budgets.reduce((s, b) => s + b.money_spent, 0)
  const hourTotal = budgets.reduce((s, b) => s + b.hours, 0)
  const hourSpent = budgets.reduce((s, b) => s + b.hours_spent, 0)

  return (
    <div className="view">
      <div className="summary">
        <div className="cell">
          <span className="k">本季可用</span>
          <span className="v">{money(moneyTotal - moneySpent)}</span>
        </div>
        <div className="cell">
          <span className="k">已用</span>
          <span className="v">{money(moneySpent)}</span>
        </div>
        <div className="cell">
          <span className="k">小时额度</span>
          <span className="v">
            {hourSpent} / {hourTotal}
          </span>
        </div>
        <div className="cell">
          <span className="k">科目</span>
          <span className="v">{budgets.length}</span>
        </div>
        <span className="tag warn" style={{ marginLeft: 'auto' }}>
          沙箱示例
        </span>
      </div>

      <table className="ledger">
        <caption>双币预算 · 2026 Q4</caption>
        <thead>
          <tr>
            <th>#</th>
            <th>科目</th>
            <th>负责人</th>
            <th style={{ width: '26%' }}>钱</th>
            <th style={{ width: '18%' }}>小时</th>
            <th className="r">余额</th>
          </tr>
        </thead>
        <tbody>
          {budgets.map((b, i) => {
            const m = pct(b.money_spent, b.money_cents)
            const h = pct(b.hours_spent, b.hours)
            const over = m > 90
            return (
              <tr key={b.id}>
                <td className="idx num">{String(i + 1).padStart(2, '0')}</td>
                <td>
                  {b.name}
                  <div className="tiny" style={{ marginTop: 2 }}>{b.id}</div>
                </td>
                <td className="mono" style={{ fontSize: 11 }}>
                  {owner(b.owner)}
                </td>
                <td>
                  <div className="bar" aria-label={`已用 ${Math.round(m)}%`}>
                    <i className={over ? 'over' : ''} style={{ width: `${m}%` }} />
                  </div>
                  <div className="num tiny" style={{ marginTop: 5 }}>
                    {money(b.money_spent)} / {money(b.money_cents)}
                  </div>
                </td>
                <td>
                  {b.hours > 0 ? (
                    <>
                      <div className="bar">
                        <i style={{ width: `${h}%` }} />
                      </div>
                      <div className="num tiny" style={{ marginTop: 5 }}>
                        {b.hours_spent}h / {b.hours}h
                      </div>
                    </>
                  ) : (
                    <span className="muted tiny">不计工时</span>
                  )}
                </td>
                <td className="r num">{money(b.money_cents - b.money_spent)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>

      <p className="note" style={{ marginTop: 18 }}>
        每个项目同时持有钱与小时两种额度。小时是真正的硬约束：钱可以再赚，时间不能。
        系统自身的运营成本单列为「system」，不与任何业务混用。
      </p>
    </div>
  )
}
