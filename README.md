# Project Tracker - 项目进度跟踪系统

面向系统集成/工程项目的全流程进度跟踪工具，支持客户管理、供应商报价管理、价格参考归类、PDF/Excel 报价导入及可视化看板。

## 功能概览

| 模块 | 功能 |
|------|------|
| 看板 | 按月/季度/年统计项目落地率、毛利、金额（Chart.js 图表） |
| 项目管理 | 项目 CRUD + 多供应商报价（支持 CNY/HKD/MOP 三币种） |
| 客户管理 | 客户信息维护（可一键复制公司/联系人/电话/邮箱） |
| 价格参考 | 历史报价自动归类统计（均价/最低/最高/供应商列表） |
| 导入报价 | 支持 PDF / Excel / CSV 文件上传，自动解析入库 |

## 技术栈

- **后端**: Python FastAPI + SQLAlchemy + SQLite
- **前端**: 原生 HTML/CSS/JS + Chart.js
- **部署**: Docker + docker-compose

## 本地部署 (Docker Desktop for Windows)

### 前置条件

1. 安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. 确保 Docker 正常运行

### 启动步骤

```bat
# 方式一：双击批处理文件
start.bat

# 方式二：命令行
docker-compose up -d
```

启动后访问 **http://localhost:8000**

### 停止服务

```bat
docker-compose down
```

## 目录结构

```
project-tracker/
├── backend/
│   ├── app.py          # FastAPI 主应用 + 全部 API 路由
│   ├── models.py       # SQLAlchemy 数据模型
│   ├── database.py     # 数据库会话管理
│   └── requirements.txt
├── frontend/
│   ├── index.html      # SPA 入口
│   ├── css/style.css   # 样式表
│   └── js/app.js       # 前端逻辑
├── data/               # SQLite 数据库 & 上传文件（Volume 挂载）
├── Dockerfile
├── docker-compose.yml
└── start.bat           # Windows 一键启动脚本
```

## 推送到 GitHub

```bash
git init
git add .
git commit -m "Initial commit: Project Tracker"
git branch -M main
git remote add origin https://github.com/your-username/project-tracker.git
git push -u origin main
```

## 导入文件格式说明

### Excel/CSV

第一行为表头，系统自动识别以下列名：

- 供应商 / 公司 / 厂商 → 供应商公司
- 联系人 / 姓名 → 联系人
- 电话 / 手机 → 电话
- 邮箱 / E-mail → 邮箱
- 产品 / 设备名称 / 型号 / 品名 → 产品/服务详情
- 价格 / 单价 / 金额 → 价格
- 币种 / 货币 → 币种（默认 CNY）
- 类别 / 分类 → 产品类别

### PDF

系统会尝试从 PDF 文本中提取供应商信息和价格数据。
