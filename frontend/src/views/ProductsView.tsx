import { useEffect, useState } from 'react'
import { getFinance, money } from '../api'
import type { Agent, Finance, Product } from '../types'

const KIND: Record<string, string> = { app: '应用', toy: '实体', media: '内容' }

export default function ProductsView({ products, agents }: { products: Product[]; agents: Agent[] }) {
  const [finance, setFinance] = useState<Finance | null>(null)
  const [open, setOpen] = useState<string | null>(products[0]?.id ?? null)

  useEffect(() => {
    getFinance().then(setFinance).catch(() => setFinance(null))
  }, [])

  const owner = (id: string) => agents.find((a) => a.id === id)?.code ?? id
  const selected = products.find((p) => p.id === open) ?? null
  const row = finance?.portfolio.find((p) => p.id === open) ?? null

  const selling = products.filter((p) => p.stage === '在售').length
  const building = products.filter((p) => p.stage === '开发').length

  return (
    <div className="view">
      <div className="summary">
        <div className="cell">
          <span className="k">产品</span>
          <span className="v">{products.length}</span>
        </div>
        <div className="cell">
          <span className="k">在售</span>
          <span className="v">{selling}</span>
        </div>
        <div className="cell">
          <span className="k">开发中</span>
          <span className="v">{building}</span>
        </div>
        <div className="cell">
          <span className="k">副业收入 · Q4</span>
          <span className="v">{finance ? money(finance.pl.side_revenue) : '—'}</span>
        </div>
        <span className="tag warn" style={{ marginLeft: 'auto' }}>
          沙箱示例
        </span>
      </div>

      <table className="ledger">
        <caption>产品组合 · {finance?.period ?? '本季'}</caption>
        <thead>
          <tr>
            <th>#</th>
            <th>产品</th>
            <th>线</th>
            <th>负责人</th>
            <th>阶段</th>
            <th style={{ width: '16%' }}>进度</th>
            <th>下一里程碑</th>
            <th className="r">日期</th>
          </tr>
        </thead>
        <tbody>
          {products.map((p, i) => (
            <tr
              key={p.id}
              data-selectable
              aria-selected={open === p.id}
              onClick={() => setOpen(open === p.id ? null : p.id)}
            >
              <td className="idx num">{String(i + 1).padStart(2, '0')}</td>
              <td>
                {p.name}
                <div className="tiny" style={{ marginTop: 2 }}>
                  {p.note}
                </div>
              </td>
              <td>
                <span className="tag">{KIND[p.kind] ?? p.kind}</span>
              </td>
              <td className="mono" style={{ fontSize: 11 }}>
                {owner(p.owner)}
              </td>
              <td className="muted">{p.stage}</td>
              <td>
                <div className="bar">
                  <i style={{ width: `${p.progress}%` }} />
                </div>
                <div className="num tiny" style={{ marginTop: 5 }}>
                  {p.progress}%
                </div>
              </td>
              <td>{p.milestone ?? '—'}</td>
              <td className="r num muted">{p.milestone_due ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {selected && (
        <div className="detail">
          <div>
            <div className="tiny">单位经济</div>
            {selected.kind === 'toy' ? (
              <dl className="kv" style={{ marginTop: 8 }}>
                <dt>售价</dt>
                <dd className="num">{money(selected.price_cents)}</dd>
                <dt>单件成本</dt>
                <dd className="num">{money(selected.unit_cost_cents)}</dd>
                <dt>单件毛利</dt>
                <dd className="num">{money(selected.price_cents - selected.unit_cost_cents)}</dd>
                <dt>库存</dt>
                <dd className="num">
                  {selected.inventory} 件 · {money(selected.inventory * selected.unit_cost_cents)}
                </dd>
              </dl>
            ) : (
              <p className="muted" style={{ marginTop: 8, fontSize: 12 }}>
                {selected.kind === 'media' ? '按商单计价，不按件。' : '软件边际成本近零，看订阅与留存。'}
              </p>
            )}
          </div>

          <div>
            <div className="tiny">本季损益</div>
            <dl className="kv" style={{ marginTop: 8 }}>
              <dt>收入</dt>
              <dd className="num">{row ? money(row.revenue) : '—'}</dd>
              <dt>成本</dt>
              <dd className="num">{row ? money(row.cost) : '—'}</dd>
              <dt>毛利</dt>
              <dd className="num">
                {row ? `${money(row.margin)} · ${row.margin_pct}%` : '—'}
              </dd>
            </dl>
          </div>

          <div>
            <div className="tiny">里程碑</div>
            <p style={{ marginTop: 8, fontSize: 13 }}>
              {selected.milestone}
              <span className="muted"> · {selected.milestone_due}</span>
            </p>
            <p className="muted" style={{ marginTop: 6, fontSize: 12 }}>
              由 {owner(selected.owner)} 负责。进度来自任务包验收，不手填。
            </p>
          </div>
        </div>
      )}

      <p className="note" style={{ marginTop: 18 }}>
        产品组合是 CEO 的看板，不是任务列表。每行只有一个负责人和下一个里程碑。
        实体产品的成本拆到单件，软件产品看订阅与留存。
      </p>
    </div>
  )
}
