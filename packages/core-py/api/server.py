"""
FastAPI server for the expense agent.
Provides REST API endpoints for the frontend to communicate with the Python backend.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import uvicorn
import asyncio

from src import AgentLoop, Memory, AgentLoopOptions, Message, MessageRole
from src.types import CopilotResponse, CopilotStatus

# Initialize FastAPI app
app = FastAPI(
    title="Expense Agent API",
    description="Multimodal expense processing agent API",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instances (in production, use session management)
agents: Dict[str, AgentLoop] = {}
memory_instance = Memory(memory_file="./memory.json")


# Request/Response models
class MessageRequest(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    session_id: str
    messages: List[MessageRequest]


class CopilotResponseRequest(BaseModel):
    session_id: str
    tool_call_id: str
    tool_name: str
    status: str  # "approve", "reject", "refined"
    approved_data: Dict[str, Any]
    reason: str = ""


class ChatResponse(BaseModel):
    actor: str  # "user" or "agent"
    messages: List[Dict[str, Any]]
    copilot_requests: List[Dict[str, Any]]
    unprocessed_tool_calls: List[Dict[str, Any]]
    finish_reason: Optional[str] = None


class MemoryStatsResponse(BaseModel):
    total_memories: int
    categories: Dict[str, int]
    memory_file: str


# Helper functions
def get_or_create_agent(session_id: str) -> AgentLoop:
    """Get or create agent for a session"""
    if session_id not in agents:
        options = AgentLoopOptions(memory=memory_instance)
        agents[session_id] = AgentLoop(options=options)
    return agents[session_id]


def message_to_dict(msg: Message) -> Dict[str, Any]:
    """Convert Message to dict"""
    return {
        "role": msg.role.value,
        "content": msg.content if isinstance(msg.content, str) else [
            {
                "type": getattr(part, 'type', 'text'),
                "text": getattr(part, 'text', ''),
                "image_url": getattr(part, 'image_url', ''),
                "tool_call_id": getattr(part, 'tool_call_id', ''),
                "tool_name": getattr(part, 'tool_name', ''),
                "args": getattr(part, 'args', {}),
                "output": getattr(part, 'output', None),
            }
            for part in msg.content
        ]
    }


# API Endpoints

@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "service": "expense-agent-api"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    Accepts user messages and returns agent response.
    """
    try:
        agent = get_or_create_agent(request.session_id)

        # Convert request messages to Message objects
        messages = [
            Message(
                role=MessageRole(msg.role),
                content=msg.content
            )
            for msg in request.messages
        ]

        # Add user input
        if messages:
            await agent.user_input(messages)

        # Run agent iteration
        result = await agent.next()

        # Convert response
        return ChatResponse(
            actor=result.actor,
            messages=[message_to_dict(msg) for msg in result.messages],
            copilot_requests=[
                {
                    "tool": req.tool,
                    "invoice_image": req.invoice_image,
                    "extracted_data": req.extracted_data,
                }
                for req in result.copilot_requests
            ],
            unprocessed_tool_calls=[
                {
                    "tool_call_id": tc.tool_call_id,
                    "tool_name": tc.tool_name,
                    "args": tc.args,
                }
                for tc in result.unprocessed_tool_calls
            ],
            finish_reason=result.finish_reason,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/copilot-response")
async def copilot_response(request: CopilotResponseRequest):
    """
    Submit copilot response (human feedback).
    """
    try:
        agent = get_or_create_agent(request.session_id)

        # Create copilot response
        copilot_resp = CopilotResponse(
            tool={
                "name": request.tool_name,
                "call_id": request.tool_call_id,
            },
            status=CopilotStatus(request.status),
            approved_data=request.approved_data,
            reason=request.reason,
        )

        # Add to agent
        await agent.add_copilot_responses([copilot_resp])

        return {"status": "ok", "message": "Copilot response added"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/messages/{session_id}")
async def get_messages(session_id: str):
    """Get all messages for a session"""
    try:
        agent = get_or_create_agent(session_id)
        messages = await agent.get_messages()

        return {
            "session_id": session_id,
            "messages": [message_to_dict(msg) for msg in messages]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compact/{session_id}")
async def compact_history(session_id: str):
    """Compact message history for a session"""
    try:
        agent = get_or_create_agent(session_id)
        await agent.compact()

        return {"status": "ok", "message": "History compacted"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    if session_id in agents:
        del agents[session_id]
        return {"status": "ok", "message": f"Session {session_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/api/memory/stats", response_model=MemoryStatsResponse)
async def memory_stats():
    """Get memory statistics"""
    stats = memory_instance.get_stats()
    return MemoryStatsResponse(**stats)


@app.get("/api/memory/search")
async def search_memory(tags: str):
    """Search memory by tags (comma-separated)"""
    tag_list = [t.strip() for t in tags.split(",")]
    results = memory_instance.search_memory(tag_list)
    return {"results": results}


@app.delete("/api/memory")
async def clear_memory():
    """Clear all memory"""
    memory_instance.clear_memory()
    return {"status": "ok", "message": "Memory cleared"}


# Run server
if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
