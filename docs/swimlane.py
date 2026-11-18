"""生成 docs/swimlane.html：七个场景在六个节点上的 I/O 与终点。"""

from pathlib import Path

LANES = [
    ("你 · 需求发出", 132),
    ("秘书 · 路由", 172),
    ("CxO · 分派", 214),
    ("执行 / 工具", 196),
    ("写回", 176),
    ("停在哪", 166),
]

ROWS = [
    (
        "a",
        "年初 ECE",
        [
            ["I 一句话：开年 ECE", "O 定预算与营收目标"],
            ["I 听到这句", "O 反问：补 26 还是 27", "O 列材料包，承诺签字页", "× 未落库"],
            ["× 没有会议引擎", "没有议程 / 决议对象"],
            ["× 无"],
            ["× 0 条 decision", "预算仍是种子数据"],
            ["停在秘书的追问", "会议没开成"],
        ],
    ),
    (
        "b",
        "喝水 app",
        [
            ["I 需求 + 本周可验收", "O 一句话"],
            ["直达 CPTO，未过秘书", "（本场景未走秘书）"],
            ["I 需求", "O 范围 + 5 条验收标准", "O 派子任务"],
            ["I 自然语言任务", "O call_id → completed", "O 工作区写出 README"],
            ["O 对话消息（真实执行）", "× 无 product 事件"],
            ["有产物，没立项", "产品表没有新行"],
        ],
    ),
    (
        "c",
        "元旦去泰国",
        [
            ["I 「元旦去泰国」", "O 一句话"],
            ["不经过（直接找 CHRO）", ""],
            ["I 出行需求", "O 反问人数 / 预算 / 护照", "O 承诺拉比价"],
            ["× 等输入，未启动"],
            ["× 无支出事件", "× 无时间占用"],
            ["停在 CHRO 的追问", "假期与预算没有账"],
        ],
    ),
    (
        "d",
        "腊肠狗哑铃",
        [
            ["I 「做个腊肠狗哑铃」", "O 一句话"],
            ["I 新产品请求", "O 路由 COO / 财务 / 品牌", "O 只留四个问题给 CEO", "× 未开待批"],
            ["× 没有真正分派", "（只是口头说派）"],
            ["× 无"],
            ["× 无 approval", "× 无 product"],
            ["停在路由", "谁牵头说清了，事没动"],
        ],
    ),
    (
        "e",
        "今天的简报",
        [
            ["I 要一份 AI 简报", "O 一句话"],
            ["I 简报请求", "O 「没有可引用记录」", "× 看不到 CFO 的账", "× 看不到待批"],
            ["CFO 线程里已记 ¥300", "（另一条线，未共享）"],
            ["× 无"],
            ["账在 events 表", "秘书没有读权限"],
            ["停在可见性", "写进去了，读不出来"],
        ],
    ),
    (
        "f",
        "打工人规划",
        [
            ["I 问 26Q4/27H1 做什么", "O 一句话"],
            ["I 规划询问", "O 「没有这个产品，不编」", "O 反问三句话", "√ 正确承认缺失"],
            ["× 未编造"],
            ["× 无"],
            ["× 无"],
            ["正确地停下", "这是本次唯一全过的场景"],
        ],
    ),
    (
        "g",
        "半年度 ECE",
        [
            ["I 开半年会、复盘 H1", "O 一句话"],
            ["I 会议请求", "O 指出：11 月复盘 H1 已过", "O 建议口径 + 三张签字页", "× 未落库"],
            ["× 无"],
            ["× 无"],
            ["× 0 条 decision", "× 预算无版本"],
            ["停在秘书的追问", "同 a"],
        ],
    ),
]

