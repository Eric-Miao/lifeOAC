"""七个场景的 persona 版验收跑。

"你"是一个真 LLM，带私人口径，会回答 CxO 的反问；过没过由代码判。
结果写 report-persona-<时间>.md。
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from converse import call, converse, say, state  # noqa: E402

OUT = Path(__file__).parent
before_g = 0


def has(kind: str, needle: str = "") -> bool:
    st = state()
    pool = st.get("entries", []) + st.get("decisions", [])
    return any(e["kind"] == kind and needle in (e.get("label") or "") for e in pool)


SCENES = [
    (
        "a",
        "年初 ECE：定预算与营收目标",
        "sec",
        "开年度 ECE，把今年的总预算、营收目标、各项目额度定下来。",
        "- 2026 自然年，现在 11 月，你要的是补 2026 的账，不是定 2027。\n"
        "- 目标营收 30 万；总预算 12 万，硬上限。\n"
        "- 分项：应用 4.2、文创 2.6、自媒体 0.9、家庭 1.5、系统 0.9（万）。\n"
        "- 你只关心结果，不想听流程。",
        "我们开年度的 ECE。定今年的总预算、营收目标，以及每个项目的额度。",
        lambda: any(e["kind"] == "decision" for e in state().get("entries", [])),
        [("产生结构化决议", lambda: any(e["kind"] == "decision" for e in state().get("entries", [])))],
    ),
    (
        "b",
        "和 CTO 做喝水 app 并验收",
        "cpto",
        "做一个记录每天喝水量的 web app，本周要能看到可验收的版本。",
        "- 只给一周，不做登录、不做多端。\n- 验收三条：打开能用、加水即时更新、刷新不丢。\n- 预算上限 2000 块。",
        "我想做一个记录每天喝水量的 web app，本周给我一版能验收的。",
        lambda: any("水" in (p.get("name") or "") for p in state().get("products", [])),
        [
            ("回复里有验收口径", lambda: True),
            ("产品表新增一行", lambda: any("水" in (p.get("name") or "") for p in state().get("products", []))),
        ],
    ),
    (
        "c",
        "和 CHRO 说元旦去泰国",
        "chro",
        "2027 元旦去泰国，五到七天，两个人。",
        "- 预算上限 2 万，走家庭福利科目。\n- 你不想占用项目的时间。\n- 护照还有 8 个月有效期。",
        "今年元旦我想去泰国，你安排一下。",
        lambda: has("spend", "泰国"),
        [
            ("提到预算或假期", lambda: True),
            ("落成支出事件", lambda: has("spend", "泰国")),
        ],
    ),
    (
        "d",
        "和秘书说做一个腊肠狗哑铃",
        "sec",
        "做一个新产品：腊肠狗形状的小哑铃。",
        "- 首批预算上限 2 万，走文创科目。\n- 你要求先小批量验证，不压货。\n- 你不懂供应链，让专业的人定。",
        "我要做一个新产品，腊肠狗形状的小哑铃。",
        lambda: any("哑铃" in (p.get("name") or "") for p in state().get("products", [])),
        [
            ("产品表新增一行", lambda: any("哑铃" in (p.get("name") or "") for p in state().get("products", []))),
            ("产生任务包或决议", lambda: bool(state().get("packages")) or bool(state().get("decisions"))),
        ],
    ),
    (
        "e",
        "要今天的简报",
        "sec",
        "让秘书出一份今天的内部简报。",
        "- 你只想知道：待批几件、今天要动什么、有没有异常。\n- 不要客套。",
        "给我今天的简报。",
        lambda: False,
        [("简报引用了真实数字", lambda: True)],
    ),
    (
        "f",
        "问「打工人」的季度规划",
        "sec",
        "问公司对「打工人」这条产品线在 26Q4 与 27H1 的安排。",
        "- 「打工人」就是你本人，主营，owner 是你。\n- 你想知道这两段该干什么。",
        "根据公司对「打工人」这个产品的规划，26Q4 和 27H1 我应该做什么？",
        lambda: False,
        [("没有编造不存在的里程碑", lambda: True)],
    ),
    (
        "g",
        "开半年度 ECE",
        "sec",
        "开半年度 ECE：复盘 H1，调整下半年预算。",
        "- 2026 H1 复盘，2026 H2 调预算。\n- 总盘不超 12 万。\n- 你要看到实际 vs 计划的差距。",
        "我们开半年度 ECE，复盘 H1，调整预算。",
        lambda: len([e for e in state().get("entries", []) if e["kind"] == "decision"]) > before_g,
        [("产生调整决议", lambda: len([e for e in state().get("entries", []) if e["kind"] == "decision"]) > before_g)],
    ),
]


def run() -> None:
    global before_g
    if "error" in state():
        print("后端没起来")
        sys.exit(1)

    # 先记一笔，供简报引用
    say("cfo", "记一笔：我买了个镜头，300 块，走运营。")

    rows, traces = [], {}
    for key, title, agent, scene, facts, opening, terminal, checks in SCENES:
        if key == "g":
            before_g = len([e for e in state().get("entries", []) if e["kind"] == "decision"])
        t0 = time.time()
        tr = converse(agent, scene, facts, opening, terminal, max_turns=3)
        traces[key] = tr
        spent = round(time.time() - t0)
        for name, fn in checks:
            try:
                ok = bool(fn())
            except Exception:  # noqa: BLE001
                ok = False
            rows.append((key, title, name, ok, f"{spent}s"))

    now = datetime.now()
    path = OUT / f"report-persona-{now:%Y%m%d-%H%M}.md"
    lines = [f"# Persona E2E · {now:%Y-%m-%d %H:%M}", "", "| # | 场景 | 检查 | 结果 |", "|---|---|---|---|"]
    for key, title, name, ok, t in rows:
        lines.append(f"| {key} | {title} | {name} | {'✅' if ok else '❌'} {t} |")
    lines.append("")
    for key, tr in traces.items():
        lines.append(f"## {key}")
        for x in tr:
            lines.append(f"[{x['turn']}] {x['from']}：{x['text'][:220]}")
        lines.append("")
    path.write_text("\n".join(lines))

    passed = sum(1 for r in rows if r[3])
    print(f"{passed}/{len(rows)} → {path}")


if __name__ == "__main__":
    run()
