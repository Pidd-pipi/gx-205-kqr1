# 逻辑推理题库系统

一个面向逻辑思维和智力训练爱好者的在线题库平台，提供多种推理题型、智能组卷、错题追踪和段位排名。

业务领域：全栈Web应用

## Docker Compose 快速启动

```bash
cp .env.example .env
docker compose up -d
```

访问地址：
- 前端：http://localhost:18505
- 后端健康检查：http://localhost:19505/health/
- API 前缀：前端通过 `/api` 由 Nginx 反向代理到后端

## 项目主要功能

- 题型分类题库：覆盖数字推理、图形推理、逻辑判断、类比推理、演绎推理。
- 智能组卷练习：支持按难度和题量生成练习卷。
- 答题与解析：在线选择答案，查看解析步骤和知识点说明。
- 错题本与收藏：记录错误次数和最后练习时间，便于专项复盘。
- 模拟考试模式：提供提交接口和成绩报告骨架。
- 学习进度追踪：统计题型正确率、答题总量、连续正确天数和练习时长。
- 难度分级与推荐：保留入门到专家五级难度和动态推荐接口。
- 排行榜与段位：展示青铜到王者段位体系的示例排名。

## 本地开发

前端：

```bash
cd frontend
npm install
npm run dev
```

后端：

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:19505
```

本地开发时需要可访问的 PostgreSQL，并按 `.env.example` 设置数据库变量。

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | React 18、TypeScript、Vite、Ant Design、Zustand |
| 后端 | Django 4.2、Django REST Framework、simplejwt、Pillow |
| 数据库 | PostgreSQL 15 |
| 部署 | Docker Compose、Nginx、Gunicorn |

## 项目目录结构

```text
.
├── backend/
│   ├── bank/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── config/
│   │   ├── settings.py
│   │   └── urls.py
│   ├── Dockerfile
│   ├── manage.py
│   └── requirements.txt
├── database/
│   └── init.sql
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── store/
│   │   └── types/
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── .env
├── .env.example
└── README.md
```

## 环境变量说明

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `COMPOSE_PROJECT_NAME` | Compose 项目名，避免中文目录名影响启动 | `gxlogic-bank` |
| `DB_NAME` | PostgreSQL 数据库名 | `gxlogic_bank` |
| `DB_USER` | PostgreSQL 用户名 | `gxlogic` |
| `DB_PASSWORD` | PostgreSQL 用户密码 | `gxlogic_pwd` |
| `JWT_SECRET` | simplejwt 签名密钥 | `change_me...` |
| `DJANGO_SECRET_KEY` | Django 应用密钥 | `change_me...` |
| `DJANGO_DEBUG` | 是否开启调试模式 | `0` |
| `FRONTEND_PORT` | 前端宿主机端口 | `18505` |
| `BACKEND_PORT` | 后端宿主机端口 | `19505` |
| `DB_PORT` | PostgreSQL 宿主机端口 | `33505` |

## Docker 部署说明

- `docker-compose.yml` 不使用 `version` 字段，并声明 `name: gxlogic-bank`。
- PostgreSQL 数据保存在命名卷 `db_data`，不会绑定到中文路径。
- 前端容器使用 Nginx 托管静态文件，`/api/` 反向代理到 `http://backend:19505/`。
- 后端等待数据库健康后执行迁移并启动 Gunicorn，前端等待后端健康后启动。
- 如端口冲突，修改 `.env` 中的 `FRONTEND_PORT`、`BACKEND_PORT`、`DB_PORT` 后重新执行 `docker compose up -d`。

常用命令：

```bash
docker compose ps
docker compose logs -f backend
docker compose down
```

## License

MIT
