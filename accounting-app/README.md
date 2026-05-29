# 记账APP Demo

一个简单的个人记账应用，支持收入/支出记录、分类管理和统计报表。

## 技术栈

- **后端**: Python FastAPI + SQLAlchemy + MySQL
- **前端**: React + Vite + Ant Design

## 功能特性

- ✅ 记录收入和支出
- ✅ 多种分类（餐饮、交通、工资等）
- ✅ 按月统计报表
- ✅ 账单列表查看和删除
- ✅ 收支趋势图表

## 快速开始

### 1. 创建 MySQL 数据库

```sql
CREATE DATABASE accounting_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 后端启动

```bash
cd backend
pip install -r requirements.txt

# 配置数据库连接（修改 .env 文件）
# DATABASE_URL=mysql+pymysql://root:password@localhost:3306/accounting_db

python main.py
# 后端运行在 http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 3. 前端启动

```bash
cd frontend
npm install
npm run dev
# 前端运行在 http://localhost:5173
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/transactions | 获取账单列表 |
| POST | /api/transactions | 添加账单 |
| DELETE | /api/transactions/{id} | 删除账单 |
| GET | /api/categories | 获取分类列表 |
| GET | /api/statistics | 获取统计数据 |
