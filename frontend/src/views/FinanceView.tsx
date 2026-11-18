import { useEffect, useState } from 'react'
import { getFinance, money } from '../api'
import type { Agent, Approval, DecisionEvent, Finance } from '../types'

const KIND: Record<string, string> = { app: '应用', toy: '实体', media: '内容' }

const pct = (a: number, b: number) => (b > 0 ? Math.round((a / b) * 100) : 0)

function PlRow({ label, note, amount }: { label: string; note?: string | null; amount: number }) {
  return (
    <tr>
      <td className="idx" />
      <td>{label}</td>
      <td className="note-col">{note ?? ''}</td>
      <td className="r num">{money(amount)}</td>
    </tr>
  )
}

export default function FinanceView({
  approvals,
  agents,
  decisions,
  onResolve,
}: {
  approvals: Approval[]
  agents: Agent[]
  decisions: DecisionEvent[]
  onResolve: (id: number, d: 'approve' | 'reject') => Promise<void>
}) {
  const [f, setF] = useState<Finance | null>(null)
  const [busy, setBusy] = useState<number | null>(null)

  useEffect(() => {
    getFinance().then(setF).catch(() => setF(null))
  }, [approvals.length])

  if (!f) return <div className="view"><p className="note">正在结账…</p></div>

  const owner = (id: string) => agents.find((a) => a.id === id)?.code ?? id

  return (
    <div className="view">
      <div className="summary">
        <div className="cell">
          <span className="k">收入 · {f.period}</span>
          <span className="v">{money(f.pl.total_revenue)}</span>
        </div>
        <div className="cell">
          <span className="k">净利</span>
          <span className="v">{money(f.pl.net)}</span>
        </div>
        <div className="cell">
          <span className="k">现金</span>
          <span className="v">{money(f.cash.closing)}</span>
        </div>
        <div className="cell">
          <span className="k">断粮 runway</span>
          <span className="v">{f.cash.runway_months} 个月</span>
        </div>
        <span className="tag warn" style={{ marginLeft: 'auto' }}>
          沙箱示例
        </span>
      </div>

      <div className="plhead">
        <span>损益表 · {f.period}</span>
        <span className="muted">
          主业占收入 {f.pl.salary_share}% · 副业 {money(f.pl.side_revenue)}
        </span>
      </div>

      <table className="ledger stmt">
        <thead>
          <tr>
            <th />
            <th>科目</th>
            <th className="r">备注</th>
            <th className="r">金额</th>
          </tr>
        </thead>
        <tbody>
          <tr className="sect">
            <td className="idx" />
            <td>营业收入</td>
            <td className="note-col" />
            <td className="r">{money(f.pl.total_revenue)}</td>
          </tr>
          {f.pl.revenue.map((l) => (
            <PlRow key={l.id} label={l.label} note={l.note} amount={l.amount_cents} />
          ))}
          <tr className="sect">
            <td className="idx" />
            <td>营业成本</td>
            <td className="note-col" />
            <td className="r">{money(f.pl.total_cogs)}</td>
          </tr>
          {f.pl.cogs.map((l) => (
            <PlRow key={l.id} label={l.label} amount={l.amount_cents} />
          ))}
          <tr className="total">
            <td className="idx" />
            <td>毛利 · {f.pl.gross_pct}%</td>
            <td className="note-col" />
            <td className="r num">{money(f.pl.gross)}</td>
          </tr>
          <tr className="sect">
            <td className="idx" />
            <td>期间费用</td>
            <td className="note-col" />
            <td className="r">{money(f.pl.total_opex)}</td>
          </tr>
          {f.pl.opex.map((l) => (
            <PlRow key={l.id} label={l.label} amount={l.amount_cents} />
          ))}
          <tr className="total">
            <td className="idx" />
            <td>净利 · {f.pl.net_pct}%</td>
            <td className="note-col" />
            <td className="r num">{money(f.pl.net)}</td>
          </tr>
        </tbody>
      </table>

      <div className="twocol">
        <div>
          <div className="plhead" style={{ marginTop: 0 }}>
            <span>现金流</span>
            <span className="muted">按收付实现</span>
          </div>
          <table className="ledger stmt">
            <tbody>
              <PlRow label="期初现金" amount={f.cash.opening} />
              <PlRow label="流入" note="全部营业收入" amount={f.cash.inflow} />
              <PlRow label="流出" note="成本 + 费用" amount={-f.cash.outflow} />
              <tr className="total">
                <td className="idx" />
                <td>期末现金</td>
                <td className="note-col" />
                <td className="r num">{money(f.cash.closing)}</td>
              </tr>
            </tbody>
          </table>
          <p className="tiny" style={{ marginTop: 10 }}>
            月烧 {money(f.cash.monthly_burn)} · 断掉主业还能活 {f.cash.runway_months} 个月
          </p>
        </div>

        <div>
          <div className="plhead">
            <span>资产负债表</span>
            <span className="muted">期末</span>
          </div>
          <table className="ledger stmt">
            <tbody>
              <tr className="sect">
                <td className="idx" />
                <td>资产</td>
                <td className="note-col" />
                <td />
              </tr>
              {f.balance.assets.map((a) => (
                <PlRow key={a.label} label={a.label} amount={a.amount} />
              ))}
              <tr className="sect">
                <td className="idx" />
                <td>负债</td>
                <td className="note-col" />
                <td />
              </tr>
              {f.balance.liabilities.map((l) => (
                <PlRow key={l.label} label={l.label} amount={l.amount_cents} />
              ))}
              <tr className="total">
                <td className="idx" />
                <td>权益</td>
                <td className="note-col" />
                <td className="r num">{money(f.balance.equity)}</td>
              </tr>
            </tbody>
          </table>
          <p className="tiny" style={{ marginTop: 10 }}>
            资产 {money(f.balance.assets_total)} · 负债 {money(f.balance.liabilities_total)}
          </p>
        </div>
      </div>

      <div className="plhead" style={{ marginTop: 30 }}>
        <span>项目成本与毛利</span>
        <span className="muted">实体拆到单件，软件看订阅</span>
      </div>

      <table className="ledger">
        <thead>
          <tr>
            <th>#</th>
            <th>项目</th>
            <th>线</th>
            <th>负责人</th>
            <th className="r">收入</th>
            <th className="r">成本</th>
            <th className="r">毛利</th>
            <th className="r" style={{ width: 92 }}>毛利率</th>
          </tr>
        </thead>
        <tbody>
          {f.portfolio.map((p, i) => (
            <tr key={p.id}>
              <td className="idx num">{String(i + 1).padStart(2, '0')}</td>
              <td>
                {p.name}
                {p.kind === 'toy' && (
                  <div className="tiny" style={{ marginTop: 2 }}>
                    库存 {p.inventory} 件 · 占用 {money(p.stock_value)}
                  </div>
                )}
              </td>
              <td>
                <span className="tag">{KIND[p.kind] ?? p.kind}</span>
              </td>
              <td className="mono" style={{ fontSize: 11 }}>
                {owner(p.owner)}
              </td>
              <td className="r num">{money(p.revenue)}</td>
              <td className="r num">{money(p.cost)}</td>
              <td className="r num">{money(p.margin)}</td>
              <td>
                <div className="num" style={{ fontSize: 11, textAlign: 'right' }}>
                  {p.margin_pct}%
                </div>
                <div className="bar" style={{ marginTop: 4 }}>
                  <i className={p.margin_pct < 30 ? 'over' : ''} style={{ width: `${Math.max(0, p.margin_pct)}%` }} />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="plhead" style={{ marginTop: 30 }}>
        <span>决议</span>
        <span className="muted">{decisions.length} 条 · 只能被后续决议 supersede</span>
      </div>

      {decisions.length === 0 ? (
        <p className="note">还没有决议。ECE 开过之后，这里会记录每一笔额度与取舍。</p>
      ) : (
        <table className="ledger stmt">
          <tbody>
            {decisions.map((d, i) => (
              <tr key={d.id}>
                <td className="idx num">{String(i + 1).padStart(2, '0')}</td>
                <td>{d.label}</td>
                <td className="note-col">
                  {d.period} · {d.actor}
                </td>
                <td className="r num">
                  {d.amount_cents ? money(d.amount_cents) : `${d.hours}h`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="plhead" style={{ marginTop: 30 }}>
        <span>待批</span>
        <span className="muted">{approvals.length} 件</span>
      </div>

      {approvals.length === 0 ? (
        <p className="note">没有待批。财务这边安静，说明没有人正在花你的钱。</p>
      ) : (
        <table className="ledger">
          <tbody>
            {approvals.map((a, i) => (
              <tr key={a.id}>
                <td className="idx num">{String(i + 1).padStart(2, '0')}</td>
                <td>
                  {a.title}
                  <div className="tiny" style={{ marginTop: 2 }}>{a.detail}</div>
                </td>
                <td className="mono" style={{ fontSize: 11 }}>
                  {owner(a.agent_id)}
                </td>
                <td className="r num">{a.amount_cents ? money(a.amount_cents) : '—'}</td>
                <td className="r" style={{ width: 160 }}>
                  <button
                    className="btn seal"
                    disabled={busy === a.id}
                    onClick={async () => {
                      setBusy(a.id)
                      await onResolve(a.id, 'approve')
                      setBusy(null)
                    }}
                  >
                    批准
                  </button>{' '}
                  <button
                    className="btn"
                    disabled={busy === a.id}
                    onClick={async () => {
                      setBusy(a.id)
                      await onResolve(a.id, 'reject')
                      setBusy(null)
                    }}
                  >
                    驳回
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <p className="note" style={{ marginTop: 18 }}>
        三张表从同一份流水现算，不手填。利润不是现金：主业工资是现金牛，副业才是期权。
        {pct(f.pl.side_revenue, f.pl.total_revenue)}% 的收入来自副业，这个比例才是这家公司真正的进度条。
      </p>
    </div>
  )
}
