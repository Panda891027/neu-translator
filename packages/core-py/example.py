"""
Example usage of the expense agent.
Demonstrates how to process an invoice with the multimodal agent.
"""
import asyncio
from src import AgentLoop, Memory, AgentLoopOptions, Message, MessageRole
from src.types import TextContent, ImageContent, CopilotResponse, CopilotStatus


async def main():
    """Main example function"""

    # Initialize memory
    memory = Memory(memory_file="./example_memory.json")

    # Create agent with options
    options = AgentLoopOptions(memory=memory)
    agent = AgentLoop(options=options)

    print("=" * 60)
    print("Expense Processing Agent - Example")
    print("=" * 60)

    # Example 1: User provides an invoice image
    print("\n[User] Please process this lunch receipt")

    user_message = Message(
        role=MessageRole.USER,
        content="Please extract the expense information from this receipt image: ./invoice.jpg"
    )

    await agent.user_input([user_message])

    # Run agent iteration
    print("\n[Agent] Processing...")
    result = await agent.next()

    print(f"Actor: {result.actor}")
    print(f"Messages: {len(result.messages)}")
    print(f"Copilot Requests: {len(result.copilot_requests)}")

    # If there are copilot requests, simulate human review
    if result.copilot_requests:
        print("\n[Copilot Review Needed]")
        for req in result.copilot_requests:
            print(f"\nExpense ID: {req.extracted_data.get('expense_id', 'N/A')}")
            print(f"Extracted Data:")
            print(f"  Vendor: {req.extracted_data.get('vendor', 'N/A')}")
            print(f"  Amount: {req.extracted_data.get('amount', 0)} {req.extracted_data.get('currency', 'N/A')}")
            print(f"  Date: {req.extracted_data.get('date', 'N/A')}")
            print(f"  Category: {req.extracted_data.get('category', 'N/A')}")

            # Simulate human approval (in real system, this would be interactive)
            print("\n[Human Copilot] Reviewing...")

            # Create copilot response
            copilot_response = CopilotResponse(
                tool=req.tool,
                status=CopilotStatus.APPROVE,
                approved_data=req.extracted_data,
                reason="Data looks good"
            )

            # Add copilot response
            await agent.add_copilot_responses([copilot_response])

            print("[Human Copilot] Approved!")

        # Continue agent iteration after approval
        print("\n[Agent] Continuing after approval...")
        result = await agent.next()

        print(f"Actor: {result.actor}")
        print(f"Messages: {len(result.messages)}")

    # Print final messages
    print("\n" + "=" * 60)
    print("Conversation Summary")
    print("=" * 60)

    all_messages = await agent.get_messages()
    for i, msg in enumerate(all_messages, 1):
        print(f"\n{i}. Role: {msg.role.value}")
        if isinstance(msg.content, str):
            print(f"   Content: {msg.content[:100]}...")
        else:
            print(f"   Content parts: {len(msg.content)}")

    # Memory stats
    print("\n" + "=" * 60)
    print("Memory Statistics")
    print("=" * 60)
    stats = memory.get_stats()
    print(f"Total memories: {stats['total_memories']}")
    print(f"Categories: {stats['categories']}")

    print("\n[Done]")


if __name__ == "__main__":
    asyncio.run(main())
