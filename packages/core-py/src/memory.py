"""
Memory system for expense agent.
Stores and retrieves learnings from copilot feedback.
"""
import json
import os
from typing import Any, Dict, List, Optional
from pathlib import Path
from .prompts.system_memory import get_memory_extraction_prompt


class Memory:
    """
    Manages agent memory and learnings.
    Persists to JSON file for continuity across sessions.
    """

    def __init__(self, memory_file: str = "./memory.json"):
        """
        Initialize memory system.

        Args:
            memory_file: Path to JSON file for storing memory
        """
        self.memory_file = Path(memory_file)
        self.memories: List[Dict[str, Any]] = []
        self._load_memory()

    def _load_memory(self) -> None:
        """Load memory from file if it exists"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memories = data.get("memories", [])
            except Exception as e:
                print(f"Warning: Failed to load memory file: {e}")
                self.memories = []
        else:
            self.memories = []

    def _save_memory(self) -> None:
        """Save memory to file"""
        try:
            # Create directory if it doesn't exist
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "memories": self.memories,
                    "count": len(self.memories)
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save memory: {e}")

    async def extract_memory(self, interaction: Dict[str, Any]) -> None:
        """
        Extract learning from copilot interaction.

        Args:
            interaction: Dictionary with 'req' and 'res' from copilot interaction
        """
        req = interaction.get("req", {})
        res = interaction.get("res", {})

        # Only extract memory from rejections or refinements
        if res.get("status") == "approve":
            return

        # Use LLM to extract structured learning
        from .llm import get_openrouter_client

        try:
            client = get_openrouter_client()

            # Prepare context for memory extraction
            context = f"""
## Original Request
Expense ID: {req.get('expense_id', 'N/A')}
Extracted Data: {json.dumps(req.get('extracted_data', {}), indent=2)}

## Copilot Response
Status: {res.get('status', 'N/A')}
Approved Data: {json.dumps(res.get('approved_data', {}), indent=2)}
Reason: {res.get('reason', 'N/A')}

Please extract learnings from this correction.
"""

            result = await client.generate(
                messages=[
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                system=get_memory_extraction_prompt(),
                temperature=0.5,
                max_tokens=800
            )

            # Parse learning
            learning = json.loads(result["content"])

            # Add timestamp
            from datetime import datetime
            learning["timestamp"] = datetime.now().isoformat()

            # Add to memory
            self.memories.append(learning)

            # Save to file
            self._save_memory()

        except Exception as e:
            print(f"Warning: Failed to extract memory: {e}")

    def provide_memory(self, query: Optional[str] = None, limit: int = 10) -> str:
        """
        Provide relevant memory context.

        Args:
            query: Optional query to filter relevant memories
            limit: Maximum number of memories to return

        Returns:
            Formatted memory string for injection into prompts
        """
        if not self.memories:
            return ""

        # For now, return most recent memories
        # TODO: Implement semantic search based on query
        recent_memories = self.memories[-limit:]

        # Format memories
        memory_text = "## Learned Patterns\n\n"

        for i, mem in enumerate(recent_memories, 1):
            memory_text += f"### Learning {i}: {mem.get('learning', 'N/A')}\n"
            memory_text += f"**Category**: {mem.get('category', 'N/A')}\n"
            memory_text += f"**Tags**: {', '.join(mem.get('tags', []))}\n"
            memory_text += f"**Apply to**: {mem.get('apply_to', 'N/A')}\n\n"

            details = mem.get('details', {})
            if details:
                memory_text += f"**Original**: {details.get('original', 'N/A')}\n"
                memory_text += f"**Corrected**: {details.get('corrected', 'N/A')}\n"
                memory_text += f"**Reason**: {details.get('reason', 'N/A')}\n\n"

        return memory_text

    def search_memory(self, tags: List[str]) -> List[Dict[str, Any]]:
        """
        Search memory by tags.

        Args:
            tags: List of tags to search for

        Returns:
            List of matching memories
        """
        matches = []
        for mem in self.memories:
            mem_tags = set(mem.get('tags', []))
            if any(tag in mem_tags for tag in tags):
                matches.append(mem)
        return matches

    def clear_memory(self) -> None:
        """Clear all memories"""
        self.memories = []
        self._save_memory()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Dictionary with memory stats
        """
        categories = {}
        for mem in self.memories:
            cat = mem.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_memories": len(self.memories),
            "categories": categories,
            "memory_file": str(self.memory_file),
        }
