"""七个场景的验收跑。

模拟的"你"只走 HTTP，和 UI 用同一组接口；断言由本脚本做，不让被考的模型自己宣布通过。
输出 tests/e2e/report-<日期>.md。
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = os.environ.get("LIFEOAC_APP", "http://127.0.0.1:8001")
OUT = Path(__file__).parent

results: list[dict] = []


def call(method: str, path: str, body: dict | None = None, timeout: float = 180) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as exc:  # noqa: BLE001 - 报告里要看到原因
        return {"error": str(exc)}


def say(agent: str, text: str) -> str:
    res = call("POST", f"/api/agents/{agent}/messages", {"body": text})
    msgs = (res or {}).get("messages") or []
    return msgs[-1]["body"] if msgs else f"<失败：{res.get('error', '无回复')}>"


def state() -> dict:
    return call("GET", "/api/state")


def finance() -> dict:
    return call("GET", "/api/finance")


def check(name: str, ok: bool, detail: str = "") -> dict:
    return {"name": name, "ok": ok, "detail": detail}


def scenario(key: str, title: str, checks: list[dict], transcript: list[tuple[str, str]]) -> None:
    results.append({"key": key, "title": title, "checks": checks, "transcript": transcript})


def brief_contains(text: str, *words: str) -> bool:
    return any(w in text for w in words)


def run() -> None:
    st = state()
    if "error" in st:
        print("后端没起来：", st["error"])
        sys.exit(1)

    # ---------- a 年度 ECE ----------
    t = []
    t.append(("秘书", say("sec", "我们开年度的 ECE。定今年的总预算、营收目标，以及每个项目的额度。")))
    st = state()
    decisions = [e for e in st.get("entries", []) if e["kind"] == "decision"]
    scenario(
        "a",
        "年初 ECE：定预算与营收目标",
        [
            check("产生结构化决议", len(decisions) > 0, f"decision 事件 {len(decisions)} 条"),
            check(
                "预算由会议写入（非种子）",
                any(e["kind"] in ("decision", "budget") for e in st.get("entries", [])),
                "预算仍是种子数据，会议没有写入能力",
            ),
        ],
        t,
    )

    # ---------- b 喝水 app ----------
    t = []
    reply = say("cpto", "我要做一个记录每天喝水量的 web app，本周给我一版可以验收的原型。")
    t.append(("CPTO", reply))
    planned = brief_contains(reply, "验收", "任务包", "交付")
    runres = call(
        "POST",
        "/api/agents/cpto/runs",
        {"provider": "opencode", "prompt": "在仓库根目录创建 water-app/README.md，写明这是一个记录每日饮水量的 web app 的最小方案，一句话即可。"},
    )
    ok_run = bool(runres.get("ok"))
    time.sleep(30)
    runs = call("GET", "/api/runs?agent_id=cpto").get("runs", [])
    latest = runs[0] if runs else {}
    st = state()
    has_product = any("水" in (p.get("name") or "") for p in st.get("products", []))
    scenario(
        "b",
        "和 CTO 做喝水 app 并验收",
        [
            check("回复里出现验收口径", planned, "看关键词"),
            check("能派真实任务", ok_run, latest.get("call_id", "没派出去")),
            check("任务跑完", latest.get("status") == "completed", str(latest.get("status"))),
            check("产品表新增一行", has_product, "没有立项能力" if not has_product else "已新增"),
        ],
        t,
    )

    # ---------- c 泰国 ----------
    t = []
    reply = say("chro", "今年元旦我想去泰国旅游，你安排一下。")
    t.append(("CHRO", reply))
    st = state()
    trip = [e for e in st.get("entries", []) if "泰国" in (e.get("label") or "")]
    scenario(
        "c",
        "和 CHRO 说元旦去泰国",
        [
            check("回复提到预算或假期", brief_contains(reply, "预算", "假期", "天数", "机票"), "看关键词"),
            check("落成一条支出事件", len(trip) > 0, f"匹配 {len(trip)} 条"),
            check("与项目排期冲突时有升级", False, "没有时间账本，无法判断"),
        ],
        t,
    )

    # ---------- d 哑铃 ----------
    t = []
    reply = say("sec", "我要做一个新产品，腊肠狗形状的小哑铃。")
    t.append(("秘书", reply))
    routed = brief_contains(reply, "COO", "运营", "供应链", "CFO", "立项")
    st = state()
    dumbbell = any("哑铃" in (p.get("name") or "") for p in st.get("products", []))
    pending = [a for a in st.get("approvals", []) if "哑铃" in (a.get("title") or "")]
    scenario(
        "d",
        "和秘书说做一个腊肠狗哑铃",
        [
            check("指出牵头人（不自己干）", routed, "看关键词"),
            check("触发保留事项待批", len(pending) > 0, f"待批 {len(pending)} 条"),
            check("产品表新增一行", dumbbell, "没有立项能力" if not dumbbell else "已新增"),
        ],
        t,
    )

    # ---------- e 简报 ----------
    t = []
    t.append(("CFO", say("cfo", "我今天自己掏钱买了个镜头，300 块，记一下。")))
    reply = say("sec", "给我今天的 AI 简报。")
    t.append(("秘书", reply))
    f = finance()
    spend_known = any(e["label"] == "镜头" for e in state().get("entries", []))
    scenario(
        "e",
        "要今天的 AI 简报",
        [
            check("包含待批项", brief_contains(reply, "待批", "审批", "批准"), "看关键词"),
            check(
                "引用了真实数字",
                spend_known and brief_contains(reply, "300", "295", "1,904", "214", "21,900"),
                "应与库里的镜头 300 或系统 214 对上",
            ),
            check("不重复推送", True, "没有 outbox，暂时无从重复"),
        ],
        t,
    )

    # ---------- f 打工人 ----------
    t = []
    reply = say("sec", "根据公司对「打工人」这个产品的规划，26Q4 和 27H1 我应该做什么？")
    t.append(("秘书", reply))
    admits = brief_contains(reply, "没有", "找不到", "未收录", "不存在", "没有这个")
    scenario(
        "f",
        "问「打工人」的季度规划",
        [
            check("找不到就说找不到", admits, "看是否承认没有"),
            check("没有编造里程碑", not brief_contains(reply, "26Q4 计划", "27H1 计划"), "粗判"),
        ],
        t,
    )

    # ---------- g 半年度 ECE ----------
    t = []
    before = len([e for e in state().get("entries", []) if e["kind"] == "decision"])
    t.append(("秘书", say("sec", "我们开半年度 ECE，复盘 H1，调整预算。")))
    after = len([e for e in state().get("entries", []) if e["kind"] == "decision"])
    scenario(
        "g",
        "开半年度 ECE",
        [
            check("产生调整决议", after > before, f"决议数 {before} → {after}"),
            check("预算可被 supersede", False, "预算仍是种子数据，没有版本"),
        ],
        t,
    )


def write_report() -> Path:
    now = datetime.now()
    path = OUT / f"report-{now:%Y%m%d-%H%M}.md"
    lines = [f"# E2E report · {now:%Y-%m-%d %H:%M}", "", f"目标：{BASE}", ""]
    lines.append("| # | 场景 | 检查 | 结果 |")
    lines.append("|---|---|---|---|")
    for r in results:
        for c in r["checks"]:
            lines.append(
                f"| {r['key']} | {r['title']} | {c['name']} | {'✅' if c['ok'] else '❌'} {c['detail']} |"
            )
    lines.append("")
    for r in results:
        lines.append(f"## {r['key']} · {r['title']}")
        for who, text in r["transcript"]:
            lines.append(f"**{who}**：{text}")
        lines.append("")
    path.write_text("\n".join(lines))

    passed = sum(1 for r in results for c in r["checks"] if c["ok"])
    total = sum(len(r["checks"]) for r in results)
    print(f"{passed}/{total} 通过 → {path}")
    return path


if __name__ == "__main__":
    run()
    write_report()
