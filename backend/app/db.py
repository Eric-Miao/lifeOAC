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
    seat        INTEGER NOT NULL DEFAULT 0,
    subagents   INTEGER NOT NULL DEFAULT 0
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

CREATE TABLE IF NOT EXISTS products (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    kind            TEXT NOT NULL,
    owner           TEXT NOT NULL,
    stage           TEXT NOT NULL,
    progress        INTEGER NOT NULL DEFAULT 0,
    milestone       TEXT,
    milestone_due   TEXT,
    price_cents     INTEGER NOT NULL DEFAULT 0,
    unit_cost_cents INTEGER NOT NULL DEFAULT 0,
    inventory       INTEGER NOT NULL DEFAULT 0,
    note            TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT NOT NULL,
    kind         TEXT NOT NULL,
    period       TEXT,
    actor        TEXT NOT NULL,
    subject      TEXT,
    label        TEXT,
    amount_cents INTEGER NOT NULL DEFAULT 0,
    hours        INTEGER NOT NULL DEFAULT 0,
    section      TEXT,
    product_id   TEXT,
    payload      TEXT
);

CREATE TABLE IF NOT EXISTS ledger (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    period       TEXT NOT NULL,
    product_id   TEXT,
    section      TEXT NOT NULL,
    label        TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    note         TEXT
);

