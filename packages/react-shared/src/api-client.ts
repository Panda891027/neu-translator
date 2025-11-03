/**
 * API client for communicating with the Python expense agent backend.
 */
import type {
  AgentResponse,
  CopilotResponse,
  ModelMessage,
} from "./types.js";

export class ExpenseAgentAPI {
  private baseUrl: string;
  private sessionId: string | null;

  constructor(baseUrl: string = "http://localhost:8000") {
    this.baseUrl = baseUrl;
    this.sessionId = null;
  }

  /**
   * Set the session ID
   */
  setSessionId(sessionId: string) {
    this.sessionId = sessionId;
  }

  /**
   * Get the current session ID
   */
  getSessionId(): string {
    if (!this.sessionId) {
      // Generate a new session ID
      this.sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }
    return this.sessionId;
  }

  /**
   * Send a chat message and get agent response
   */
  async chat(userMessage: string): Promise<AgentResponse> {
    const sessionId = this.getSessionId();

    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        messages: [
          {
            role: "user",
            content: userMessage,
          },
        ],
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    const data = await response.json();
    return data as AgentResponse;
  }

  /**
   * Submit copilot response (human feedback)
   */
  async submitCopilotResponse(
    copilotResponse: CopilotResponse
  ): Promise<void> {
    const sessionId = this.getSessionId();

    const response = await fetch(`${this.baseUrl}/api/copilot-response`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        tool_call_id: copilotResponse.tool.callId,
        tool_name: copilotResponse.tool.name,
        status: copilotResponse.status,
        approved_data: copilotResponse.approved_data,
        reason: copilotResponse.reason,
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
  }

  /**
   * Get all messages for the current session
   */
  async getMessages(): Promise<ModelMessage[]> {
    const sessionId = this.getSessionId();

    const response = await fetch(`${this.baseUrl}/api/messages/${sessionId}`);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    const data = await response.json();
    return data.messages as ModelMessage[];
  }

  /**
   * Compact message history
   */
  async compact(): Promise<void> {
    const sessionId = this.getSessionId();

    const response = await fetch(`${this.baseUrl}/api/compact/${sessionId}`, {
      method: "POST",
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
  }

  /**
   * Delete the current session
   */
  async deleteSession(): Promise<void> {
    if (!this.sessionId) {
      return;
    }

    const response = await fetch(
      `${this.baseUrl}/api/session/${this.sessionId}`,
      {
        method: "DELETE",
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    this.sessionId = null;
  }

  /**
   * Get memory statistics
   */
  async getMemoryStats(): Promise<{
    total_memories: number;
    categories: Record<string, number>;
    memory_file: string;
  }> {
    const response = await fetch(`${this.baseUrl}/api/memory/stats`);

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Search memory by tags
   */
  async searchMemory(tags: string[]): Promise<any[]> {
    const tagsParam = tags.join(",");
    const response = await fetch(
      `${this.baseUrl}/api/memory/search?tags=${encodeURIComponent(tagsParam)}`
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    const data = await response.json();
    return data.results;
  }

  /**
   * Clear all memory
   */
  async clearMemory(): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/memory`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
  }
}
