import type { Settings } from '../types'

const GATE: Record<string, { label: string; tone: string }> = {
  auto: { label: '放行', tone: 'ok' },
  notify: { label: '事后告知', tone: '' },
  approve: { label: '事前批准', tone: 'warn' },
  dual: { label: '双签', tone: 'warn' },
  deny: { label: '默认拒绝', tone: 'seal' },
}

export default function PolicyPanel({ policy }: { policy: Settings['policy'] }) {
  return (
    <>
      <dl className="kv" style={{ marginBottom: 22, maxWidth: 520 }}>
        <dt>版本</dt>
        <dd className="num">v{policy.version}</dd>
        <dt>生效</dt>
        <dd className="num">{policy.effective.slice(0, 10)}</dd>
        <dt>沙箱根</dt>
        <dd>{policy.folder_roots.join(' · ')}</dd>
      </dl>

      <table className="ledger">
        <caption>动作 × 门</caption>
        <thead>
          <tr>
            <th>#</th>
            <th>动作</th>
            <th>策略键</th>
            <th className="r">默认门</th>
            <th className="r">谁批</th>
          </tr>
        </thead>
        <tbody>
          {policy.rules.map((r, i) => {
            const g = GATE[r.gate] ?? { label: r.gate, tone: '' }
            return (
              <tr key={r.id}>
                <td className="idx num">{String(i + 1).padStart(2, '0')}</td>
                <td>{r.action}</td>
                <td className="mono muted" style={{ fontSize: 11 }}>
                  {r.id}
                </td>
                <td className="r">
                  <span className={`tag ${g.tone}`}>{g.label}</span>
                </td>
                <td className="r muted">{r.approver ?? '—'}</td>
              </tr>
            )
          })}
        </tbody>
      </table>

      <p className="note" style={{ marginTop: 18 }}>
        策略是文件，带版本号与生效时间。每次运行读取当前版本，运行中的不中途提权。
        改它要走决议并留审计，否则下一次运行不认。
      </p>
    </>
  )
}
