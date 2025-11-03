# Expense Agent

多模态报销处理Agent系统，基于Qwen3-VL实现。

## 架构

```
┌─────────────────────────────────────────────┐
│         Frontend (TypeScript)               │
│  ┌──────────────┐      ┌──────────────┐    │
│  │  CLI (Ink)   │      │  Web (Next)  │    │
│  └──────┬───────┘      └──────┬───────┘    │
│         │                     │             │
│         └──────────┬──────────┘             │
│                    │ HTTP API               │
└────────────────────┼────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│        Backend (Python FastAPI)             │
│  ┌──────────────────────────────────┐      │
│  │  AgentLoop + Qwen3-VL            │      │
│  │  - Invoice extraction            │      │
│  │  - Expense validation            │      │
│  │  - Memory & learning             │      │
│  └──────────────────────────────────┘      │
└─────────────────────────────────────────────┘
```

## 快速开始

### 1. 启动Python后端

```bash
cd packages/core-py

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 QWEN_API_KEY

# 启动服务器
./start_server.sh
```

后端将在 `http://localhost:8000` 启动

API文档：`http://localhost:8000/docs`

### 2. 使用CLI（命令行界面）

```bash
cd packages/cli

# 安装依赖
yarn install

# 启动CLI
yarn dev
```

### 3. 使用Web UI

```bash
cd packages/ui

# 配置API URL（可选）
cp .env.local.example .env.local

# 安装依赖
yarn install

# 启动开发服务器
yarn dev
```

访问 `http://localhost:3000`

## 项目结构

```
neu-translator/
├── packages/
│   ├── core-py/              # Python后端（FastAPI + Qwen3-VL）
│   │   ├── src/              # Agent核心逻辑
│   │   │   ├── agent.py      # AgentLoop主循环
│   │   │   ├── tools/        # 工具集
│   │   │   ├── llm.py        # Qwen3-VL集成
│   │   │   └── memory.py     # 记忆系统
│   │   ├── api/              # FastAPI服务器
│   │   │   └── server.py     # REST API端点
│   │   ├── requirements.txt
│   │   ├── API.md            # API文档
│   │   └── README.md
│   │
│   ├── cli/                  # 命令行界面（Ink）
│   │   └── src/
│   │       └── hooks/
│   │           └── use-agent.ts  # HTTP API客户端
│   │
│   ├── ui/                   # Web界面（Next.js）
│   │   └── src/
│   │       ├── app/api/next/route.ts  # API代理
│   │       └── app/hooks/use-agent.ts
│   │
│   └── react-shared/         # 共享代码
│       └── src/
│           ├── types.ts      # 类型定义
│           └── api-client.ts # API客户端库
│
└── README.md
```

## 功能特性

### 🤖 智能发票识别
- 使用Qwen3-VL多模态大模型识别发票和收据
- 支持JPG、PNG、PDF格式
- 自动提取：商家、日期、金额、币种、类目等

### ✅ 自动验证
- 根据公司政策验证报销金额
- 检查必填字段完整性
- 识别异常和可疑费用

### 🔄 人机协作
- 人工审核AI提取的数据
- 支持批准、拒绝、修改
- 从反馈中学习，持续优化

### 🧠 记忆系统
- 保存历史纠正记录
- 自动学习常见错误模式
- 提高未来识别准确率

## 开发

### 前端开发

```bash
# 在 packages/cli 或 packages/ui
yarn dev
```

### 后端开发

```bash
cd packages/core-py
python api/server.py
```

### 环境变量

**后端 (packages/core-py/.env)**:
```env
QWEN_API_KEY=your_qwen_api_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/api/v1
```

**前端 (可选，默认localhost:8000)**:
```env
EXPENSE_AGENT_API_URL=http://localhost:8000
```

## API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | 发送消息获取响应 |
| `/api/copilot-response` | POST | 提交人工审核 |
| `/api/messages/{id}` | GET | 获取会话历史 |
| `/api/memory/stats` | GET | 记忆统计 |

完整API文档：`packages/core-py/API.md`

## 许可证

MIT License

## 作者

Yanzhen Yu <yanzhen@arcfra.com>
