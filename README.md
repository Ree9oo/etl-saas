# 轻量多源数据同步 ETL SaaS 系统

> 轻量化离线数据同步平台：无需编码、可视化配置即可完成多关系型数据库的全量 / 增量定时同步、任务调度、日志监控与异常告警。聚焦中小 B 端、事业单位、制造企业等刚需场景，开箱即用、低成本、支持 SaaS 订阅 + 私有化部署。

<p align="center">
<!-- 项目主界面截图，将截图放置 docs/assets 目录下，替换文件名 -->
<img src="docs/assets/home.png" alt="系统首页概览" width="800"/>
</p>

## 📚 资源链接

- 📖 **官方文档**：https://xinxishuangyuan.cn/etl-docs/
- 🔗 **在线演示地址**：http://139.155.68.150:5173
  > 演示账号：`free` / `123456`

>
>⚠️ 演示环境为公共体验环境，数据会定期重置，请勿存放真实业务数据。

<!-- 更多截图示例，按需开启，图片提交到仓库 docs/assets 文件夹 -->

<p align="center">
<img src="docs/assets/datasource.png" alt="数据源管理页面" width="800"/>
<img src="docs/assets/createDatabase.gif" alt="新建数据源完整操作演示" width="800"/>
<img src="docs/assets/createTask.gif" alt="新建同步任务完整操作演示" width="800"/>
</p>

## ✨ 功能特性

- 🔐 用户权限：登录、JWT鉴权、路由守卫、**多租户数据隔离**
- 🗄️ 数据源管理：支持 MySQL / SQLServer / PostgreSQL / Oracle / 达梦，支持连接测试、读取表列表
- ⚙️ 同步任务：全量/增量同步、字段自动映射、目标自动建表、批量分页读取、手动触发执行
- ⏰ 定时调度：可视化Cron调度、任务启停、失败自动重试、超时强制终止
- 📊 日志监控：执行记录、同步行数、耗时统计、错误详情查看
- 📢 消息告警：任务失败推送钉钉、企业微信机器人
- 💰 商业化授权：免费版额度限制、付费解锁、私有化授权码校验
> 本地演示额外支持 SQLite；正式生产同步源/目标支持上面5种数据库。

## 🛠 技术栈

- **后端**：FastAPI + SQLAlchemy 2.0 + APScheduler + Pydantic v2 + JWT
- **前端**：Vue3
- **部署方式**：Docker / docker‑compose / 本地直接启动

## 📁 项目目录结构
```
etl-saas/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py          # 应用入口（路由注册 / CORS / 生命周期）
│   │   ├── config.py        # 配置（环境变量）
│   │   ├── database.py      # 引擎 / 会话 / 建表
│   │   ├── security.py      # 密码哈希 / JWT / 数据源密码加解密
│   │   ├── models.py        # ORM 模型
│   │   ├── schemas.py       # Pydantic 模型
│   │   ├── deps.py          # 鉴权依赖
│   │   ├── routers/         # 各模块路由
│   │   ├── services/        # 同步引擎 / 调度器 / 告警 / 连接工厂 / 额度
│   │   └── utils/response.py# 统一响应封装
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   ├── init_db.py        # 独立数据库初始化脚本（建库 / 建表 / 管理员 / 导出 SQL）
│   ├── add_comments.py   # 为已存在的表补充中文注释（ALTER 方式）
│   └── schema.sql        # 由 ORM 自动生成的 MySQL 建表 SQL（参考）
├── frontend/                # Vue3 前端
│   ├── src/
│   │   ├── views/           # 登录 / 概览 / 数据源 / 任务 / 日志 / 设置
│   │   ├── router/ Layout.vue / utils/request.js
│   ├── Dockerfile / nginx.conf
│   └── vite.config.js
├── docker-compose.yml       # 一键编排 MySQL + 后端 + 前端
├── start.sh                 # 本地一键启动（默认 SQLite）
└── README.md
```

## 🚀快速开始

### 方式一：Docker 一键部署（推荐生产 / 演示）

```bash
docker compose up -d --build
# 前端: http://localhost       后端 API: http://localhost:8000
```

### 方式二：本地直接启动（零外部依赖，使用 SQLite）

```bash
chmod +x start.sh
./start.sh
# 前端开发服务器: http://localhost:5173 （已代理 /api -> :8000）
```

> 仅后端（无前端）：
> ```bash
> cd backend && pip install -r requirements.txt
> uvicorn app.main:app --host 0.0.0.0 --port 8000
> ```

