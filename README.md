# LoomLot-01 · 染坊缸染与色牢度抽检

靛蓝染坊台：按 **染坊 → 配方版本 → 染缸 → 染程 → 色牢度** 工序推进，聚焦缸染调度与抽检，不是库存出入库系统。

## 技术栈

| 层 | 技术 |
| --- | --- |
| Backend | FastAPI + SQLAlchemy 2 + Pydantic v2 + Postgres + JWT |
| Frontend | Svelte 4 + Vite + svelte-spa-router |
| 部署 | docker-compose（db + backend + frontend/nginx） |

## 端口

| 服务 | 端口 |
| --- | --- |
| 前端 | **3600** |
| 后端 API | **8600** |
| PostgreSQL | **5439** |

数据库账号：`loomlot` / `loomlot` / 库名 `loomlot`。

## 演示账号

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| `admin` | `123456` | 染坊主管 |
| `dyer` | `123456` | 染程操作员 |

容器启动时 entrypoint 自动建表并 seed。

## 快速启动

```bash
cd D:\work\document\bytecode\claudeCodePro\LoomLot\LoomLot-01
docker compose up -d --build
```

浏览器：http://localhost:3600  
API：http://localhost:8600/api/health

停止：

```bash
docker compose down
```

## 业务实体

1. **DyeHouse** — `name`, `waterNote`, `notes`
2. **RecipeVersion** — `dyeHouseId`, `recipeName`, `versionNo`, `isActive`, `maxFabricKg`
3. **Vat** — `dyeHouseId`, `vatCode`, `fiberType`, `capacityL`, `status` ∈ `ready|dyeing|drain`
4. **DyeLot** — `vatId`, `recipeName`, `fabricKg`, `startedAt`, `operatorName`
5. **FastnessCheck** — `dyeLotId`, `checkedAt`, `washFastness`(1–5), `rubFastness`(>0), `tempC`, `notes`

### 规则

- 仅当染缸状态为 `ready` 或 `dyeing` 时可新建染程，否则 409
- 新建染程后，染缸状态自动设为 `dyeing`
- 可选接口：`POST /api/vats/{id}/drain` 将染缸置为 `drain`

### 配方版本与命中规则

- 配方版本挂染坊：同坊同 `recipeName` 下 `versionNo` 唯一；`maxFabricKg` 必须为正
- **命中**：新建/更新染程时，`recipeName` 必须命中**目标染缸所属染坊**的某条启用版本；同坊同配方名有多条启用版本时，取 `versionNo` 最高者为命中版本。未命中（含版本已停用）→ **409**
- **上限**：`fabricKg` 不得超过命中版本的 `maxFabricKg`，否则 → **400**
- 命中与上限校验共用同一函数（`app/recipe_rules.py` 的 `validate_lot_against_version`），新建与更新染程均走该校验
- 更新染程时，仅当 `vatId` / `recipeName` / `fabricKg` 任一变化才重新命中校验；只改时间、操作员等字段不重新命中
- 停用版本不可再被新染程引用；历史染程仍按原 `recipeName` 文本展示，不受启停影响
- 染程表单的配方下拉只列所选染缸所属染坊的启用版本，与后端命中规则对账
- 权限：主管（`admin`）可新建/修改/启停/删除版本；操作员（`dyer`）只读版本列表，开染程仍受命中与上限约束
- 看板「启用配方版本」数 = 版本列表中启用行数（同源统计 `isActive = true`）

## 主要 API

- `POST /api/auth/login`（OAuth2 表单）
- `GET /api/auth/me`
- `GET/POST/PUT/DELETE /api/dye-houses`
- `GET/POST/PUT/DELETE /api/recipe-versions`（写操作仅主管；列表支持 `dyeHouseId`、`isActive` 过滤）
- `GET/POST/PUT/DELETE /api/vats` · `POST /api/vats/{id}/drain`
- `GET/POST/PUT/DELETE /api/dye-lots`
- `GET/POST/PUT/DELETE /api/fastness-checks`
- `GET /api/dashboard/stats`

除登录外需 `Authorization: Bearer <token>`。字段对外为 camelCase。

## 目录

```
LoomLot-01/
├── docker-compose.yml
├── backend/          # FastAPI
├── frontend/         # Svelte 4 + Vite + nginx
└── README.md
```

## 本地开发

### 数据库

```bash
docker compose up -d db
```

### 后端

```bash
cd backend
python -m venv .venv
# Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
$env:DATABASE_URL="postgresql+psycopg2://loomlot:loomlot@127.0.0.1:5439/loomlot"
python -c "from app.database import Base, engine; from app import models; Base.metadata.create_all(bind=engine)"
python -c "from app.seed import seed; seed()"
uvicorn app.main:app --reload --port 8600
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

开发态 Vite 将 `/api` 代理到 `http://127.0.0.1:8600`。
