"""一个真的 LLM 扮演"你"，把场景走完。

它有私人口径（预算、目标、家庭情况），没有数据库访问权；
过没过由代码判，不由它宣布。
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from llm_client import generate  # noqa: E402

BASE = "http://127.0.0.1:8001"


def call(method: str, path: str, body: dict | None = None, timeout: float = 180) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def say(agent: str, text: str) -> str:
    res = call("POST", f"/api/agents/{agent}/messages", {"body": text})
    msgs = (res or {}).get("messages") or []
    return msgs[-1]["body"] if msgs else f"<无回复 {res.get('error', '')}>"


def state() -> dict:
    return call("GET", "/api/state")


PERSONA = """你是这家公司唯一的真人，也就是 CEO。你在和自己的 CxO 谈事。
这不是演示，不要提测试、系统、模型、流程。

你的私人情况（只有你知道，被问到才说）：
{facts}

当前场景：{scene}

怎么说话：
- 像老板：短句，一次说一件事，30 字以内。
- 对方问你要信息，就从上面挑着给；给过的不重复。
- 对方要你拍板，就在授权内直接拍，别绕。
- 对方把事办完并给了结论，你就回两个字：结束。
- 不要替对方干活，不要自己写方案。

对话到目前为止：
{history}

你下一句："""


def converse(agent: str, scene: str, facts: str, opening: str, terminal, max_turns: int = 5) -> list[dict]:
    trace: list[dict] = []
    msg = opening
    for turn in range(1, max_turns + 1):
        reply = say(agent, msg)
        trace.append({"turn": turn, "from": "你", "text": msg})
        trace.append({"turn": turn, "from": agent, "text": reply})

        if terminal():
            trace.append({"turn": turn, "from": "assert", "text": "命中终止条件"})
            break

        hist = "\n".join(f"{t['from']}：{t['text']}" for t in trace[-8:])
        nxt = generate(PERSONA.format(facts=facts, scene=scene, history=hist)) or "结束"
        if nxt.strip().rstrip("。") == "结束":
            trace.append({"turn": turn, "from": "你", "text": "结束"})
            break
        msg = nxt.strip().splitlines()[0][:120]
        time.sleep(0.2)
    return trace


SCENES = {
    "a": {
        "agent": "sec",
        "scene": "开年度 ECE，把今年的总预算、营收目标、各项目额度定下来。",
        "facts": """- 2026 是自然年，现在 11 月，你说的是补 2026 的账，不是定 2027。
- 2026 目标营收 30 万（主业工资 24 万 + 副业 6 万）。
- 2026 总预算 12 万，上限就是 12 万，不能超。
- 分项：应用 4.2 万、文创 2.6 万、自媒体 0.9 万、家庭 1.5 万、系统 0.9 万。
- 你只关心结果，不想听流程。""",
        "opening": "我们开年度的 ECE。定今年的总预算、营收目标，以及每个项目的额度。",
        "terminal": lambda: bool([e for e in state().get("entries", []) if e["kind"] == "decision"]),
    },
    "b": {
        "agent": "cpto",
        "scene": "做一个记录每天喝水量的 web app，本周要能看到可验收的版本。",
        "facts": """- 只给你一周时间，别做登录、别做多端。
- 验收就三条：打开能用、加水即时更新、刷新不丢。
- 预算上限 2000 块，超了要跟我说。""",
        "opening": "我想做一个记录每天喝水量的 web app，本周给我一版能验收的。",
        "terminal": lambda: any("水" in (p.get("name") or "") for p in state().get("products", [])),
    },
}

if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else "a"
    spec = SCENES[key]
    trace = converse(spec["agent"], spec["scene"], spec["facts"], spec["opening"], spec["terminal"])
    out = Path(__file__).parent / f"trace-{key}.json"
    out.write_text(json.dumps(trace, ensure_ascii=False, indent=1))
    for t in trace:
        print(f"[{t['turn']}] {t['from']}: {t['text'][:150]}")
    print("→", out)
