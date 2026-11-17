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

## 明确没有做的

- **没有接任何模型。** CxO 的回复来自 `backend/app/sim.py` 的规则模拟器，消息上标「沙箱」。接模型是下一步，不是这一版。
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
