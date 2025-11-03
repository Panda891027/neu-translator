"""
Basic tests for AgentLoop
"""
import pytest
from src import AgentLoop, Memory, AgentLoopOptions, Message, MessageRole


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test that agent can be initialized"""
    agent = AgentLoop()
    assert agent is not None
    assert agent.context is not None
    assert agent.tool_definitions is not None


@pytest.mark.asyncio
async def test_agent_with_memory():
    """Test that agent can be initialized with memory"""
    memory = Memory(memory_file="./test_memory.json")
    options = AgentLoopOptions(memory=memory)
    agent = AgentLoop(options=options)

    assert agent.options.memory is not None
    assert agent.options.memory == memory


@pytest.mark.asyncio
async def test_user_input():
    """Test adding user input"""
    agent = AgentLoop()

    message = Message(
        role=MessageRole.USER,
        content="Hello, agent!"
    )

    await agent.user_input([message])

    messages = await agent.get_messages()
    assert len(messages) == 1
    assert messages[0].role == MessageRole.USER
    assert messages[0].content == "Hello, agent!"


@pytest.mark.asyncio
async def test_memory_stats():
    """Test memory statistics"""
    memory = Memory(memory_file="./test_memory.json")

    stats = memory.get_stats()
    assert "total_memories" in stats
    assert "categories" in stats
    assert "memory_file" in stats

    # Clean up
    memory.clear_memory()
