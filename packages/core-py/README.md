# Expense Agent Core (Python)

多模态报销处理Agent，基于Qwen3-VL实现，架构与TypeScript版本保持一致。

## 功能特性

### 🤖 智能发票识别
- 使用Qwen3-VL多模态大模型识别发票和收据
- 支持多种图片格式：JPG、PNG、PDF
- 自动提取关键信息：商家、日期、金额、币种、类目等

### ✅ 自动验证
- 根据公司政策自动验证报销金额
- 检查必填字段完整性
- 识别异常和可疑费用
- 支持自定义验证规则

### 🔄 人机协作
- 人工审核提取的数据
- 支持批准、拒绝、修改
- 从反馈中学习，持续优化

### 🧠 记忆系统
- 保存历史纠正记录
- 自动学习常见错误模式
- 提高未来识别准确率

## 架构设计

本项目采用与TypeScript版本相同的架构模式：

```
packages/core-py/
├── src/
│   ├── agent.py              # Agent主循环
│   ├── context.py            # 对话上下文管理
│   ├── llm.py                # LLM集成（Qwen3-VL）
│   ├── memory.py             # 记忆系统
│   ├── types.py              # 类型定义
│   ├── tools/                # 工具集
│   │   ├── extract_invoice_tool.py    # 发票提取工具
│   │   ├── validate_expense_tool.py   # 验证工具
│   │   ├── read_tool.py               # 文件读取工具
│   │   └── thinking_tool.py           # 思考工具
│   └── prompts/              # 系统提示词
│       ├── system_workflow.py         # 工作流提示
│       └── system_memory.py           # 记忆提示
├── api/
│   ├── server.py             # FastAPI服务器
│   └── __init__.py
├── requirements.txt          # 依赖
├── pyproject.toml           # 项目配置
├── example.py               # Python使用示例
├── start_server.sh          # 启动API服务器脚本
└── README.md
```

## 快速开始

### 安装依赖

```bash
cd packages/core-py
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的API密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# Qwen API配置（必需）
QWEN_API_KEY=your_qwen_api_key_here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/api/v1

# OpenRouter配置（可选，作为备用）
OPENROUTER_API_KEY=your_openrouter_api_key_here

# 记忆文件路径
MEMORY_FILE=./memory.json
```

## 使用方式

### 方式一：启动API服务器（推荐用于前端集成）

启动FastAPI服务器，供前端UI（CLI或Web）调用：

```bash
# 使用启动脚本
./start_server.sh

# 或手动启动
cd packages/core-py
python api/server.py
```

服务器将在 `http://localhost:8000` 启动

访问API文档：`http://localhost:8000/docs`

#### API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | 发送消息并获取agent响应 |
| `/api/copilot-response` | POST | 提交人工审核反馈 |
| `/api/messages/{session_id}` | GET | 获取会话所有消息 |
| `/api/compact/{session_id}` | POST | 压缩会话历史 |
| `/api/session/{session_id}` | DELETE | 删除会话 |
| `/api/memory/stats` | GET | 获取记忆统计 |
| `/api/memory/search?tags=` | GET | 搜索记忆 |
| `/api/memory` | DELETE | 清空记忆 |

#### 前端调用示例

```typescript
// 发送消息
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: 'user-123',
    messages: [
      { role: 'user', content: '请处理这张发票：./invoice.jpg' }
    ]
  })
});

const data = await response.json();
// data.copilot_requests - 需要人工审核的请求
// data.messages - agent返回的消息

// 提交人工审核
if (data.copilot_requests.length > 0) {
  await fetch('http://localhost:8000/api/copilot-response', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: 'user-123',
      tool_call_id: data.copilot_requests[0].tool.call_id,
      tool_name: data.copilot_requests[0].tool.name,
      status: 'approve',
      approved_data: data.copilot_requests[0].extracted_data,
      reason: '数据正确'
    })
  });
}
```

### 方式二：直接使用Python（用于脚本和自动化）

```python
import asyncio
from src import AgentLoop, Memory, AgentLoopOptions, Message, MessageRole

async def main():
    # 初始化记忆系统
    memory = Memory(memory_file="./memory.json")

    # 创建Agent
    options = AgentLoopOptions(memory=memory)
    agent = AgentLoop(options=options)

    # 用户输入
    user_message = Message(
        role=MessageRole.USER,
        content="请处理这张午餐发票：./lunch_receipt.jpg"
    )
    await agent.user_input([user_message])

    # 运行Agent
    result = await agent.next()

    # 处理结果
    if result.copilot_requests:
        # 需要人工审核
        for req in result.copilot_requests:
            print(f"提取的数据: {req.extracted_data}")
            # 在实际应用中，这里会提示用户审核

asyncio.run(main())
```

更完整的示例请查看 `example.py`。

## 核心概念

### AgentLoop

Agent主循环，管理整个对话流程：

