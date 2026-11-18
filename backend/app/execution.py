"""AutoSwarm adapter — the execution channel under a CxO.

We do not import AutoSwarm's state model. We call its CLI, keep the call id as a
pointer, and mirror only what the audit needs. If it is uninstalled or breaks,
`available()` goes false and the UI falls back to the sandbox simulator.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

HOME = Path(os.environ.get("AUTOSWARM_HOME", Path(__file__).parent / "data" / "autoswarm"))
WORKSPACES = Path(__file__).parent / "data" / "workspaces"

_cache: dict = {"at": 0.0, "providers": []}
_TTL = 60.0


def binary() -> str | None:
    return shutil.which("autoswarm")


def available() -> bool:
    return binary() is not None


def _call(args: list[str], timeout: float = 120) -> dict:
    bin_ = binary()
    if bin_ is None:
        return {"ok": False, "error": "autoswarm 未安装"}
    try:
        proc = subprocess.run(
            [bin_, "--home", str(HOME), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "autoswarm 调用超时"}
    except OSError as exc:
        return {"ok": False, "error": str(exc)}

    raw = proc.stdout.strip()
    if not raw:
        return {"ok": False, "error": proc.stderr.strip()[:400] or "没有输出"}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"ok": False, "error": raw[:400]}


def providers(refresh: bool = False) -> list[dict]:
    import time

    now = time.monotonic()
    if not refresh and now - _cache["at"] < _TTL:
        return _cache["providers"]

    res = _call(["agents"], timeout=30)
    items = (res.get("data") or {}).get("agents") or []
    _cache["providers"] = [
        {
            "provider": a.get("provider"),
            "available": bool(a.get("available")),
            "version": a.get("version"),
            "verified": bool(a.get("invocation_verified")),
        }
        for a in items
    ]
    _cache["at"] = now
    return _cache["providers"]


def usable() -> list[str]:
    return [p["provider"] for p in providers() if p["available"]]


def workspace(agent_id: str) -> Path:
    path = WORKSPACES / agent_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def dispatch(agent_id: str, provider: str, prompt: str) -> dict:
    ws = workspace(agent_id)
    res = _call(
        ["run", "--background", "--agent", provider, "--cwd", str(ws), prompt],
        timeout=90,
    )
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error") or "派发失败"}
    data = res.get("data") or {}
    if not data.get("call_id"):
        return {"ok": False, "error": "没有拿到 call_id"}
    return {
        "ok": True,
        "call_id": data["call_id"],
        "agent_id": agent_id,
        "provider": provider,
        "workspace": str(ws),
        "state": data.get("state", "running"),
    }


def inspect(call_id: str) -> dict:
    res = _call(["inspect", call_id], timeout=30)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error") or "查询失败"}
    data = res.get("data") or {}
    result = data.get("result") or {}
    state = data.get("state")
    if state == "returned" and result:
        outcome = result.get("outcome")
        status = "completed" if outcome == "completed" else "failed"
        return {
            "ok": True,
            "status": status,
            "content": result.get("content"),
            "error": result.get("error"),
            "session_id": result.get("native_session_id"),
        }
    if state == "running":
        return {"ok": True, "status": "running"}
    return {"ok": True, "status": state or "unknown"}


def cancel(call_id: str) -> dict:
    return _call(["cancel", call_id], timeout=30)
