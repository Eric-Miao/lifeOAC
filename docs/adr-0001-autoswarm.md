# ADR-0001 · 把 AutoSwarm 当作执行通道，而不是重构基线

- 日期：2026-11-18
- 状态：已采纳
- 决策者：CEO；执行：本仓库

## 背景

需要一层"把一次委派变成真实 CLI 调用"的能力。候选是 HKUDS/AutoSwarm（MIT，2.6k star，2026-07 起，支持 12 家 agent CLI）。

## 决策

**intake，不作为 baseline。** 我们调它的 CLI，读它的调用记录，但不 import 它的状态模型。

## 理由

1. **它明确不做调度。** 架构文档原话：`There are no companies, task cards, global task queue or extra scheduling state machine`、`no resident scheduler`。我们需要的东西不在里面。
2. **它的 v1 就是一家公司，v2 删掉了。** 归档里有 `company_corporate_config.yaml`（`topology: Corporate Structure`、`final_decider_role_id`、员工 roster）、`company-staffing-agent-selection`（组织绑定、逐角色选人、checkpoint 路由）。v2 把整层删掉，退回"最小状态，只留事实"。
   → 公司层是复杂度真正爆掉的地方。我们保留它，但必须薄：组织从记录派生，不为组织单造状态机。
3. **它的强项正好是我们的弱项。** 12 家 CLI 的原生协议适配、session 续接、审批往返、每次调用一个原子目录。这些是脏活，写起来贵、维护更贵。
4. **绑死它当基线，会把我们刻意要造的五层架在一个删掉同样五层的运行时上**，还绑死它的记录格式与发版节奏（33 个 open issue，刚做过一次大重构）。

## 边界

| 能力 | 归属 |
|---|---|
| 执行通道、CLI 适配、session 句柄、原生审批往返 | AutoSwarm |
| 会话内容 | 各家 CLI 自己的存储 |
| 编排（任务包、fanout 计划、验收） | 我们的 CxO |
| 审批的最终门（预算双签、对外发布） | 我们的 policy |
| 记忆（部门资产、公司事实、做梦） | 我们 |
| inbox / 定时器 / outbox / 审计 | 我们 |

## 后果

- `backend/app/execution.py` 是唯一接触 AutoSwarm 的模块。换掉它不影响其他代码。
- `backend/app/runs.py` 存我们自己承认的那份账；AutoSwarm 的目录只当外部快照。
- **回写必须同步。** 它不复制原生 history，session 被清理后指针就悬空；所以任务结束当场写部门资产，不能事后补捞。
- **审计粒度是调用级**，不是逐 token 级。
- 它不保证跨产品 exactly-once；涉及花钱与对外的任务，幂等键由我们生成。

## 未验证

- 未逐行读它的源码，只读了架构文档、模块清单与 v1 归档配置。
- 审批中转（`approval_required` → 我们 → `decision.json`）尚未实测，当前只跑通了 run / inspect / resume。
- Codex 与 OpenCode 已实测（34s / 7.5s，resume 保持同一 native session）。DSH 仅探测到可执行，未跑。

## 落地

`backend/app/execution.py`（适配器）+ `backend/app/runs.py`（账）+ `/api/agents/{id}/runs`（入口）+ 抽屉里的「派活」页。
