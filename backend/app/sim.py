"""Local sandbox simulation.

No model provider is wired yet, so the CxO replies here are rule-based. Every
message it writes is tagged kind='sandbox' and the UI labels it. Nothing in this
file may pretend to be real inference.
"""

from __future__ import annotations

import json
import random
import sqlite3
from datetime import datetime

from . import execution
from .db import now

WORK_STATES = ("working", "working", "working", "idle", "idle")


def _agent(conn: sqlite3.Connection, agent_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()


def _say(conn: sqlite3.Connection, thread: str, sender: str, body: str, kind: str = "sandbox") -> None:
    conn.execute(
        "INSERT INTO messages (ts, thread, sender, body, kind) VALUES (?,?,?,?,?)",
        (now(), thread, sender, body, kind),
    )


def _audit(conn, actor, action, target, policy, decision, meta=""):
    conn.execute(
        "INSERT INTO audit (ts, actor, action, target, policy, decision, meta) VALUES (?,?,?,?,?,?,?)",
        (now(), actor, action, target, policy, decision, meta),
    )


def _approval(conn, agent_id: str, title: str, detail: str, amount_cents: int = 0) -> None:
    conn.execute(
        "INSERT INTO approvals (ts, agent_id, title, detail, amount_cents, status) VALUES (?,?,?,?,?,?)",
        (now(), agent_id, title, detail, amount_cents, "pending"),
    )
    conn.execute("UPDATE agents SET status = 'waiting' WHERE id = ?", (agent_id,))


KEYWORDS = (
    ("预算", "spend"),
    ("钱", "spend"),
    ("花", "spend"),
    ("买", "spend"),
    ("发布", "external"),
    ("发帖", "external"),
    ("对外", "external"),
    ("审计", "audit"),
    ("检查", "audit"),
)


def respond(conn: sqlite3.Connection, agent_id: str, text: str) -> None:
    """Write a sandbox reply, and open an approval when the ask needs one."""
    agent = _agent(conn, agent_id)
    if agent is None:
        return

    kind = "chat"
    for word, tag in KEYWORDS:
        if word in text:
            kind = tag
            break

    scope = agent["scope"].split("、")[0]

    if kind == "spend":
        amount = 48000
        _approval(
            conn,
            agent_id,
            f"{scope} · 一笔支出",
            "来自对话的即时申请。金额按上次同类项估的，等你批。",
            amount,
        )
        _say(
            conn,
            agent_id,
            agent_id,
            f"这笔钱走「{scope}」科目，我按 ¥480 起的申请。预算还有余量，"
            "你批了我再往下推；不批就压回队列，不动。",
        )
        _audit(conn, agent_id, "spend.request", "budget", "spend.small", "pending", "¥480")
        return

    if kind == "external":
        _approval(
            conn,
            agent_id,
            "对外发布 · 一条内容",
            "草稿已就位，等你放行。发布后删除成本高，撤回窗口约 2 分钟。",
            0,
        )
        _say(
            conn,
            agent_id,
            agent_id,
            "草稿我压在本地，没发。对外动作按 policy external 走：你点头才出街。"
            "要不要我先给你看一版文案？",
        )
        _audit(conn, agent_id, "external.publish", "draft", "external", "pending", "未发出")
        return

    if kind == "audit":
        _say(
            conn,
            agent_id,
            agent_id,
            "收到。这一条进审计清单，我按证据链走，不走你的记忆。"
            "本轮只做只读检查，不改任何文件。",
            kind="chat",
        )
        return

    _say(
        conn,
        agent_id,
        agent_id,
        f"记下了。这条进「{scope}」的任务包，缺的是预算和截止日。"
        "你先给我一个时间盒，我把它编译成可执行的那一版。",
    )


def tick(conn: sqlite3.Connection) -> None:
    """Advance agent states. Cheap, deterministic enough, and honest about it."""
    agents = conn.execute("SELECT * FROM agents").fetchall()
    if not agents:
        return

    agent = random.choice(agents)
    if agent["status"] == "waiting":
        return

    status = random.choice(WORK_STATES)
    task = {
        "working": f"{agent['scope'].split('、')[0]} · 推进中",
        "idle": None,
        "waiting": "等一个决定",
    }[status]
    subs = random.choice([0, 0, 1, 2, 3]) if status == "working" else 0
    conn.execute(
        "UPDATE agents SET status = ?, task = ?, subagents = ? WHERE id = ?",
        (status, task, subs, agent["id"]),
    )

    pending = conn.execute("SELECT COUNT(*) AS n FROM approvals WHERE status='pending'").fetchone()["n"]
    if pending < 3 and random.random() < 0.025:
        _approval(
            conn,
            agent["id"],
            f"{agent['scope'].split('、')[0]} · 例行申请",
            "沙箱模拟出的例行审批。",
            random.choice([0, 12000, 38000, 96000]),
        )
    conn.commit()


def resolve(conn: sqlite3.Connection, approval_id: int, decision: str, note: str) -> None:
    row = conn.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
    if row is None or row["status"] != "pending":
        return
    conn.execute(
        "UPDATE approvals SET status = ?, resolved_ts = ?, resolution = ? WHERE id = ?",
        ("approved" if decision == "approve" else "rejected", now(), note, approval_id),
    )
    conn.execute("UPDATE agents SET status = 'working' WHERE id = ?", (row["agent_id"],))
    _audit(
        conn,
        "ceo-a",
        "approval.resolve",
        f"approval#{approval_id}",
        "spend.small" if row["amount_cents"] else "external",
        decision,
        f"¥{row['amount_cents'] / 100:.0f}",
    )
    _say(
        conn,
        row["agent_id"],
        row["agent_id"],
        "批了，我往下推。" if decision == "approve" else "驳回收到，压回队列，本轮不动。",
        kind="chat",
    )
    conn.commit()


def state(conn: sqlite3.Connection) -> dict:
    agents = [dict(r) for r in conn.execute("SELECT * FROM agents ORDER BY tier, seat")]
    for a in agents:
        a["palette"] = json.loads(a["palette"])

    approvals = [dict(r) for r in conn.execute("SELECT * FROM approvals WHERE status='pending' ORDER BY id")]
    threads = [dict(r) for r in conn.execute(
        "SELECT thread, MAX(id) AS last_id, COUNT(*) AS n FROM messages GROUP BY thread"
    )]
    last = {
        r["thread"]: dict(r)
        for r in conn.execute(
            "SELECT m.* FROM messages m JOIN (SELECT thread, MAX(id) AS mid FROM messages GROUP BY thread) t"
            " ON m.id = t.mid"
        )
    }
    budgets = [dict(r) for r in conn.execute("SELECT * FROM budgets ORDER BY rowid")]
    products = [dict(r) for r in conn.execute("SELECT * FROM products ORDER BY kind, id")]
    audit = [dict(r) for r in conn.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 60")]

    runs = [dict(r) for r in conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 20")]

    return {
        "mode": "sandbox",
        "execution": {
            "available": execution.available(),
            "providers": execution.providers(),
        },
        "runs": runs,
        "server_time": datetime.now().isoformat(timespec="seconds"),
        "agents": agents,
        "approvals": approvals,
        "threads": [{"thread": t["thread"], "count": t["n"], "last": last.get(t["thread"])} for t in threads],
        "budgets": budgets,
        "products": products,
        "audit": audit,
    }