### 方式三：本地指定 MySQL 数据库（开发 / 生产）

本项目使用 SQLAlchemy ORM **自动建表**，无需手写 DDL；但 **MySQL 不会自动建库**，需先存在 `etl_saas` 库。两种方式任选：

**A. 一条命令完成初始化（推荐）**

```bash
cd backend
pip install -r requirements.txt                     # 已含 MySQL 驱动 pymysql
export DATABASE_URL="mysql+pymysql://root:你的密码@127.0.0.1:3306/etl_saas?charset=utf8mb4"
python init_db.py --create-database --init          # 自动建库 + 建表 + 默认管理员
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**B. 先看 SQL 再手动执行**

```bash
python init_db.py --export-sql schema.sql           # 导出 MySQL 建表 SQL
mysql -uroot -p etl_saas < schema.sql               # 在已建好的库中执行
python init_db.py                                   # 仅创建默认管理员（或启动后端时自动创建）
```

> 不执行任何脚本也可：只要 MySQL 中存在 `etl_saas` 库，直接 `uvicorn app.main:app` 启动，应用会在 `lifespan` 阶段自动 `create_all` 建表并创建管理员。

**补表注释（可选）**

`models.py` 的每个字段都已带中文 `comment`。新建表自动带注释；若之前的表是空注释建出来的，可用脚本补充：

```bash
python add_comments.py            # 仅打印将执行的 ALTER（dry-run，安全核对）
python add_comments.py --apply    # 真正写入注释
```

> 注释的单一来源是 `models.py`：改模型后重跑本脚本即同步。脚本会自动保留 `NOT NULL` 与 `AUTO_INCREMENT`，默认只打印 SQL，确认无误再加 `--apply`。

### 默认账号

```
管理员：admin / admin123
```
首次启动自动创建；普通用户注册后为 `free` 版本，受额度限制。

---

## ⚡核心同步能力

- **全量同步**：支持「清空后写入」与「追加写入」，整表完整同步。
- **增量同步**：基于增量字段（如 `update_time`）自动记录水位（`last_sync_value`），仅同步新增 / 修改数据，断点续传。
- **字段映射**：默认按列名自动映射；支持 `columns` 指定字段子集。
- **自动建表**：目标表不存在时按源表结构自动创建。
- **批量分页**：按 `batch_size` 分页读取 / 写入，避免大表同步 OOM。
- **过滤**：支持自定义 `WHERE` 条件精准筛选。
- **调度**：Cron 表达式驱动，任务启停实时生效；失败按 `retry_count` 自动重试；超过 `timeout` 自动终止。

## 📦 数据库驱动说明

表格

| 类型       | 驱动     | 备注                                                  |
| ---------- | -------- | ----------------------------------------------------- |
| MySQL      | pymysql  | 生产环境主流数据库                                    |
| PostgreSQL | psycopg2 | —                                                     |
| SQLServer  | pyodbc   | 宿主机需要预先安装 ODBC Driver 17                     |
| Oracle     | oracledb | —                                                     |
| 达梦       | dmPython | 需要安装达梦官方驱动，Python 环境可正常导入`dmPython` |
| SQLite     | 内置     | 仅用于本地演示与开发                                  |

##  👥 社区与支持 

| wx交流群                          | 微信                                   |
| --------------------------------- | -------------------------------------- |
| ![WX群](docs/assets/wx-group.png) | ![微信](docs/assets/wechat-pay.png) \| |

## 🙏 鸣谢

> 如果你觉得项目有用，请给一个 ⭐️ Star 支持！

- 后端：[FastAPI](https://gitee.com/link?target=https%3A%2F%2Ffastapi.tiangolo.com%2F) · [Pydantic](https://gitee.com/link?target=https%3A%2F%2Fdocs.pydantic.dev%2F) · [SQLAlchemy](https://gitee.com/link?target=https%3A%2F%2Fwww.sqlalchemy.org%2F) · [APScheduler](https://gitee.com/link?target=https%3A%2F%2Fgithub.com%2Fagronholm%2Fapscheduler)
- 前端：[Vue3](https://gitee.com/link?target=https%3A%2F%2Fcn.vuejs.org%2F) · [TypeScript](https://gitee.com/link?target=https%3A%2F%2Fwww.typescriptlang.org%2F) · [Vite](https://gitee.com/link?target=https%3A%2F%2Fvitejs.dev%2F) · [Element Plus](https://gitee.com/link?target=https%3A%2F%2Felement-plus.org%2F)