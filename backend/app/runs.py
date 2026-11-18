"""真实执行的账：派发、刷新、取消。

AutoSwarm 的记录目录只当外部快照看。这里存的是我们自己承认的那一份：
谁派的、派给谁、状态、结果、花了多久。审计以这里为准。
"""

from __future__ import annotations

import sqlite3

from . import execution
from .db import now


def create(conn: sqlite3.Connection, agent_id: str, provider: str, prompt: str) -> dict:
    dispatched = execution.dispatch(agent_id, provider, prompt)
    if not dispatched.get("ok"):
        return dispatched

    cur = conn.execute(
        "INSERT INTO runs (agent_id, provider, call_id, workspace, prompt, status, started_at)"
        " VALUES (?,?,?,?,?,?,?)",
        (agent_id, provider, dispatched["call_id"], dispatched["workspace"], prompt, "running", now()),
    )
    conn.execute(
        "INSERT INTO audit (ts, actor, action, target, policy, decision, meta)"
        " VALUES (?,?,?,?,?,?,?)",
        (now(), "ceo", "run.dispatch", f"{agent_id} · {provider}", "exec", "allow", prompt[:60]),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM runs WHERE id = ?", (cur.lastrowid,)).fetchone()
    return {"ok": True, "run": dict(row)}


def refresh(conn: sqlite3.Connection, run_id: int | None = None) -> None:
    rows = (
        conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchall()
        if run_id
        else conn.execute("SELECT * FROM runs WHERE status = 'running'").fetchall()
    )
    for row in rows:
        if row["status"] != "running":
            continue
        got = execution.inspect(row["call_id"])
        if not got.get("ok"):
            conn.execute(
                "UPDATE runs SET checked_at = ?, error = ? WHERE id = ?",
                (now(), got.get("error"), row["id"]),
            )
            continue
        status = got.get("status")
        if status == "running":
            conn.execute("UPDATE runs SET checked_at = ? WHERE id = ?", (now(), row["id"]))
            continue
        conn.execute(
            "UPDATE runs SET status = ?, content = ?, error = ?, session_id = ?,"
            " finished_at = ?, checked_at = ? WHERE id = ?",
            (
                status,
                got.get("content"),
                got.get("error"),
                got.get("session_id"),
                now(),
                now(),
                row["id"],
            ),
        )
        conn.execute(
            "INSERT INTO audit (ts, actor, action, target, policy, decision, meta)"
            " VALUES (?,?,?,?,?,?,?)",
            (now(), row["agent_id"], "run.finish", row["call_id"], "exec", status, (got.get("content") or "")[:80]),
        )
        if status == "completed":
            conn.execute(
                "INSERT INTO messages (ts, thread, sender, body, kind) VALUES (?,?,?,?,?)",
                (now(), row["agent_id"], row["agent_id"], f"任务跑完了。\n\n{got.get('content') or ''}", "real"),
            )
        else:
            conn.execute(
                "INSERT INTO messages (ts, thread, sender, body, kind) VALUES (?,?,?,?,?)",
                (now(), row["agent_id"], row["agent_id"], f"任务失败：{got.get('error') or '未知原因'}", "real"),
            )
        conn.execute("UPDATE agents SET status = 'working' WHERE id = ?", (row["agent_id"],))
    conn.commit()


def cancel(conn: sqlite3.Connection, run_id: int) -> dict:
    row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    if row is None:
        return {"ok": False, "error": "没有这次运行"}
    if row["status"] != "running":
        return {"ok": False, "error": "已经结束了"}
    execution.cancel(row["call_id"])
    conn.execute(
        "UPDATE runs SET status = 'cancelled', finished_at = ?, checked_at = ? WHERE id = ?",
        (now(), now(), run_id),
    )
    conn.execute(
        "INSERT INTO audit (ts, actor, action, target, policy, decision, meta)"
        " VALUES (?,?,?,?,?,?,?)",
        (now(), "ceo", "run.cancel", row["call_id"], "exec", "cancelled", ""),
    )
    conn.commit()
    return {"ok": True}


def list_runs(conn: sqlite3.Connection, agent_id: str | None = None, limit: int = 30) -> list[dict]:
    if agent_id:
        rows = conn.execute(
            "SELECT * FROM runs WHERE agent_id = ? ORDER BY id DESC LIMIT ?", (agent_id, limit)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]