CREATE TABLE IF NOT EXISTS balance (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    period       TEXT NOT NULL,
    side         TEXT NOT NULL,
    label        TEXT NOT NULL,
    amount_cents INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS policy (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id    TEXT NOT NULL,
    provider    TEXT NOT NULL,
    call_id     TEXT NOT NULL UNIQUE,
    workspace   TEXT,
    prompt      TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'running',
    content     TEXT,
    error       TEXT,
    session_id  TEXT,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    checked_at  TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

PERIOD = "2026-Q4"


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


AGENTS = [
    # id, code, name, title, reports_to, tier, scope, kpi, palette, desk_x, desk_y, seat
    ("ceo", "CEO", "你", "CEO · 董事", None, 0,
     "最终仲裁；保留事项由董事会决定；对外代表", "公司整体运行状态",
     '{"hair":"#2B2B33","skin":"#E7C39B","shirt":"#243B4A","pants":"#1B2A33","trim":"#C9D6D2"}', 34, 40, 1),
    ("cpto", "CPTO", "技术", "产品 · 技术 · 数据", "ceo", 1,
     "应用矩阵、平台工程、数据与 AI、设计系统", "交付节奏与复用率",
     '{"hair":"#1F2A2E","skin":"#D9AE86","shirt":"#2F5D62","pants":"#22393D","trim":"#A9C7C4"}', 98, 40, 2),
    ("cfo", "CFO", "财务", "财务 · 家庭账本 · 双币预算", "ceo", 1,
     "现金、预算、家庭固定成本、三张报表", "现金安全月数与预算执行率",
     '{"hair":"#3A2B20","skin":"#E0B98F","shirt":"#6B4A2F","pants":"#3A2A1D","trim":"#D6C0A5"}', 162, 40, 3),
    ("cmo", "CMO", "市场", "品牌 · 增长 · 渠道", "ceo", 1,
     "品牌、投放、内容营销、渠道", "获客成本与自然流量占比",
     '{"hair":"#2A2233","skin":"#E9C3A0","shirt":"#7A3B52","pants":"#41263A","trim":"#D9B7C6"}', 226, 40, 4),
    ("coo", "COO", "运营", "运营 · 供应链 · 履约", "ceo", 1,
     "供应链与制造、客服售后、PMO", "交付准时率与退货率",
     '{"hair":"#20303C","skin":"#D8A87E","shirt":"#3B4A2F","pants":"#26301F","trim":"#BFCBA8"}', 34, 84, 5),
    ("chro", "CHRO", "人事", "组织 · 人才 · 福利", "ceo", 1,
     "Family Ops、招聘职级、福利与假期", "家庭时间兑现率与人员健康",
     '{"hair":"#33241E","skin":"#EFCBA8","shirt":"#4B3A6B","pants":"#2E2340","trim":"#C9BBE0"}', 98, 84, 6),
    ("audit", "AUD", "审计", "独立审计 · 向董事会汇报", None, 1,
     "季度、半年、年度审计；红队；可手动触发", "发现问题的数量与整改率",
     '{"hair":"#1A1A1A","skin":"#D3B08A","shirt":"#2A2A2A","pants":"#161616","trim":"#B9B9B9"}', 162, 84, 7),
    ("sec", "SEC", "秘书", "Chief of Staff · inbox/outbox", "ceo", 1,
     "分诊、节流、路由、会议材料包", "打扰次数与信息完整度",
     '{"hair":"#2C2420","skin":"#E4BE96","shirt":"#8A6A3F","pants":"#4A3823","trim":"#DDCBA9"}', 226, 84, 8),
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
    ("apps", "应用矩阵", "cpto", PERIOD, 4200000, 1904000, 180, 74),
    ("toys", "文创产品", "coo", PERIOD, 2600000, 984000, 120, 41),
    ("media", "自媒体", "cmo", PERIOD, 900000, 318000, 90, 52),
    ("household", "家庭固定成本", "cfo", PERIOD, 1500000, 712000, 0, 0),
    ("system", "系统运营", "cfo", PERIOD, 90000, 21400, 0, 0),
]

# id, name, kind, owner, stage, progress, milestone, due, price, unit_cost, inventory, note
PRODUCTS = [
    ("ledger", "记账 · 极简账本", "app", "cpto", "在售", 72,
     "v2.4 订阅页改版", "2026-12-05", 1800, 0, 0, "订阅 ¥18/月"),
    ("focus", "专注 · 番茄钟", "app", "cpto", "开发", 40,
     "内测放量到 200 人", "2026-12-20", 1200, 0, 0, "内购解锁"),
    ("pixel", "像素打工仔 · 桌面摆件", "toy", "coo", "在售", 65,
     "第二批补货 500 件", "2026-11-30", 8900, 3200, 180, "PU 树脂，三色"),
    ("xhs", "小红书 · 纯内容", "media", "cmo", "在售", 80,
     "12 月选题排期", "2026-11-28", 0, 0, 0, "约 6.8 万粉"),
    ("douyin", "抖音 · 纯内容", "media", "cmo", "在售", 55,
     "周更稳定到 8 条", "2026-12-15", 0, 0, 0, "约 1.2 万粉"),
]

# period, product_id, section, label, amount, note
LEDGER = [
    (PERIOD, None, "revenue", "工资（主营业务）", 18000000, "每月 ¥60,000"),
    (PERIOD, "ledger", "revenue", "订阅收入", 1240000, "约 690 个订阅"),
    (PERIOD, "focus", "revenue", "内购", 380000, "内测期"),
    (PERIOD, "pixel", "revenue", "零售", 2680000, "约 300 件"),
    (PERIOD, "xhs", "revenue", "商单", 460000, "3 单"),
    (PERIOD, "douyin", "revenue", "商单", 160000, "1 单"),

    (PERIOD, "pixel", "cogs", "BOM 与生产", 980000, "单件 ¥32"),
    (PERIOD, "pixel", "cogs", "模具摊销", 320000, "分 4 个季度"),
    (PERIOD, "pixel", "cogs", "物流与仓储", 240000, ""),
    (PERIOD, "pixel", "cogs", "退货与损耗", 110000, "退货率 4.1%"),
    (PERIOD, "ledger", "cogs", "App 服务器", 60000, ""),
    (PERIOD, "focus", "cogs", "App 服务器", 30000, ""),
    (PERIOD, "ledger", "cogs", "平台分成", 360000, "30%"),
    (PERIOD, "xhs", "cogs", "内容拍摄", 120000, ""),
    (PERIOD, "douyin", "cogs", "内容拍摄", 60000, ""),

    (PERIOD, None, "opex", "市场投放", 480000, "ASA + 小红书"),
    (PERIOD, None, "opex", "工具与系统", 90000, "模型与 API"),
    (PERIOD, None, "opex", "家庭固定成本", 1500000, ""),
    (PERIOD, None, "opex", "差旅", 120000, ""),
]

BALANCE = [
    ("inventory", "asset", "存货（成品 + 在制）", 1760000),
    ("receivable", "asset", "应收账款", 620000),
    ("payable", "liability", "应付账款", 890000),
    ("card", "liability", "信用卡待还", 240000),
]

SETTINGS = {
    "billing": {
        "provider": "Anthropic",
        "model": "claude-opus-5.5",
        "cap_cents": 90000,
        "spent_cents": 21400,
        "keys": [
            {"name": "ANTHROPIC_API_KEY", "masked": "sk-ant-••••4f2a", "status": "ok"},
            {"name": "OPENAI_API_KEY", "masked": "未配置", "status": "missing"},
        ],
        "by_agent": [
            {"agent": "CPTO", "calls": 412, "cents": 9800},
            {"agent": "CMO", "calls": 96, "cents": 4200},
            {"agent": "CFO", "calls": 61, "cents": 3100},
            {"agent": "SEC", "calls": 1284, "cents": 4300},
        ],
    },
    "memory": {
        "namespaces": [
            {"name": "ceo", "docs": 12, "tokens": 8400, "updated": "2026-11-17 09:12"},
            {"name": "cfo", "docs": 31, "tokens": 21400, "updated": "2026-11-17 08:40"},
            {"name": "cpto", "docs": 64, "tokens": 48200, "updated": "2026-11-16 22:10"},
            {"name": "shared", "docs": 18, "tokens": 12600, "updated": "2026-11-16 19:02"},
        ],
        "dreaming": {"last": "2026-11-17 03:00", "next": "2026-11-18 03:00", "kept": 147, "dropped": 26},
        "pending": 6,
    },
    "plugins": [
        {"id": "github", "name": "GitHub", "version": "0.4.1", "scopes": ["repo:read", "issue:write"], "status": "on", "owner": "CPTO"},
        {"id": "figma", "name": "Figma", "version": "0.2.0", "scopes": ["file:read"], "status": "on", "owner": "CPTO"},
        {"id": "shopify", "name": "Shopify", "version": "0.1.3", "scopes": ["order:read", "inventory:write"], "status": "off", "owner": "COO"},
        {"id": "ffmpeg", "name": "FFmpeg", "version": "7.1", "scopes": ["fs:read", "fs:write"], "status": "on", "owner": "CMO"},
        {"id": "imagegen", "name": "Image Gen", "version": "1.0.0", "scopes": ["net:out"], "status": "off", "owner": "CMO"},
    ],
    "connectors": [
        {"id": "fs", "name": "本地文件系统", "kind": "data", "status": "connected", "last": "实时", "detail": "~/Documents/projectM"},
        {"id": "notion", "name": "Notion", "kind": "data", "status": "disconnected", "last": "—", "detail": "未授权"},
        {"id": "obsidian", "name": "Obsidian", "kind": "data", "status": "connected", "last": "12 分钟前", "detail": "~/life/vault"},
        {"id": "feishu", "name": "飞书", "kind": "chat", "status": "connected", "last": "刚刚", "detail": "bot: lifeoac"},
        {"id": "telegram", "name": "Telegram", "kind": "chat", "status": "connected", "last": "3 分钟前", "detail": "@lifeoac_bot"},
        {"id": "github", "name": "GitHub", "kind": "work", "status": "connected", "last": "1 小时前", "detail": "Eric-Miao"},
        {"id": "bank", "name": "银行流水", "kind": "money", "status": "manual", "last": "11-15", "detail": "人工回填"},
    ],
    "notifications": {
        "brief_at": "08:30",
        "channels": [
            {"name": "飞书", "level": "简报"},
            {"name": "Telegram", "level": "实时"},
            {"name": "邮件", "level": "关闭"},
        ],
        "sources": [
            {"name": "审批与预算", "level": "实时"},
            {"name": "审计异常", "level": "实时"},
            {"name": "项目里程碑", "level": "简报"},
            {"name": "平台评论与私信", "level": "简报"},
            {"name": "GitHub 动态", "level": "关闭"},
        ],
    },
}

SEED_THREADS = {
    "sec": [
        ("user", "今天先看这三件事：应用矩阵的排期、文创的库存、周末的安排。"),
        ("sec", "收到。应用矩阵我合到 CPTO 的周报里，库存找 COO，周末安排走 CHRO 的福利科目。三件都压到明早的简报里，不单独打扰。"),
    ],
    "cfo": [
        ("cfo", "本季度系统运营成本已归集 ¥214，占 IT 科目 24%。要不要设上限？"),
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

    conn.executemany(
        "INSERT INTO products (id, name, kind, owner, stage, progress, milestone, milestone_due,"
        " price_cents, unit_cost_cents, inventory, note) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        PRODUCTS,
    )

    conn.executemany(
        "INSERT INTO events (ts, kind, period, actor, subject, label, amount_cents, hours, section, product_id, payload)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                now(),
                "ledger",
                period,
                "system",
                product_id,
                label,
                amount,
                0,
                section,
                product_id,
                json.dumps({"note": note}, ensure_ascii=False),
            )
            for period, product_id, section, label, amount, note in LEDGER
        ],
    )

    conn.executemany(
        "INSERT INTO balance (period, side, label, amount_cents) VALUES (?,?,?,?)",
        [("2026-Q4", side, label, amount) for _, side, label, amount in BALANCE],
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
        ("cash_opening", "12400000"),
    ):
        conn.execute("INSERT INTO policy (key, value) VALUES (?,?)", (key, str(value)))

    for key, value in SETTINGS.items():
        conn.execute("INSERT INTO settings (key, value) VALUES (?,?)", (key, json.dumps(value, ensure_ascii=False)))

    conn.execute(
        "INSERT INTO audit (ts, actor, action, target, policy, decision, meta)"
        " VALUES (?,?,?,?,?,?,?)",
        (now(), "system", "bootstrap", "lifeOAC", "—", "allow", "组织图与空账本就位；无任务"),
    )
    conn.commit()
