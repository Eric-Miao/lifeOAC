import { useEffect, useState } from 'react'
import { getSettings, money, runDreaming } from '../api'
import type { Settings } from '../types'
import PolicyPanel from './PolicyPanel'

const TABS = [
  ['policy', '权限'],
  ['billing', 'Billing'],
  ['memory', 'Memory'],
  ['plugins', 'Plugins'],
  ['connectors', 'Connectors'],
  ['notify', '通知'],
] as const

type Tab = (typeof TABS)[number][0]

const LEVEL: Record<string, string> = { 实时: 'seal', 简报: 'ok', 关闭: '' }
const KIND: Record<string, string> = { data: '数据', chat: '消息', work: '工作', money: '资金' }

export default function SettingsView() {
  const [tab, setTab] = useState<Tab>('policy')
  const [s, setS] = useState<Settings | null>(null)
  const [dreaming, setDreaming] = useState(false)

  useEffect(() => {
    getSettings().then(setS).catch(() => setS(null))
  }, [])

  if (!s) return <div className="view"><p className="note">读取配置…</p></div>

  const spent = Math.min(100, Math.round((s.billing.spent_cents / s.billing.cap_cents) * 100))

  return (
    <div className="view">
      <div className="subtabs" role="tablist">
        {TABS.map(([k, label]) => (
          <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)}>
            {label}
          </button>
        ))}
      </div>

      {tab === 'policy' && <PolicyPanel policy={s.policy} />}

      {tab === 'billing' && (
        <>
          <div className="summary">
            <div className="cell">
              <span className="k">提供方</span>
              <span className="v" style={{ fontSize: 14 }}>
                {s.billing.provider}
              </span>
            </div>
            <div className="cell">
              <span className="k">模型</span>
              <span className="v" style={{ fontSize: 14 }}>
                {s.billing.model}
              </span>
            </div>
            <div className="cell">
              <span className="k">本季用量</span>
              <span className="v">
                {money(s.billing.spent_cents)} / {money(s.billing.cap_cents)}
              </span>
            </div>
            <span className="tag warn" style={{ marginLeft: 'auto' }}>
              系统开销，不是公司财务
            </span>
          </div>

          <div className="bar" style={{ marginBottom: 26 }}>
            <i className={spent > 80 ? 'over' : ''} style={{ width: `${spent}%` }} />
          </div>

          <table className="ledger">
            <caption>按 CxO 归集</caption>
            <thead>
              <tr>
                <th>#</th>
                <th>调用方</th>
                <th className="r">次数</th>
                <th className="r">金额</th>
                <th style={{ width: 220 }}>占比</th>
              </tr>
            </thead>
            <tbody>
              {s.billing.by_agent.map((b, i) => (
                <tr key={b.agent}>
                  <td className="idx num">{String(i + 1).padStart(2, '0')}</td>
                  <td className="mono" style={{ fontSize: 11.5 }}>
                    {b.agent}
                  </td>
                  <td className="r num">{b.calls}</td>
                  <td className="r num">{money(b.cents)}</td>
                  <td>
                    <div className="bar">
                      <i style={{ width: `${(b.cents / s.billing.spent_cents) * 100}%` }} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <table className="ledger" style={{ marginTop: 28 }}>
            <caption>凭证</caption>
            <tbody>
              {s.billing.keys.map((k, i) => (
                <tr key={k.name}>
                  <td className="idx num">{String(i + 1).padStart(2, '0')}</td>
                  <td className="mono" style={{ fontSize: 11.5 }}>
                    {k.name}
                  </td>
                  <td className="mono muted" style={{ fontSize: 11.5 }}>
                    {k.masked}
                  </td>
                  <td className="r">
                    <span className={`tag ${k.status === 'ok' ? 'ok' : 'warn'}`}>
                      {k.status === 'ok' ? '已配置' : '缺失'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <p className="note" style={{ marginTop: 18 }}>
            Billing 只回答一个问题：这套系统自己烧了多少钱。公司赚多少、花多少，去「财务」标签。
            凭证不进 agent 环境，由代理层注入。
          </p>
        </>
      )}

      {tab === 'memory' && (
        <>
          <div className="summary">
            <div className="cell">
              <span className="k">命名空间</span>
              <span className="v">{s.memory.namespaces.length}</span>
            </div>
            <div className="cell">
              <span className="k">待写入</span>
              <span className="v">{s.memory.pending}</span>
            </div>
            <div className="cell">
              <span className="k">上次整理</span>
              <span className="v" style={{ fontSize: 13 }}>
                {s.memory.dreaming.last}
              </span>
            </div>
            <button
              className="btn"
              style={{ marginLeft: 'auto' }}
              disabled={dreaming}
              onClick={async () => {
                setDreaming(true)
                await runDreaming()
                setDreaming(false)
              }}
            >
              {dreaming ? '整理中…' : '立即整理'}
            </button>
          </div>

          <table className="ledger">
            <caption>记忆分层</caption>
            <thead>
              <tr>
                <th>#</th>
                <th>命名空间</th>
                <th className="r">文档</th>
                <th className="r">token</th>
                <th className="r">最后更新</th>
              </tr>
            </thead>
            <tbody>
              {s.memory.namespaces.map((n, i) => (
                <tr key={n.name}>
                  <td className="idx num">{String(i + 1).padStart(2, '0')}</td>
                  <td className="mono" style={{ fontSize: 11.5 }}>
                    {n.name}
                  </td>
                  <td className="r num">{n.docs}</td>
                  <td className="r num">{n.tokens.toLocaleString('zh-CN')}</td>
                  <td className="r num muted" style={{ fontSize: 11 }}>
                    {n.updated}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <p className="note" style={{ marginTop: 18 }}>
            下次整理 {s.memory.dreaming.next} · 上轮保留 {s.memory.dreaming.kept} 条、丢弃 {s.memory.dreaming.dropped} 条。
            整理只动记忆，不动个人数据：文件即真相，日志只存指针。
          </p>
        </>
      )}

      {tab === 'plugins' && (
        <>
          <table className="ledger">
            <caption>已装载的能力包</caption>
            <thead>
              <tr>
                <th>#</th>
                <th>插件</th>
                <th>版本</th>
                <th>声明的 scope</th>
                <th className="r">归属</th>
                <th className="r">状态</th>
              </tr>
            </thead>
            <tbody>
              {s.plugins.map((p, i) => (
                <tr key={p.id}>
                  <td className="idx num">{String(i + 1).padStart(2, '0')}</td>
                  <td>
                    {p.name}
                    <div className="tiny" style={{ marginTop: 2 }}>{p.id}</div>
                  </td>
                  <td className="num muted">{p.version}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      {p.scopes.map((sc) => (
                        <span key={sc} className="tag">
                          {sc}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="r mono" style={{ fontSize: 11 }}>
                    {p.owner}
                  </td>
                  <td className="r">
                    <span className={`tag ${p.status === 'on' ? 'ok' : ''}`}>{p.status === 'on' ? '启用' : '停用'}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <p className="note" style={{ marginTop: 18 }}>
            安装一个插件＝授予一组能力。manifest 必须声明 scope，装它和改权限走同一道审批。
          </p>
        </>
      )}

      {tab === 'connectors' && (
        <>
          <table className="ledger">
            <caption>外部连接</caption>
            <thead>
              <tr>
                <th>#</th>
                <th>连接</th>
                <th>类型</th>
                <th>目标</th>
                <th className="r">最后同步</th>
                <th className="r">状态</th>
              </tr>
            </thead>
            <tbody>
              {s.connectors.map((c, i) => (
                <tr key={c.id}>
                  <td className="idx num">{String(i + 1).padStart(2, '0')}</td>
                  <td>{c.name}</td>
                  <td>
                    <span className="tag">{KIND[c.kind] ?? c.kind}</span>
                  </td>
                  <td className="mono muted" style={{ fontSize: 11 }}>
                    {c.detail}
                  </td>
                  <td className="r num muted" style={{ fontSize: 11 }}>
                    {c.last}
                  </td>
                  <td className="r">
                    <span
                      className={`tag ${c.status === 'connected' ? 'ok' : c.status === 'manual' ? 'warn' : ''}`}
                    >
                      {c.status === 'connected' ? '已连接' : c.status === 'manual' ? '人工回填' : '未连接'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <p className="note" style={{ marginTop: 18 }}>
            银行流水与库存属于外部系统，先人工回填或走插件。系统只存带时间戳的快照，不假装是实时真相。
          </p>
        </>
      )}

      {tab === 'notify' && (
        <>
          <dl className="kv" style={{ marginBottom: 22, maxWidth: 420 }}>
            <dt>日报时间</dt>
            <dd className="num">{s.notifications.brief_at}</dd>
            <dt>默认原则</dt>
            <dd className="muted">宁可少说，不可多说。信任靠每次开口都挣。</dd>
          </dl>

          <div className="twocol">
            <div>
              <div className="plhead">
                <span>渠道</span>
                <span className="muted">从哪里找你</span>
              </div>
              <table className="ledger">
                <tbody>
                  {s.notifications.channels.map((c, i) => (
                    <tr key={c.name}>
                      <td className="idx num">{String(i + 1).padStart(2, '0')}</td>
                      <td>{c.name}</td>
                      <td className="r">
                        <span className={`tag ${LEVEL[c.level] ?? ''}`}>{c.level}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div>
              <div className="plhead">
                <span>来源</span>
                <span className="muted">什么值得打扰</span>
              </div>
              <table className="ledger">
                <tbody>
                  {s.notifications.sources.map((c, i) => (
                    <tr key={c.name}>
                      <td className="idx num">{String(i + 1).padStart(2, '0')}</td>
                      <td>{c.name}</td>
                      <td className="r">
                        <span className={`tag ${LEVEL[c.level] ?? ''}`}>{c.level}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <p className="note" style={{ marginTop: 18 }}>
            实时＝立刻打断。简报＝并进每日一次。关闭＝只进审计，不推送。默认安静。
          </p>
        </>
      )}
    </div>
  )
}
