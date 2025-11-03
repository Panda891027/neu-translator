# Expense Agent API 文档

Python后端API服务，供前端UI调用。

## 快速启动

```bash
cd packages/core-py
./start_server.sh
```

服务器启动在: `http://localhost:8000`

## API文档

启动服务器后访问：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 端点详情

### 1. 发送消息 - POST `/api/chat`

发送用户消息并获取agent响应

**请求体:**
```json
{
  "session_id": "user-123",
  "messages": [
    {
      "role": "user",
      "content": "请处理这张午餐发票: ./receipt.jpg"
    }
  ]
}
```

**响应:**
```json
{
  "actor": "agent",
  "messages": [...],
  "copilot_requests": [
    {
      "tool": {
        "name": "extract_invoice",
        "call_id": "abc123"
      },
      "invoice_image": "base64_encoded_image",
      "extracted_data": {
        "vendor": "餐厅名称",
        "date": "2024-01-15",
        "amount": 85.0,
        "currency": "CNY",
        "category": "meals"
      }
    }
  ],
  "unprocessed_tool_calls": [],
  "finish_reason": null
}
```

### 2. 人工审核反馈 - POST `/api/copilot-response`

提交人工对提取数据的审核结果

**请求体:**
```json
{
  "session_id": "user-123",
  "tool_call_id": "abc123",
  "tool_name": "extract_invoice",
  "status": "approve",  // "approve" | "reject" | "refined"
  "approved_data": {
    "vendor": "餐厅名称",
    "date": "2024-01-15",
    "amount": 85.0,
    "currency": "CNY",
    "category": "meals"
  },
  "reason": "数据正确"
}
```

**响应:**
```json
{
  "status": "ok",
  "message": "Copilot response added"
}
```

### 3. 获取会话消息 - GET `/api/messages/{session_id}`

获取某个会话的所有历史消息

**响应:**
```json
{
  "session_id": "user-123",
  "messages": [
    {
      "role": "user",
      "content": "请处理这张发票"
    },
    {
      "role": "assistant",
      "content": [...]
    }
  ]
}
```

### 4. 压缩历史 - POST `/api/compact/{session_id}`

压缩会话历史以节省内存

**响应:**
```json
{
  "status": "ok",
  "message": "History compacted"
}
```

### 5. 删除会话 - DELETE `/api/session/{session_id}`

删除一个会话及其所有数据

**响应:**
```json
{
  "status": "ok",
  "message": "Session user-123 deleted"
}
```

### 6. 记忆统计 - GET `/api/memory/stats`

获取记忆系统的统计信息

**响应:**
```json
{
  "total_memories": 15,
  "categories": {
    "vendor": 8,
    "amount": 5,
    "category": 2
  },
  "memory_file": "./memory.json"
}
```

### 7. 搜索记忆 - GET `/api/memory/search?tags=vendor,starbucks`

根据标签搜索记忆

**响应:**
```json
{
  "results": [
    {
      "learning": "Starbucks常被误识别为Starbuck",
      "tags": ["starbucks", "vendor_spelling"],
      "category": "vendor",
      "details": {...}
    }
  ]
}
```

### 8. 清空记忆 - DELETE `/api/memory`

清空所有学习记忆

**响应:**
```json
{
  "status": "ok",
  "message": "Memory cleared"
}
```

## 错误处理

所有错误返回格式：
```json
{
  "detail": "错误描述信息"
}
```

HTTP状态码：
- `200` - 成功
- `404` - 资源不存在
- `500` - 服务器错误

## 会话管理

每个用户/客户端应使用唯一的 `session_id` 来隔离会话。

建议格式：`user-{user_id}` 或 `session-{uuid}`

## CORS配置

当前配置允许所有来源 (`*`)。

生产环境请在 `api/server.py` 中修改：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 指定具体域名
    ...
)
```

## 安全建议

1. **生产环境**应使用环境变量配置API密钥
2. **启用HTTPS**保护数据传输
3. **添加认证**机制（JWT、API Key等）
4. **限流**防止滥用
5. **会话过期**自动清理旧会话

## 性能优化

- 当前使用内存字典存储会话，生产环境建议使用Redis
- 记忆系统建议使用数据库而非JSON文件
- 图片base64编码较大，考虑使用对象存储
- 添加缓存层提高响应速度
