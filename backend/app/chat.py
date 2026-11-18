"""CxO 说话：JD + 公司现状 + 记账协议，拼成一次生成。

模型只产出文字与提议；三类写入（决议 / 任务包 / 立项）与账目都必须过
contracts 的校验才落库。模型不可用时退回本地模拟器。
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import date

from . import contracts, llm, sim
from .db import now

EVENT_BLOCK = re.compile(r"```event\s*(\{.*?\})\s*```", re.S)

PROTOCOL = """你是「生活有限公司」的 {code}，名字叫{name}，岗位是「{title}」。
汇报对象：{reports}
职责范围：{scope}
对什么负责：{kpi}

今天是 {today}。财年是自然年，当前是 {period}。

{facts}

规矩：
- 说人话，短。像高管，不像客服。不要堆敬语。
- 不知道就说不知道。数字只能来自上面「公司现状」或用户这一轮说的话，禁止推算编造。
- 你只出判断、方案、预算申请、任务包；具体执行说"我派一个子任务"。

写入协议：只在这四种情况下，额外输出一个 event 块（放在回复最后，单独一段，不在正文里出现）：
1. 用户报告一笔收入或支出 → kind=spend 或 income
2. 用户拍板一个额度、预算、取舍 → kind=decision
3. 你要派人干活 → kind=package
4. 用户要立一个新产品/新业务线 → kind=product

