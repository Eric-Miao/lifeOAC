"""CxO 说话：把 JD、上下文与记账协议拼成一次生成。

模型给的只是文字与提议；数字进账前必须过 contracts 的校验。
模型不可用时退回本地模拟器，界面会标「沙箱」。
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

规矩：
- 说人话，短。像高管，不像客服。不要堆敬语。
- 不知道就说不知道。所有数字只能来自下面给的上下文或用户这一轮说的话，禁止推算编造。
- 你只出判断、方案、预算申请、任务包；具体执行说"我派一个子任务"，不假装自己已经动手。

记账协议：
用户报告任何一笔收入或支出时，你必须额外输出一个事件块，放在回复最后单独一段，格式严格：
```event
{{"kind":"spend","amount_cents":30000,"label":"镜头","period":"{period}","section":"opex","product_id":null,"hours":0}}
```
kind 用 spend 或 income；section 取 revenue|cogs|opex；金额单位是分；不确定科目就用 opex，不确定产品就填 null。事件块不要出现在正文里。
"""


def _history(conn: sqlite3.Connection, agent_id: str, limit: int = 12) -> list[tuple[str, str]]:
    rows = conn.execute(
        "SELECT sender, body FROM messages WHERE thread = ? ORDER BY id DESC LIMIT ?",
        (agent_id, limit + 1),
    ).fetchall()
    out = []
    for r in reversed(rows[1:]):
        who = "用户" if r["sender"] == "user" else "你"
        out.append((who, r["body"]))
    return out


def _record(conn: sqlite3.Connection, agent_id: str, e: dict) -> bool:
    ok, why = contracts.validate_event(e)
    if not ok:
        conn.execute(
            "INSERT INTO audit (ts, actor, action, target, policy, decision, meta)"
            " VALUES (?,?,?,?,?,?,?)",
            (now(), agent_id, "event.reject", e.get("label", "?"), "ledger", "deny", why),
        )
        return False

    cur = conn.execute(
        "INSERT INTO events (ts, kind, period, actor, subject, label, amount_cents, hours, section, product_id, payload)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            now(),
            e["kind"],
            e["period"],
            agent_id,
            e.get("product_id"),
            e["label"],
            e.get("amount_cents") or 0,
            e.get("hours") or 0,
            e.get("section") or "",
            e.get("product_id"),
            json.dumps(e, ensure_ascii=False),
        ),
    )
    conn.execute(
        "INSERT INTO audit (ts, actor, action, target, policy, decision, meta)"
        " VALUES (?,?,?,?,?,?,?)",
        (now(), agent_id, "event.record", e["label"], "ledger", "allow", f"#{cur.lastrowid}"),
    )
    return True


def reply(conn: sqlite3.Connection, agent_id: str, body: str) -> None:
    agent = conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
    if agent is None:
        return

    reports = agent["reports_to"] or "董事会"
    prompt = PROTOCOL.format(
        code=agent["code"],
        name=agent["name"],
        title=agent["title"],
        reports=reports,
        scope=agent["scope"],
        kpi=agent["kpi"],
        today=date.today().isoformat(),
        period=contracts.period_of(),
    )

    hist = _history(conn, agent_id)
    if hist:
        prompt += "\n最近的对话：\n" + "\n".join(f"{w}：{t}" for w, t in hist) + "\n"

    prompt += f"\n用户：{body}\n你的回复："

    text = llm.generate(prompt)
    if text is None:
        sim.respond(conn, agent_id, body)
        return

    recorded = 0
    for raw in EVENT_BLOCK.findall(text):
        try:
            e = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(e, dict) and _record(conn, agent_id, e):
            recorded += 1

    clean = EVENT_BLOCK.sub("", text).strip()

    if recorded:
        clean += "\n\n（已记账，进本期流水。）"

    conn.execute(
        "INSERT INTO messages (ts, thread, sender, body, kind) VALUES (?,?,?,?,?)",
        (now(), agent_id, agent_id, clean, "real"),
    )
    conn.commit()