W_RAIL = 104
MARGIN = 24
ROW_H = 84
GAP = 8
HEAD_H = 44
LINE = 12
FS = 10


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    lane_x = [W_RAIL]
    for _, w in LANES:
        lane_x.append(lane_x[-1] + w + GAP)
    total_w = lane_x[-1] - GAP + MARGIN
    body_h = HEAD_H + 10 + len(ROWS) * (ROW_H + GAP)
    total_h = body_h + 46

    out = []
    out.append(f'<svg viewBox="0 0 {total_w} {total_h}" width="100%" role="img" aria-label="七个场景的泳道图：从需求到写入，再到停在哪里">')
    out.append("<defs><marker id='ar' viewBox='0 0 6 6' refX='5' refY='3' markerWidth='5' markerHeight='5' orient='auto'>"
               "<path d='M0 0 L6 3 L0 6 z' fill='#9a9f94'/></marker></defs>")

    # lane headers
    for i, (name, w) in enumerate(LANES):
        x = lane_x[i]
        last = i == len(LANES) - 1
        out.append(f'<text x="{x}" y="18" class="lane{" stop" if last else ""}">{esc(name)}</text>')
        out.append(f'<line x1="{x}" y1="26" x2="{x + w}" y2="26" class="rule"/>')

    # rows
    for r, (code, title, cells) in enumerate(ROWS):
        y = HEAD_H + 10 + r * (ROW_H + GAP)
        out.append(f'<text x="0" y="{y + 17}" class="code">{code}</text>')
        out.append(f'<text x="0" y="{y + 39}" class="rname">{esc(title)}</text>')
        out.append(f'<text x="0" y="{y + 54}" class="ridx">/{r + 1}</text>')

        for c, lines in enumerate(cells):
            x = lane_x[c]
            w = LANES[c][1]
            stop = c == len(LANES) - 1
            cls = "cell stop" if stop else "cell"
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{ROW_H}" rx="3" class="{cls}"/>')

            ty = y + 18
            for line in lines:
                if not line:
                    continue
                if line.startswith("×"):
                    kind = "x"
                    text = line[1:].strip()
                elif line.startswith("√"):
                    kind = "ok"
                    text = line[1:].strip()
                elif line.startswith("I "):
                    kind = "io"
                    text = line
                elif line.startswith("O "):
                    kind = "io"
                    text = line
                else:
                    kind = "n"
                    text = line
                out.append(
                    f'<text x="{x + 10}" y="{ty}" class="l {kind}">{esc(text)}</text>'
                )
                ty += LINE

            if c < len(LANES) - 1:
                ax = x + w + 1
                out.append(
                    f'<line x1="{ax}" y1="{y + ROW_H / 2}" x2="{lane_x[c + 1] - 4}" y2="{y + ROW_H / 2}" '
                    f'class="link" marker-end="url(#ar)"/>'
                )

    out.append(f'<text x="0" y="{total_h - 16}" class="foot">'
               f'I = 输入 · O = 输出 · × = 断在这里 · √ = 通过 · 终点列标红</text>')
    out.append("</svg>")

    html = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>七个场景的泳道图 · lifeOAC</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=Geist:wght@400;500&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --paper:#efeee6; --surface:#faf9f3; --ink:#191d19; --muted:#646a60;
    --rule:rgba(25,29,25,.13); --rule2:rgba(25,29,25,.3); --accent:#a9352b;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--paper); color:var(--ink); font-family:'Geist',system-ui,sans-serif; }}
  .wrap {{ padding:36px 40px 48px; }}
  h1 {{ font-family:'Bricolage Grotesque','Geist',sans-serif; font-weight:700; letter-spacing:-.03em;
        font-size:30px; margin:0 0 6px; }}
  .sub {{ color:var(--muted); font-size:13px; margin:0 0 26px; max-width:70ch; }}
  .frame {{ border:1px solid var(--rule); background:var(--surface); border-radius:4px; padding:18px 20px; overflow-x:auto; }}
  svg {{ display:block; min-width:1120px; }}
  .lane {{ font-family:'Geist Mono',monospace; font-size:10px; letter-spacing:.08em; fill:var(--muted); }}
  .lane.stop {{ fill:var(--accent); }}
  .rule {{ stroke:var(--rule2); stroke-width:1; }}
  .cell {{ fill:#fff; stroke:var(--rule); }}
  .cell.stop {{ fill:rgba(169,53,43,.045); stroke:rgba(169,53,43,.45); }}
  .l {{ font-family:'Geist',sans-serif; font-size:{FS}px; fill:var(--ink); }}
  .l.x {{ fill:var(--muted); }}
  .l.ok {{ fill:#2c6a4a; font-weight:500; }}
  .l.io {{ font-family:'Geist Mono',monospace; font-size:{FS - 0.5}px; }}
  .l.n {{ fill:var(--muted); }}
  .code {{ font-family:'Geist Mono',monospace; font-size:13px; fill:var(--accent); font-weight:500; }}
  .rname {{ font-size:11px; fill:var(--ink); }}
  .ridx {{ font-family:'Geist Mono',monospace; font-size:9px; fill:var(--muted); }}
  .link {{ stroke:#9a9f94; stroke-width:1; }}
  .foot {{ font-family:'Geist Mono',monospace; font-size:9px; fill:var(--muted); letter-spacing:.04em; }}
</style></head>
<body><div class="wrap">
  <h1>七个场景，六个节点</h1>
  <p class="sub">从一句话发出，到它死在哪一步。横向是节点，纵向是场景；每格写清输入与输出，最后一列是终点。</p>
  <div class="frame">{''.join(out)}</div>
</div></body></html>"""

    target = Path(__file__).parent / "swimlane.html"
    target.write_text(html)
    print("wrote", target, total_w, total_h)


if __name__ == "__main__":
    main()