格式严格：
```event
{{"kind":"spend","amount_cents":30000,"label":"镜头","section":"opex","period":"{period}"}}
{{"kind":"decision","amount_cents":1200000,"hours":0,"label":"2026 总预算 12 万","approved_by":"CEO","period":"{period}"}}
{{"kind":"package","label":"2026 账目拉齐","owner":"cfo","deadline":"2026-11-19","acceptance":"分项目分科目的实际与承诺","go_nogo":"缺数不发","hours":6}}
{{"kind":"product","name":"打工人","line":"personal","owner":"ceo","label":"打工人","milestone":"Q4 完成年度述职"}}
```
金额单位是分；section 取 revenue|cogs|opex；line 取 app|toy|media|personal。
一个块只放一个事件。没有要写的就不写。
"""


def _money(cents: int) -> str:
    return f"¥{cents / 100:,.0f}"


def _facts(conn: sqlite3.Connection) -> str:
    period = contracts.period_of()
    prods = conn.execute("SELECT name, stage, owner FROM products ORDER BY kind, id").fetchall()
    pend = conn.execute("SELECT title, amount_cents FROM approvals WHERE status='pending'").fetchall()
    entries = conn.execute(
        "SELECT kind, label, amount_cents FROM events WHERE kind IN ('spend','income') ORDER BY id DESC LIMIT 5"
    ).fetchall()
    decs = conn.execute(
        "SELECT label, amount_cents FROM events WHERE kind='decision' ORDER BY id DESC LIMIT 5"
    ).fetchall()
    pkgs = conn.execute(
        "SELECT label, payload FROM events WHERE kind='package' ORDER BY id DESC LIMIT 5"
    ).fetchall()
    rev, opex = conn.execute(
        "SELECT"
        " COALESCE(SUM(CASE WHEN section='revenue' THEN amount_cents END),0),"
        " COALESCE(SUM(CASE WHEN section IN ('cogs','opex') THEN amount_cents END),0)"
        " FROM events WHERE period = ? AND kind IN ('ledger','spend','income')",
        (period,),
    ).fetchone()

    lines = [f"公司现状（只读，引用数字只能来自这里）：", f"期间 {period}"]
    lines.append("产品：" + ("、".join(f"{p['name']}({p['stage']})" for p in prods) or "还没有"))
    lines.append(f"本期收入 {_money(rev)} · 支出 {_money(opex)}")
    if entries:
        lines.append("最近记的账：" + "；".join(f"{e['label']} {_money(e['amount_cents'])}" for e in entries))
    if decs:
        lines.append("最近决议：" + "；".join(f"{d['label']} {_money(d['amount_cents'])}" for d in decs))
    if pkgs:
        def _pkg(r):
            try:
                d = json.loads(r["payload"] or "{}")
            except json.JSONDecodeError:
                d = {}
            return f"{r['label']}({d.get('owner', '?')}, {d.get('deadline', '?')})"

        lines.append("已派任务包：" + "；".join(_pkg(p) for p in pkgs))
    if pend:
        lines.append(
            "待你批：" + "；".join(f"{p['title']} {_money(p['amount_cents'])}" for p in pend)
        )
    return "\n".join(lines)


def _history(conn: sqlite3.Connection, agent_id: str, limit: int = 12) -> list[tuple[str, str]]:
    rows = conn.execute(
        "SELECT sender, body FROM messages WHERE thread = ? ORDER BY id DESC LIMIT ?",
        (agent_id, limit + 1),
    ).fetchall()
    out = []
    for r in reversed(rows[1:]):
        out.append(("用户" if r["sender"] == "user" else "你", r["body"]))
    return out


def _apply(conn: sqlite3.Connection, e: dict) -> None:
    """写入事件之后，把有副作用的类型落到表上。"""
    if e["kind"] == "product":
        pid = e["name"].strip()
        exists = conn.execute("SELECT id FROM products WHERE id = ?", (pid,)).fetchone()
        if exists:
            conn.execute(
                "UPDATE products SET owner = ?, milestone = ? WHERE id = ?",
                (e["owner"], e.get("milestone"), pid),
            )
        else:
            conn.execute(
                "INSERT INTO products (id, name, kind, owner, stage, progress, milestone, milestone_due,"
                " price_cents, unit_cost_cents, inventory, note)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    pid,
                    pid,
                    e["line"],
                    e["owner"],
                    "立项",
                    0,
                    e.get("milestone"),
                    e.get("deadline"),
                    0,
                    0,
                    0,
                    "由对话立项",
                ),
            )


def _record(conn: sqlite3.Connection, agent_id: str, e: dict) -> tuple[bool, str]:
    ok, why = contracts.validate_event(e)
    if not ok:
        conn.execute(
            "INSERT INTO audit (ts, actor, action, target, policy, decision, meta)"
            " VALUES (?,?,?,?,?,?,?)",
            (now(), agent_id, "event.reject", str(e.get("label") or e.get("name") or "?")[:40], "write", "deny", why),
        )
        return False, why

    cur = conn.execute(
        "INSERT INTO events (ts, kind, period, actor, subject, label, amount_cents, hours, section, product_id, payload)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            now(),
            e["kind"],
            e.get("period") or contracts.period_of(),
            agent_id,
            e.get("product_id") or e.get("owner"),
            e.get("label") or e.get("name"),
            e.get("amount_cents") or 0,
            e.get("hours") or 0,
            e.get("section") or "",
            e.get("product_id"),
            json.dumps(e, ensure_ascii=False),
        ),
    )
    _apply(conn, e)
    conn.execute(
        "INSERT INTO audit (ts, actor, action, target, policy, decision, meta)"
        " VALUES (?,?,?,?,?,?,?)",
        (now(), agent_id, f"{e['kind']}.write", str(e.get("label") or e.get("name"))[:40], "write", "allow", f"#{cur.lastrowid}"),
    )
    return True, ""


def reply(conn: sqlite3.Connection, agent_id: str, body: str) -> None:
    agent = conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
    if agent is None:
        return

    prompt = PROTOCOL.format(
        code=agent["code"],
        name=agent["name"],
        title=agent["title"],
        reports=agent["reports_to"] or "董事会",
        scope=agent["scope"],
        kpi=agent["kpi"],
        today=date.today().isoformat(),
        period=contracts.period_of(),
        facts=_facts(conn),
    )

    hist = _history(conn, agent_id)
    if hist:
        prompt += "\n最近的对话：\n" + "\n".join(f"{w}：{t}" for w, t in hist) + "\n"

    prompt += f"\n用户：{body}\n你的回复："

    text = llm.generate(prompt)
    if text is None:
        sim.respond(conn, agent_id, body)
        return

    written = []
    for raw in EVENT_BLOCK.findall(text):
        try:
            e = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(e, dict) and _record(conn, agent_id, e)[0]:
            written.append(e["kind"])

    clean = EVENT_BLOCK.sub("", text).strip()
    if written:
        label = {"decision": "决议", "package": "任务包", "product": "立项", "spend": "支出", "income": "收入"}
        clean += "\n\n（已写入：" + "、".join(label.get(k, k) for k in written) + "）"

    conn.execute(
        "INSERT INTO messages (ts, thread, sender, body, kind) VALUES (?,?,?,?,?)",
        (now(), agent_id, agent_id, clean, "real"),
    )
    conn.commit()
