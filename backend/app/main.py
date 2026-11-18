"""FastAPI surface for the lifeOAC skeleton.

Deliberately small: one state endpoint the UI polls, plus the writes a person
actually performs — talk to an agent, resolve an approval, read the books.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import chat, execution, finance, llm, runs, sim
from .db import connect, now, seed


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class RunIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    provider: str = Field(min_length=1, max_length=40)


class ResolveIn(BaseModel):
    decision: str = Field(pattern="^(approve|reject)$")
    note: str = ""


conn: sqlite3.Connection = connect()


@asynccontextmanager
async def lifespan(_: FastAPI):
    seed(conn)

    async def loop() -> None:
        while True:
            await asyncio.sleep(6)
            sim.tick(conn)
            await asyncio.to_thread(runs.refresh, conn)

    task = asyncio.create_task(loop())
    yield
    task.cancel()


app = FastAPI(title="lifeOAC", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/state")
def get_state() -> dict:
    return sim.state(conn)


@app.get("/api/agents/{agent_id}/messages")
def get_messages(agent_id: str) -> dict:
    rows = conn.execute("SELECT * FROM messages WHERE thread = ? ORDER BY id", (agent_id,)).fetchall()
    return {"messages": [dict(r) for r in rows]}


@app.post("/api/agents/{agent_id}/messages")
def post_message(agent_id: str, body: MessageIn) -> dict:
    agent = conn.execute("SELECT id FROM agents WHERE id = ?", (agent_id,)).fetchone()
    if agent is None:
        raise HTTPException(404, "unknown agent")

    conn.execute(
        "INSERT INTO messages (ts, thread, sender, body, kind) VALUES (?,?,?,?,?)",
        (now(), agent_id, "user", body.body, "chat"),
    )
    conn.execute("UPDATE agents SET status='working' WHERE id = ?", (agent_id,))
    conn.execute(
        "INSERT INTO audit (ts, actor, action, target, policy, decision, meta) VALUES (?,?,?,?,?,?,?)",
        (now(), "ceo", "message.send", agent_id, "—", "allow", body.body[:60]),
    )
    conn.commit()
    chat.reply(conn, agent_id, body.body)
    conn.commit()

    rows = conn.execute("SELECT * FROM messages WHERE thread = ? ORDER BY id", (agent_id,)).fetchall()
    return {"messages": [dict(r) for r in rows]}


@app.post("/api/approvals/{approval_id}")
def resolve_approval(approval_id: int, body: ResolveIn) -> dict:
    sim.resolve(conn, approval_id, body.decision, body.note)
    return {"ok": True}


@app.get("/api/execution")
def get_execution() -> dict:
    return {
        "available": execution.available(),
        "home": str(execution.HOME),
        "providers": execution.providers(),
    }


@app.get("/api/runs")
def get_runs(agent_id: str | None = None) -> dict:
    runs.refresh(conn)
    return {"runs": runs.list_runs(conn, agent_id)}


@app.post("/api/agents/{agent_id}/runs")
def post_run(agent_id: str, body: RunIn) -> dict:
    agent = conn.execute("SELECT id FROM agents WHERE id = ?", (agent_id,)).fetchone()
    if agent is None:
        raise HTTPException(404, "unknown agent")
    if body.provider not in execution.usable():
        raise HTTPException(400, f"{body.provider} 不可用")

    made = runs.create(conn, agent_id, body.provider, body.prompt)
    if not made.get("ok"):
        raise HTTPException(502, made.get("error") or "派发失败")
    conn.execute("UPDATE agents SET status='working' WHERE id = ?", (agent_id,))
    conn.commit()
    return made


@app.post("/api/runs/{run_id}/cancel")
def cancel_run(run_id: int) -> dict:
    result = runs.cancel(conn, run_id)
    if not result.get("ok"):
        raise HTTPException(400, result.get("error") or "取消失败")
    return result


@app.get("/api/llm")
def get_llm() -> dict:
    return {
        "online": llm.online(),
        "models": llm.models(),
        "config": llm.config(),
    }


@app.put("/api/llm")
def put_llm(body: dict) -> dict:
    cfg = llm.config()
    if "default" in body and isinstance(body["default"], dict):
        cfg["default"] = body["default"]
    if "agents" in body and isinstance(body["agents"], dict):
        cfg.setdefault("agents", {}).update(body["agents"])
    llm.save_config(cfg)
    conn.execute(
        "INSERT INTO audit (ts, actor, action, target, policy, decision, meta) VALUES (?,?,?,?,?,?,?)",
        (now(), "ceo", "llm.config", "models", "—", "allow", json.dumps(cfg, ensure_ascii=False)[:120]),
    )
    conn.commit()
    return {"ok": True, "config": cfg}


@app.get("/api/finance")
def get_finance() -> dict:
    return finance.build(conn)


@app.get("/api/policy")
def get_policy() -> dict:
    spec = conn.execute("SELECT value FROM policy WHERE key='spec'").fetchone()
    return json.loads(spec["value"]) if spec else {}


@app.get("/api/settings")
def get_settings() -> dict:
    out: dict = {}
    for row in conn.execute("SELECT key, value FROM settings"):
        out[row["key"]] = json.loads(row["value"])
    policy = conn.execute("SELECT value FROM policy WHERE key='spec'").fetchone()
    out["policy"] = json.loads(policy["value"]) if policy else {}
    return out


@app.post("/api/memory/dream")
def run_dreaming() -> dict:
    """后台整理现在是占位：只写审计，不动真实记忆。"""
    conn.execute(
        "INSERT INTO audit (ts, actor, action, target, policy, decision, meta) VALUES (?,?,?,?,?,?,?)",
        (now(), "system", "memory.dream", "all namespaces", "—", "allow", "手动触发，沙箱"),
    )
    conn.commit()
    return {"ok": True}


@app.get("/api/org")
def get_org() -> dict:
    rows = [dict(r) for r in conn.execute("SELECT * FROM agents ORDER BY tier, seat")]
    nodes = [
        {
            "id": r["id"],
            "code": r["code"],
            "name": r["name"],
            "title": r["title"],
            "reports_to": r["reports_to"],
            "scope": r["scope"],
            "status": r["status"],
            "subagents": r["subagents"],
        }
        for r in rows
    ]
    return {"nodes": nodes, "derived_from": "agents table + audit log"}
