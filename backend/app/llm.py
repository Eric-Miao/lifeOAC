"""本地 OpenCode 服务的模型调用。

不直连供应商：复用 opencode 已经配好的 provider 与凭证。
服务不可达时返回 None，上层降级回模拟器。
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

CONFIG = Path(__file__).parent / "data" / "llm.json"
DEFAULT = {"providerID": "opencode-go", "id": "deepseek-v4.1-flash"}

_cache: dict = {"url": None, "pw": None, "at": 0.0, "models": None}


def _service() -> tuple[str, str] | None:
    if _cache["url"] and time.monotonic() - _cache["at"] < 30:
        return _cache["url"], _cache["pw"]

    url = None
    try:
        out = subprocess.run(["opencode", "service", "status"], capture_output=True, text=True, timeout=9)
        url = out.stdout.strip().splitlines()[0].strip() if out.stdout.strip() else None
    except (OSError, subprocess.SubprocessError):
        return None

    pw = ""
    p = Path(os.path.expanduser("~/.config/opencode/service.json"))
    if p.exists():
        try:
            pw = json.loads(p.read_text()).get("password", "")
        except json.JSONDecodeError:
            pw = ""

    if not url:
        return None
    _cache.update(url=url.rstrip("/"), pw=pw, at=time.monotonic())
    return _cache["url"], _cache["pw"]


def _request(path: str, payload: dict | None = None, timeout: float = 120) -> dict | None:
    svc = _service()
    if svc is None:
        return None
    url, pw = svc
    token = base64.b64encode(f"opencode:{pw}".encode()).decode()
    headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url + path, data=data, headers=headers, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None


_online = {"at": 0.0, "v": False}


def online() -> bool:
    now = time.monotonic()
    if now - _online["at"] < 15:
        return _online["v"]
    _online["v"] = _request("/api/info", timeout=4) is not None
    _online["at"] = now
    return _online["v"]


def models() -> list[dict]:
    if _cache["models"] and time.monotonic() - _cache["at"] < 120:
        return _cache["models"]
    res = _request("/api/model", timeout=12)
    items = (res or {}).get("data") or []
    out = [
        {
            "providerID": m.get("providerID"),
            "id": m.get("id"),
            "name": m.get("name"),
            "type": m.get("type"),
            "cost": m.get("cost"),
        }
        for m in items
        if m.get("type") == "chat"
    ]
    _cache["models"] = out
    return out


def config() -> dict:
    if CONFIG.exists():
        try:
            return json.loads(CONFIG.read_text())
        except json.JSONDecodeError:
            pass
    return {"default": DEFAULT, "agents": {}}


def save_config(cfg: dict) -> None:
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))


def model_for(agent_id: str) -> dict:
    cfg = config()
    return (cfg.get("agents") or {}).get(agent_id) or cfg.get("default") or DEFAULT


def generate(prompt: str, model: dict | None = None, timeout: float = 120) -> str | None:
    ref = model or config().get("default") or DEFAULT
    res = _request(
        "/api/experimental/generate/text",
        {"model": {"providerID": ref["providerID"], "id": ref["id"]}, "prompt": prompt},
        timeout=timeout,
    )
    if not res:
        return None
    return ((res.get("data") or {}).get("text") or "").strip() or None
