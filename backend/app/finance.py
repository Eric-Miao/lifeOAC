"""三张表与项目损益，全部从 ledger / balance 现算。

沙箱数据，但算法是真的：改一行 ledger，报表跟着变。
"""

from __future__ import annotations

import sqlite3

PERIOD = "2026-Q4"


def _sum(rows: list[sqlite3.Row]) -> int:
    return sum(r["amount_cents"] for r in rows)


def build(conn: sqlite3.Connection) -> dict:
    ledger = conn.execute("SELECT * FROM ledger WHERE period = ? ORDER BY id", (PERIOD,)).fetchall()
    names = {r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM products")}
    ledger = [
        dict(r, label=f"{names[r['product_id']]} · {r['label']}" if r["product_id"] in names else r["label"])
        for r in ledger
    ]
    revenue = [r for r in ledger if r["section"] == "revenue"]
    cogs = [r for r in ledger if r["section"] == "cogs"]
    opex = [r for r in ledger if r["section"] == "opex"]

    rev, cost, opex_total = _sum(revenue), _sum(cogs), _sum(opex)
    gross, net = rev - cost, rev - cost - opex_total

    row = conn.execute("SELECT value FROM policy WHERE key='cash_opening'").fetchone()
    opening = int(row["value"]) if row else 0
    closing = opening + net
    burn = round((cost + opex_total) / 3)
    runway = round(closing / burn, 1) if burn else 0

    balance_rows = conn.execute("SELECT * FROM balance WHERE period = ?", (PERIOD,)).fetchall()
    inventory = next((r["amount_cents"] for r in balance_rows if r["side"] == "asset" and "存货" in r["label"]), 0)
    receivable = next((r["amount_cents"] for r in balance_rows if r["side"] == "asset" and "应收" in r["label"]), 0)
    liabilities = [r for r in balance_rows if r["side"] == "liability"]
    liab_total = _sum(liabilities)

    assets = closing + inventory + receivable
    equity = assets - liab_total

    # 项目损益
    products = conn.execute("SELECT * FROM products ORDER BY kind, id").fetchall()
    portfolio = []
    for p in products:
        p_rev = sum(r["amount_cents"] for r in revenue if r["product_id"] == p["id"])
        p_cost = sum(r["amount_cents"] for r in cogs if r["product_id"] == p["id"])
        portfolio.append(
            {
                "id": p["id"],
                "name": p["name"],
                "kind": p["kind"],
                "owner": p["owner"],
                "revenue": p_rev,
                "cost": p_cost,
                "margin": p_rev - p_cost,
                "margin_pct": round((p_rev - p_cost) / p_rev * 100) if p_rev else 0,
                "inventory": p["inventory"],
                "unit_cost": p["unit_cost_cents"],
                "price": p["price_cents"],
                "stock_value": p["inventory"] * p["unit_cost_cents"],
            }
        )

    salary = next((r["amount_cents"] for r in revenue if r["product_id"] is None), 0)

    return {
        "period": PERIOD,
        "currency": "CNY",
        "pl": {
            "revenue": [dict(r) for r in revenue],
            "cogs": [dict(r) for r in cogs],
            "opex": [dict(r) for r in opex],
            "total_revenue": rev,
            "total_cogs": cost,
            "gross": gross,
            "gross_pct": round(gross / rev * 100) if rev else 0,
            "total_opex": opex_total,
            "net": net,
            "net_pct": round(net / rev * 100) if rev else 0,
            "salary_share": round(salary / rev * 100) if rev else 0,
            "side_revenue": rev - salary,
        },
        "cash": {
            "opening": opening,
            "inflow": rev,
            "outflow": cost + opex_total,
            "closing": closing,
            "monthly_burn": burn,
            "runway_months": runway,
        },
        "balance": {
            "assets": [
                {"label": "现金", "amount": closing},
                {"label": "存货", "amount": inventory},
                {"label": "应收", "amount": receivable},
            ],
            "liabilities": [dict(r) for r in liabilities],
            "assets_total": assets,
            "liabilities_total": liab_total,
            "equity": equity,
        },
        "portfolio": portfolio,
    }
