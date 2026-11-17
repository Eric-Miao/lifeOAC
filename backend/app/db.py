"""SQLite schema, connection and seed data.

Two rules from AGENTS.md shape this file:
  * the system log is append-only (messages, audit, approvals);
  * the org chart is derived from records, never hand-edited.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.environ.get("LIFEOAC_DB", Path(__file__).parent / "data" / "lifeoac.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
    id          TEXT PRIMARY KEY,
    code        TEXT NOT NULL,
    name        TEXT NOT NULL,
    title       TEXT NOT NULL,
    reports_to  TEXT,
    tier        INTEGER NOT NULL DEFAULT 1,
    status      TEXT NOT NULL DEFAULT 'idle',
    task        TEXT,
    scope       TEXT,
    kpi         TEXT,
    palette     TEXT NOT NULL,
    desk_x      INTEGER NOT NULL,
    desk_y      INTEGER NOT NULL,
    seat        INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      TEXT NOT NULL,
    thread  TEXT NOT NULL,
    sender  TEXT NOT NULL,
    body    TEXT NOT NULL,
    kind    TEXT NOT NULL DEFAULT 'chat'
);

CREATE TABLE IF NOT EXISTS approvals (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT NOT NULL,
    agent_id     TEXT NOT NULL,
    title        TEXT NOT NULL,
    detail       TEXT,
    amount_cents INTEGER NOT NULL DEFAULT 0,
    status       TEXT NOT NULL DEFAULT 'pending',
    resolved_ts  TEXT,
    resolution   TEXT
);

CREATE TABLE IF NOT EXISTS audit (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    ts       TEXT NOT NULL,
    actor    TEXT NOT NULL,
    action   TEXT NOT NULL,
    target   TEXT,
    policy   TEXT,
    decision TEXT,
    meta     TEXT
);

CREATE TABLE IF NOT EXISTS budgets (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    owner        TEXT NOT NULL,
    period       TEXT NOT NULL,
    money_cents  INTEGER NOT NULL,
    money_spent  INTEGER NOT NULL,
    hours        INTEGER NOT NULL,
    hours_spent  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS policy (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def row_to_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in row.keys()}


AGENTS = [
    # id, code, name, title, reports_to, tier, scope, kpi, palette, desk_x, desk_y, seat
    ("ceo-a", "CEO", "你", "联席 CEO · 董事", None, 0,
     "最终仲裁；保留事项一致同意；对外代表", "公司整体运行状态",
     '{"hair":"#2B2B33","skin":"#E7C39B","shirt":"#243B4A","pants":"#1B2A33","trim":"#C9D6D2"}', 34, 40, 1),
    ("ceo-b", "CEO", "伴侣", "联席 CEO · 董事", None, 0,
     "最终仲裁；保留事项一致同意；对外代表", "公司整体运行状态",
     '{"hair":"#4A2E22","skin":"#EBC9A6","shirt":"#5A2E3B","pants":"#2E1B24","trim":"#E3C6CE"}', 98, 40, 2),
    ("cpto", "CPTO", "技术", "产品 · 技术 · 数据", "ceo-a", 1,
     "应用矩阵、平台工程、数据与 AI、设计系统", "交付节奏与复用率",
     '{"hair":"#1F2A2E","skin":"#D9AE86","shirt":"#2F5D62","pants":"#22393D","trim":"#A9C7C4"}', 162, 40, 3),
    ("cfo", "CFO", "财务", "财务 · 家庭账本 · 双币预算", "ceo-a", 1,
     "现金、预算、家庭固定成本、billing", "现金安全月数与预算执行率",
     '{"hair":"#3A2B20","skin":"#E0B98F","shirt":"#6B4A2F","pants":"#3A2A1D","trim":"#D6C0A5"}', 226, 40, 4),
    ("cmo", "CMO", "市场", "品牌 · 增长 · 渠道", "ceo-b", 1,
     "品牌、投放、内容营销、渠道", "获客成本与自然流量占比",
     '{"hair":"#2A2233","skin":"#E9C3A0","shirt":"#7A3B52","pants":"#41263A","trim":"#D9B7C6"}', 34, 84, 5),
    ("coo", "COO", "运营", "运营 · 供应链 · 履约", "ceo-b", 1,
     "供应链与制造、客服售后、PMO", "交付准时率与退货率",
     '{"hair":"#20303C","skin":"#D8A87E","shirt":"#3B4A2F","pants":"#26301F","trim":"#BFCBA8"}', 98, 84, 6),
    ("chro", "CHRO", "人事", "组织 · 人才 · 福利", "ceo-a", 1,
     "Family Ops、招聘职级、福利与假期", "家庭时间兑现率与人员健康",
     '{"hair":"#33241E","skin":"#EFCBA8","shirt":"#4B3A6B","pants":"#2E2340","trim":"#C9BBE0"}', 162, 84, 7),
    ("audit", "AUD", "审计", "独立审计 · 向董事会汇报", None, 1,
     "季度、半年、年度审计；红队；可手动触发", "发现问题的数量与整改率",
     '{"hair":"#1A1A1A","skin":"#D3B08A","shirt":"#2A2A2A","pants":"#161616","trim":"#B9B9B9"}', 226, 84, 8),
    ("sec", "SEC", "秘书", "Chief of Staff · inbox/outbox", "ceo-a", 1,
     "分诊、节流、路由、会议材料包", "打扰次数与信息完整度",
     '{"hair":"#2C2420","skin":"#E4BE96","shirt":"#8A6A3F","pants":"#4A3823","trim":"#DDCBA9"}', 44, 150, 9),
]

POLICY = {
    "version": 7,
    "effective": "2026-11-17T00:00:00+08:00",
    "folder_roots": ["~/Documents/projectM", "~/life"],
    "rules": [
        {"id": "fs.read", "action": "read 登记目录", "gate": "auto", "approver": None},
        {"id": "fs.write", "action": "write 登记目录", "gate": "notify", "approver": None},
        {"id": "exec", "action": "execute 沙箱内", "gate": "notify", "approver": None},
        {"id": "plugin.install", "action": "安装 plugin", "gate": "approve", "approver": "CEO"},
        {"id": "spend.small", "action": "spend 低于阈值（¥200）", "gate": "approve", "approver": "CEO"},
        {"id": "spend.large", "action": "spend 高于阈值", "gate": "dual", "approver": "CFO + CEO"},
        {"id": "external", "action": "publish / 私信 / 下单", "gate": "approve", "approver": "CEO"},
        {"id": "delete", "action": "delete", "gate": "deny", "approver": "CEO"},
    ],
}

BUDGETS = [
    ("apps", "应用矩阵", "cpto", "2026-Q4", 4200000, 1904000, 180, 74),
    ("toys", "文创产品", "coo", "2026-Q4", 2600000, 984000, 120, 41),
    ("media", "自媒体", "cmo", "2026-Q4", 900000, 318000, 90, 52),
    ("household", "家庭固定成本", "cfo", "2026-Q4", 1500000, 712000, 0, 0),
    ("system", "系统运营（IT）", "cfo", "2026-Q4", 90000, 21400, 0, 0),
]

SEED_THREADS = {
    "sec": [
        ("user", "今天先看这三件事：应用矩阵的排期、文创的库存、周末的安排。"),
        ("sec", "收到。应用矩阵我合到 CPTO 的周报里，库存找 COO，周末安排走 CHRO 的福利科目。三件都压到明早的简报里，不单独打扰。"),
    ],
    "cfo": [
        ("cfo", "本季度系统运营成本已归集 ¥2,140，占 IT 科目 24%。要不要设上限？"),
    ],
}


def seed(conn: sqlite3.Connection) -> None:
    cur = conn.execute("SELECT COUNT(*) AS n FROM agents")
    if cur.fetchone()["n"]:
        return

    conn.executemany(
        "INSERT INTO agents (id, code, name, title, reports_to, tier, scope, kpi, palette, desk_x, desk_y, seat)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        AGENTS,
    )

    for agent_id, notes in SEED_THREADS.items():
        for sender, body in notes:
            conn.execute(
                "INSERT INTO messages (ts, thread, sender, body, kind) VALUES (?,?,?,?,?)",
                (now(), agent_id, sender, body, "seed"),
            )

    conn.executemany(
        "INSERT INTO budgets (id, name, owner, period, money_cents, money_spent, hours, hours_spent)"
        " VALUES (?,?,?,?,?,?,?,?)",
        BUDGETS,
    )

    conn.execute(
        "INSERT INTO approvals (ts, agent_id, title, detail, amount_cents, status)"
        " VALUES (?,?,?,?,?,?)",
        (now(), "cfo", "系统运营预算上限", "billing 页上线前，先定本季度 token 与 API 上限。", 90000, "pending"),
    )
    conn.execute("UPDATE agents SET status='waiting' WHERE id='cfo'")

    for key, value in (
        ("version", POLICY["version"]),
        ("effective", POLICY["effective"]),
        ("spec", json.dumps(POLICY, ensure_ascii=False)),
    ):
        conn.execute("INSERT INTO policy (key, value) VALUES (?,?)", (key, str(value)))

    conn.execute(
        "INSERT INTO audit (ts, actor, action, target, policy, decision, meta)"
        " VALUES (?,?,?,?,?,?,?)",
        (now(), "system", "bootstrap", "lifeOAC", "—", "allow", "组织图与空账本就位；无任务"),
    )
    conn.commit()
