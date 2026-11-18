# E2E 验收跑

```bash
# 独立实例，不碰开发数据
cd backend
LIFEOAC_DB=/tmp/lifeoac-test/test.db AUTOSWARM_HOME=/tmp/lifeoac-test/asw \
  uv run uvicorn app.main:app --port 8001

cd ..
LIFEOAC_APP=http://127.0.0.1:8001 python3 tests/e2e/runner.py
```

模拟的"你"只走 HTTP；断言由脚本做。每个场景的对话原文与判定写进 `report-<时间>.md`。

七个场景覆盖一家公司的全年节奏：定目标、立项、非业务请求、新产品、日常汇总、记忆问答、复盘。
建这套用例的目的是**先写验收再实现**——测试不过的地方，就是下一步要造的东西。
