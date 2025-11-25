基于 FastAPI 的轻量级电商练习项目，内置 JWT 鉴权、离线测试客户端、可视化测试面板与覆盖率展示，便于端到端演练接口与前端联调。

## 环境与依赖
- Python 3.10+
- 安装依赖：`pip install -r requirements.txt`

## 启动 API 与可视化测试台
1. 运行：`uvicorn api.ecommerce_api:app --reload --host 0.0.0.0 --port 8000`
2. 打开浏览器访问 `http://localhost:8000/test-dashboard`，可视化页面提供：
   - 左上角 Token 输入区（Bearer Token）
   - 一键触发的 pytest + 覆盖率执行（POST `/api/tests/run`）
   - 覆盖率 HTML 报告链接：`/coverage/index.html`
3. 也可直接访问接口：
   - 健康检查：`GET /api/health`
   - 登录获取 Token：`POST /api/auth/token`，请求体为 `{ "username": "admin", "password": "adminpass" }`

## 账户与角色
| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| admin | adminpass | admin（可管理商品） |
| user1001 | pass1001 | user |
| user1002 | pass1002 | user |
| user1003 | pass1003 | user |
| user2001 | pass2001 | user |

登录成功后会返回 `access_token`，在后续请求头中使用 `Authorization: Bearer <token>` 即可访问受保护接口。

## 离线测试与自动化
- 使用 `offline_requests.Session` 让测试在进程内直接调用 API 逻辑，无需启动外部服务。
- 运行测试：`pytest -q`
- 运行一键脚本：`./run.sh`（创建虚拟环境、启动 API、执行 pytest 并生成 `report.html` 覆盖报告）。
- 测试覆盖场景包含：必填字段校验、非法价格/数量、非法 Token、跨用户访问限制、促销与下单流程等。

## 目录速览
- `api/ecommerce_api.py`：核心接口、JWT 生成与验证、覆盖率驱动的测试执行端点。
- `utils/http_client.py`：封装的电商 API 客户端，默认携带 Bearer Token。
- `offline_requests/`：在测试中替代真实 HTTP 的极简 Session 实现。
- `assets/test_dashboard.html`：可视化测试面板静态页面。
- `tests/`：pytest 用例，自动重置内存数据并使用离线客户端调用接口。
