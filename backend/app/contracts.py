"""六条契约，落在代码里。

契约只约束"形状"，不管"内容"：财报怎么排、产品叫什么，都不在这里。
"""

from __future__ import annotations

import re
from datetime import date

PERIOD_RE = re.compile(r"^\d{4}(-Q[1-4])?$")
KINDS = {"ledger", "spend", "income", "decision", "package", "run", "message", "meeting"}
SECTIONS = {"revenue", "cogs", "opex"}


def period_of(d: date | None = None) -> str:
    d = d or date.today()
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


def validate_event(e: dict) -> tuple[bool, str]:
    kind = e.get("kind")
    if kind not in KINDS:
        return False, f"kind 不认识：{kind}"

    period = e.get("period") or period_of()
    if not PERIOD_RE.match(str(period)):
        return False, "period 必须是 2026 或 2026-Q4"
    e["period"] = period

    label = (e.get("label") or "").strip()
    if not label:
        return False, "label 不能为空"
    e["label"] = label[:120]

    if kind in {"spend", "income", "ledger"}:
        try:
            amount = int(e.get("amount_cents") or 0)
        except (TypeError, ValueError):
            return False, "amount_cents 必须是整数（分）"
        if amount <= 0:
            return False, "金额必须大于零"
        e["amount_cents"] = amount
        section = e.get("section") or ("revenue" if kind == "income" else "opex")
        if section not in SECTIONS:
            return False, f"section 必须是 {SECTIONS}"
        e["section"] = section
        try:
            e["hours"] = max(0, int(e.get("hours") or 0))
        except (TypeError, ValueError):
            e["hours"] = 0

    return True, "ok"
