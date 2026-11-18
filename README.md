# lifeOAC

用一家公司的治理方式，管理一个人的全部生活。**这个仓库是它的系统骨架。**

先读 [`AGENTS.md`](AGENTS.md)（项目宪法与 11 条决议），再看 [`PRODUCT.md`](PRODUCT.md) 与 [`DESIGN.md`](DESIGN.md)。

## 跑起来

两个进程：后端 8000，前端 5173。

```bash
# 终端 1
cd backend
uv sync
uv run uvicorn app.main:app --port 8000

# 终端 2
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173 。数据库在 `backend/app/data/lifeoac.db`，删掉它就会重新播种。

## 现在有什么

| 一级页面 | 做什么 |
|---|---|
| 办公室 | 像素办公室，8 个角色。点一个人 → 抽屉里对话 / 看岗位 / 批预算 |
| 组织图 | 从 agents 表派生；subagent 只以 ×N 记在所属 CxO 角上 |
| 产品 | 产品组合：阶段、进度、下一里程碑、单位经济、本季损益 |
| 财务 | 三张表（损益 / 现金流 / 资产）、项目成本与毛利、待批 |
| 对话 | 与每位 CxO 的直线线程 |
| 审计 | append-only 的操作记录，可按判定筛选 |
| 设置 | 权限、Billing、Memory、Plugins、Connectors、通知 |

**Billing 是本系统调用模型的账单**，属于设置；**财务是公司的账**，属于一级页面。两者不混。

## 对话（本地模型）

设置 → LLM 里选 provider 与模型，每个席位可单独指定。默认走本机 opencode 服务的 `/api/experimental/generate/text`：

```bash
opencode service status     # 确认服务在跑
curl -s localhost:8000/api/llm | head -c 200
```

**记账协议**：你在对话里报告一笔收支，CxO 会额外输出一个 `event` 块；后端过 `contracts.validate_event` 才入库，然后进财务的流水与损益。数字由代码加总，模型只负责说话。

## 真实执行（AutoSwarm）

对话仍是本地模拟器；**派活是真的**。抽屉的第二栏能把一句话交给本机的 Codex / OpenCode / DSH，子代理在你给的工作区里动手，结果回写进对话与审计。

```bash
uv tool install --force git+https://github.com/HKUDS/AutoSwarm   # 或从源码装
autoswarm agents                                                 # 看本机哪几家可用
```

我们的记录目录默认 `backend/app/data/autoswarm`，各 CxO 的工作区在 `backend/app/data/workspaces/<agent>`。两者都不入库。设计取舍见 [ADR-0001](docs/adr-0001-autoswarm.md)。

## 明确没有做的

- **对话已接模型，但只在本地服务在线时。** 走本机 opencode 的 v2 API（默认 `opencode-go/deepseek-v4.1-flash`），不可达时退回 `backend/app/sim.py` 的模拟器，消息会标「沙箱」。
- **没有 ECE 会议协议。** 会议、材料包、任务包 schema 都还没落。这是骨架之后的第一件事。
- **没有 plugin 机制。** 权限矩阵里留了 `plugin.install` 的口子，实现没写。
- **没有真实财务数据。** 预算与审计都是示例值，界面上有标注。

## 结构

```
backend/app/
  db.py      schema、seed、9 份 JD
  sim.py     状态推进、沙箱回复、审批
  main.py    FastAPI 路由
frontend/src/
  pixels.ts          办公室的像素画法与精灵
  components/        Canvas、抽屉、图标
  views/             六个页面
  styles.css         设计令牌与全部样式
```