- **next()**: 执行一次迭代
- **user_input()**: 添加用户输入
- **add_copilot_responses()**: 添加人工审核反馈
- **get_messages()**: 获取所有消息
- **compact()**: 压缩历史消息节省tokens

### 工具系统

所有工具遵循统一的执行器模式：

```python
async def tool_executor(
    input_data: Dict[str, Any],
    options: Dict[str, Any],
    copilot_response: Optional[CopilotResponse] = None
) -> Dict[str, Any]:
    # 工具逻辑
    pass
```

#### 可用工具

| 工具 | 功能 | 需要审核 |
|------|------|---------|
| `extract_invoice` | 从图片提取发票信息 | ✅ 是 |
| `validate_expense` | 验证报销数据 | ❌ 否 |
| `read` | 读取文件内容 | ❌ 否 |
| `thinking` | 逐步推理规划 | ❌ 否 |

### 人机协作流程

```
1. Agent调用extract_invoice工具
2. 工具返回CopilotRequest（待审核）
3. 人工审核并返回CopilotResponse
4. Agent接收反馈，继续执行
5. 如果被拒绝/修改，保存到记忆系统
```

### 记忆系统

记忆系统自动从人工反馈中学习：

```python
# 初始化记忆
memory = Memory(memory_file="./memory.json")

# 获取统计
stats = memory.get_stats()
print(f"总记忆数: {stats['total_memories']}")

# 提供记忆上下文
context = memory.provide_memory()
```

## 报销政策配置

默认费用限额（可在 `validate_expense_tool.py` 中自定义）：

| 类别 | CNY限额 | USD限额 |
|------|---------|---------|
| 餐饮 (meals) | 200 | 30 |
| 差旅 (travel) | 5000 | 700 |
| 住宿 (accommodation) | 800 | 120 |
| 办公用品 (supplies) | 1000 | 150 |
| 娱乐 (entertainment) | 500 | 70 |

## 开发

### 运行示例

```bash
python example.py
```

### 运行测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

# 代码格式化
black src/
ruff check src/

# 类型检查
mypy src/
```

### 添加新工具

1. 在 `src/tools/` 下创建新工具文件
2. 定义输入输出schema（使用Pydantic）
3. 实现executor函数
4. 在 `src/tools/__init__.py` 中注册

示例：

```python
# src/tools/my_tool.py
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    param: str = Field(description="参数说明")

class MyToolOutput(BaseModel):
    result: str = Field(description="结果说明")

async def my_tool_executor(input_data, options, copilot_response=None):
    validated_input = MyToolInput(**input_data)
    # 工具逻辑
    return {
        "type": "tool-result",
        "payload": {"result": "..."}
    }

tool_definition = {
    "name": "my_tool",
    "description": "工具描述",
    "input_schema": MyToolInput.model_json_schema(),
    "output_schema": MyToolOutput.model_json_schema(),
}
```

## 与TypeScript版本的对应关系

| TypeScript | Python | 说明 |
|------------|--------|------|
| `packages/core` | `packages/core-py` | 核心包 |
| `agent.ts` | `agent.py` | Agent主类 |
| `context.ts` | `context.py` | 上下文管理 |
| `llm.ts` | `llm.py` | LLM集成 |
| `memory.ts` | `memory.py` | 记忆系统 |
| `tools/*.ts` | `tools/*.py` | 工具实现 |
| Gemini (OpenRouter) | Qwen3-VL | LLM模型 |

## API 参考

### AgentLoop

```python
class AgentLoop:
    def __init__(
        self,
        options: Optional[AgentLoopOptions] = None,
        messages: Optional[List[Message]] = None
    )

    async def next() -> AgentIterationResult
    async def user_input(messages: List[Message]) -> None
    async def add_copilot_responses(responses: List[CopilotResponse]) -> None
    async def get_messages() -> List[Message]
    async def compact() -> None
```

### Memory

```python
class Memory:
    def __init__(self, memory_file: str = "./memory.json")

    async def extract_memory(interaction: Dict[str, Any]) -> None
    def provide_memory(query: Optional[str] = None, limit: int = 10) -> str
    def search_memory(tags: List[str]) -> List[Dict[str, Any]]
    def get_stats() -> Dict[str, Any]
    def clear_memory() -> None
```

## 常见问题

### Q: 如何使用本地部署的Qwen模型？

A: 修改 `src/llm.py` 中的 `QwenVLClient`，使用本地API端点。

### Q: 如何自定义验证规则？

A: 编辑 `src/tools/validate_expense_tool.py` 中的 `POLICY_RULES` 字典。

### Q: 如何添加新的报销类别？

A: 在 `POLICY_RULES` 中添加新类别及其限额，同时更新系统提示词。

### Q: 记忆文件会很大吗？

A: 记忆文件以JSON格式存储，通常不会太大。可以定期调用 `memory.clear_memory()` 清理。

## 许可证

MIT License - 详见 LICENSE 文件

## 贡献

欢迎提交 Issue 和 Pull Request！

## 作者

Yanzhen Yu <yanzhen@arcfra.com>
