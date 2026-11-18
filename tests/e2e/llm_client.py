"""测试侧直接调本地 opencode 生成，不经我们的后端。"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

MODEL = {"providerID": "opencode-go", "id": "deepseek-v4.1-flash"}


def _service() -> tuple[str, str] | None:
    try:
        out = subprocess.run(["opencode", "service", "status"], capture_output=True, text=True, timeout=9)
        url = out.stdout.strip().splitlines()[0].strip() if out.stdout.strip() else None
    except (OSError, subprocess.SubprocessError):
        return None
    if not url:
        return None
    pw = ""
    p = Path(os.path.expanduser("~/.config/opencode/service.json"))
    if p.exists():
        try:
            pw = json.loads(p.read_text()).get("password", "")
        except json.JSONDecodeError:
            pw = ""
    return url.rstrip("/"), pw


def generate(prompt: str, timeout: float = 60) -> str | None:
    svc = _service()
    if svc is None:
        return None
    url, pw = svc
    token = base64.b64encode(f"opencode:{pw}".encode()).decode()
    body = json.dumps({"model": MODEL, "prompt": prompt}).encode()
    req = urllib.request.Request(
        url + "/api/experimental/generate/text",
        data=body,
        headers={"Authorization": f"Basic {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return ((json.loads(r.read().decode()).get("data") or {}).get("text") or "").strip() or None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None
