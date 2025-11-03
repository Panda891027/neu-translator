import type { CopilotResponse, AgentResponse } from "react-shared";
import { SessionManager } from "@/app/lib/storage";

const sessionManager = new SessionManager();

// Python backend API URL
const PYTHON_API_URL = process.env.EXPENSE_AGENT_API_URL || "http://localhost:8000";

export async function POST(req: Request) {
  const {
    copilotResponses,
    sessionId,
    userInput,
  }: {
    sessionId?: string;
    userInput?: string;
    copilotResponses?: CopilotResponse[];
  } = await req.json();

  const session = sessionId
    ? sessionManager.getSession(sessionId)
    : sessionManager.createSession();

  if (!session) {
    return new Response(`Session "${sessionId}" not found`, { status: 404 });
  }

  try {
    // Handle user input
    if (userInput) {
      // Send user input to Python backend
      const response = await fetch(`${PYTHON_API_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: session.id,
          messages: [
            {
              role: "user",
              content: userInput,
            },
          ],
        }),
        signal: req.signal,
      });

      if (!response.ok) {
        return new Response(`Python backend error: ${response.statusText}`, {
          status: 500,
        });
      }

      const agentResponse: AgentResponse = await response.json();

      // Update local session storage
      const messagesResp = await fetch(
        `${PYTHON_API_URL}/api/messages/${session.id}`
      );
      const messagesData = await messagesResp.json();
      sessionManager.setMessages(session.id, messagesData.messages);

      return new Response(
        JSON.stringify({
          sessionId: session.id,
          agentResponse: agentResponse,
        }),
        { status: 200 }
      );
    }

    // Handle copilot responses
    if (copilotResponses && copilotResponses.length > 0) {
      // Submit copilot responses to Python backend
      for (const copilotResponse of copilotResponses) {
        await fetch(`${PYTHON_API_URL}/api/copilot-response`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            session_id: session.id,
            tool_call_id: copilotResponse.tool.callId,
            tool_name: copilotResponse.tool.name,
            status: copilotResponse.status,
            approved_data: copilotResponse.approved_data,
            reason: copilotResponse.reason,
          }),
          signal: req.signal,
        });
      }

      // Continue agent loop by sending empty message
      const response = await fetch(`${PYTHON_API_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: session.id,
          messages: [],
        }),
        signal: req.signal,
      });

      if (!response.ok) {
        return new Response(`Python backend error: ${response.statusText}`, {
          status: 500,
        });
      }

      const agentResponse: AgentResponse = await response.json();

      // Update local session storage
      const messagesResp = await fetch(
        `${PYTHON_API_URL}/api/messages/${session.id}`
      );
      const messagesData = await messagesResp.json();
      sessionManager.setMessages(session.id, messagesData.messages);

      return new Response(
        JSON.stringify({
          sessionId: session.id,
          agentResponse: agentResponse,
        }),
        { status: 200 }
      );
    }

    // Just get current state
    return new Response(
      JSON.stringify({
        sessionId: session.id,
        agentResponse: {
          actor: "user",
          messages: [],
          copilotRequests: [],
          unprocessedToolCalls: [],
        },
      }),
      { status: 200 }
    );
  } catch (error) {
    console.error("Error proxying to Python backend:", error);
    return new Response(`Backend error: ${error}`, { status: 500 });
  }
}
