"""秘书的定时器。

没有明确任务时，它只做三件事：扫一遍、决定要不要叫醒谁、出不出简报。
默认沉默——没事就不该有输出。
"""

from __future__ import annotations

import json

import sqlite3
from datetime import datetime, timedelta

from . import contracts, llm
from .db import now

QUIET_HOURS = 6
PROMPT = """你是公司的秘书（Chief of Staff）。现在是你自己的一次定时巡检。
职责：分诊、节流、路由。你不做决策，也不替 CxO 干活。

{facts}

写一份给 CEO 的简报，只有值得他知道的才写：
1. 待批：几件、分别是什么、涉及多少钱
2. 今天要动的事：到期的任务包、跑完的执行
3. 异常：超支、卡住、对不上的数
4. 建议他此刻唯一要做的一个动作

规则：
- 没有内容就回四个字：无需打扰。
- 不超过 120 字，不要客套，不要复述规则。
- 数字只能来自上面。
"""


def _facts(conn: sqlite3.Connection) -> str:
    period = contracts.period_of()
    pend = conn.execute(
        "SELECT title, amount_cents FROM approvals WHERE status='pending' ORDER BY id"
    ).fetchall()
    entries = conn.execute(
        "SELECT label, amount_cents, kind FROM events WHERE kind IN ('spend','income') ORDER BY id DESC LIMIT 5"
    ).fetchall()
    pkgs = conn.execute(
        "SELECT label, payload FROM events WHERE kind='package' ORDER BY id DESC LIMIT 5"
    ).fetchall()
    runs = conn.execute(
        "SELECT agent_id, status FROM runs ORDER BY id DESC LIMIT 5"
    ).fetchall()
    decs = conn.execute(
        "SELECT label, amount_cents FROM events WHERE kind='decision' ORDER BY id DESC LIMIT 3"
    ).fetchall()

    lines = [f"期间 {period}，现在 {datetime.now():%H:%M}"]
    lines.append(
        "待批：" + ("；".join(f"{p['title']} ¥{p['amount_cents'] / 100:,.0f}" for p in pend) or "无")
    )
    if decs:
        lines.append("最近决议：" + "；".join(f"{d['label']} ¥{d['amount_cents'] / 100:,.0f}" for d in decs))
    if entries:
        lines.append("最近记账：" + "；".join(f"{e['label']} ¥{e['amount_cents'] / 100:,.0f}" for e in entries))
    if pkgs:
        def _pkg(r):
            try:
                d = json.loads(r["payload"] or "{}")
            except json.JSONDecodeError:
                d = {}
            return f"{r['label']}({d.get('owner', '?')}, 截止 {d.get('deadline', '?')})"

        lines.append("任务包：" + "；".join(_pkg(p) for p in pkgs))
    if runs:
        lines.append("执行：" + "；".join(f"{r['agent_id']} {r['status']}" for r in runs))
    return "\n".join(lines)


def last_brief(conn: sqlite3.Connection) -> str | None:
    row = conn.execute(
        "SELECT ts FROM messages WHERE thread='sec' AND kind='brief' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return row["ts"] if row else None


def tick(conn: sqlite3.Connection, force: bool = False) -> dict:
    """一次巡检。返回是否说话，以及说了什么。"""
    recent = last_brief(conn)
    if recent and not force:
        try:
            if datetime.fromisoformat(recent) > datetime.now().astimezone() - timedelta(hours=QUIET_HOURS):
                return {"spoke": False, "reason": "quiet hours"}
        except ValueError:
            pass

    text = llm.generate(PROMPT.format(facts=_facts(conn)))
    if text is None:
        return {"spoke": False, "reason": "模型不可用"}

    if text.strip().startswith("无需打扰"):
        conn.execute(
            "INSERT INTO audit (ts, actor, action, target, policy, decision, meta) VALUES (?,?,?,?,?,?,?)",
            (now(), "sec", "outbox.skip", "brief", "notify", "allow", "无需打扰"),
        )
        conn.commit()
        return {"spoke": False, "reason": "无需打扰"}

    conn.execute(
        "INSERT INTO messages (ts, thread, sender, body, kind) VALUES (?,?,?,?,?)",
        (now(), "sec", "sec", text, "brief"),
    )
    conn.execute(
        "INSERT INTO audit (ts, actor, action, target, policy, decision, meta) VALUES (?,?,?,?,?,?,?)",
        (now(), "sec", "outbox.emit", "brief", "notify", "allow", text[:60]),
    )
    conn.commit()
    return {"spoke": True, "text": text}
