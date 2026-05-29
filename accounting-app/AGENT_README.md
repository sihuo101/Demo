# 智能记账助手使用说明

## 功能特性

### 🤖 智能对话
- 通过自然语言与助手交流
- 自动识别记账、查询、统计、计算等意图
- 支持多轮对话，保持上下文

### 📝 记账功能
- 语音或文字输入记账信息
- 自动匹配分类
- 示例：
  - "帮我记一笔午饭35元"
  - "今天打车花了20"
  - "工资到账8000"

### 📊 查询统计
- 查询账单明细
- 获取收支统计
- 示例：
  - "这个月花了多少钱"
  - "查看最近的账单"
  - "本月餐饮支出多少"

### 🧮 计算能力
- 基础算术计算
- 账单相关计算（求和、平均、占比）
- 月度对比、增长率计算
- 储蓄预测
- 示例：
  - "帮我算一下 125 + 378 等于多少"
  - "日均支出多少"
  - "餐饮支出占总支出的比例"
  - "如果每月存2000，一年后有多少"

### 🎤 语音输入
- 使用浏览器内置语音识别
- 支持中文普通话
- 需要 Chrome 浏览器

---

## 配置说明

### 1. 后端配置

编辑 `backend/.env` 文件：

```env
# 数据库配置
DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/accounting_db

# LLM 配置
LLM_PROVIDER=openai_compatible
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

### 2. 支持的国产模型

#### DeepSeek
```env
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

#### 通义千问
```env
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-turbo
```

#### 智谱 GLM
```env
LLM_API_KEY=xxx
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-4
```

#### 月之暗面 Kimi
```env
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://api.moonshot.cn/v1
LLM_MODEL=moonshot-v1-8k
```

### 3. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 4. 启动服务

```bash
# 后端
cd backend
python main.py

# 前端
cd frontend
npm install
npm run dev
```

---

## 使用说明

### 新建对话
1. 点击左侧"新建"按钮
2. 或直接发送消息，系统自动创建对话

### 发送消息
- 在输入框输入消息
- 按 Enter 发送，Shift+Enter 换行
- 点击麦克风图标进行语音输入

### 管理对话
- 点击对话列表切换对话
- 点击删除图标删除对话

---

## 常见问题

### Q: 语音输入不工作？
A: 请确保：
1. 使用 Chrome 浏览器
2. 允许麦克风权限
3. 网络连接正常

### Q: 智能体没有响应？
A: 请检查：
1. LLM 配置是否正确
2. API Key 是否有效
3. 后端服务是否正常运行

### Q: 如何切换模型？
A: 修改 `.env` 文件中的 `LLM_BASE_URL` 和 `LLM_MODEL`，重启后端服务

### Q: 支持哪些浏览器？
A: 推荐使用 Chrome，语音功能需要 Chrome 支持

---

## 技术架构

```
前端 (React)
    ↓
API 请求 (SSE 流式)
    ↓
后端 (FastAPI)
    ↓
智能体服务 (Agent Service)
    ↓
LLM 接口 (OpenAI 兼容)
    ↓
工具执行 (Tools)
    ↓
数据库 (MySQL)
```

---

## 开发说明

### 添加新工具

1. 在 `backend/services/tools.py` 中定义工具
2. 在 `TOOLS_DEFINITION` 中添加工具描述
3. 在 `execute_tool` 中实现执行逻辑

### 添加新计算类型

1. 在 `backend/services/calculator.py` 中添加计算方法
2. 在 `backend/services/tools.py` 的 `_calculate` 中添加映射

### 自定义系统提示词

编辑 `backend/services/agent.py` 中的 `SYSTEM_PROMPT` 变量
