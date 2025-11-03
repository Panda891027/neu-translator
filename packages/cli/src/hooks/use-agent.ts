import type { CopilotResponse } from "react-shared";
import { ExpenseAgentAPI } from "react-shared";
import { createRef, useCallback } from "react";
import { useAgentStore } from "react-shared";

// API client instance
const apiClientRef = createRef<ExpenseAgentAPI>();
apiClientRef.current = null;

const runningRef = createRef<boolean>();
runningRef.current = false;

const abortController = createRef<AbortController | null>();
abortController.current = null;

// Get or create API client
function getAPIClient(): ExpenseAgentAPI {
  if (!apiClientRef.current) {
    // Read API URL from environment or use default
    const apiUrl = process.env.EXPENSE_AGENT_API_URL || "http://localhost:8000";
    apiClientRef.current = new ExpenseAgentAPI(apiUrl);
  }
  return apiClientRef.current;
}

export const useAgent = () => {
  const messages = useAgentStore((s) => s.messages);
  const setMessages = useAgentStore((s) => s.setMessages);

  const unprocessedToolCalls = useAgentStore((s) => s.unprocessedToolCalls);
  const setUnprocessedToolCalls = useAgentStore(
    (s) => s.setUnprocessedToolCalls
  );

  const currentActor = useAgentStore((s) => s.currentActor);
  const setCurrentActor = useAgentStore((s) => s.setCurrentActor);

  const copilotRequests = useAgentStore((s) => s.copilotRequests);
  const setCopilotRequests = useAgentStore((s) => s.setCopilotRequests);

  const doNext = useCallback(async () => {
    const apiClient = getAPIClient();
    setCurrentActor("agent");

    while (runningRef.current) {
      try {
        // Note: The Python backend handles the iteration internally
        // We don't need to call next() repeatedly like the old implementation
        // The backend will process until it needs copilot feedback or finishes

        // Get current messages to check if we need to make a request
        const currentMessages = await apiClient.getMessages();
        setMessages(currentMessages);

        // Since we've already sent the user input or copilot response,
        // the backend should have processed it. We just need to get the latest state.
        break;

      } catch (error) {
        const isAbortError =
          error instanceof Error && error.name === "AbortError";
        if (!isAbortError) {
          console.error("Error in agent loop:", error);
        }
        runningRef.current = false;
        setCurrentActor("user");
        break;
      }
    }
  }, [
    setCurrentActor,
    setMessages,
  ]);

  const submitAgent = async (input: string) => {
    runningRef.current = true;
    const apiClient = getAPIClient();

    try {
      // Send chat message to Python backend
      const agentResponse = await apiClient.chat(input);

      // Check for copilot requests
      if (agentResponse.copilotRequests && agentResponse.copilotRequests.length > 0) {
        setCopilotRequests(agentResponse.copilotRequests);
        setCurrentActor("agent");
      } else {
        setCurrentActor(agentResponse.actor);
      }

      // Update messages
      const allMessages = await apiClient.getMessages();
      setMessages(allMessages);

      // Update unprocessed tool calls
      setUnprocessedToolCalls(agentResponse.unprocessedToolCalls);

      runningRef.current = false;
    } catch (error) {
      console.error("Error submitting to agent:", error);
      runningRef.current = false;
      setCurrentActor("user");
    }
  };

  const finishCopilotRequest = async (copilotResponses: CopilotResponse[]) => {
    setCopilotRequests([]);
    const apiClient = getAPIClient();

    try {
      // Submit copilot responses to Python backend
      for (const response of copilotResponses) {
        await apiClient.submitCopilotResponse(response);
      }

      // Continue the agent loop by sending a follow-up chat request
      // The backend will process the copilot responses and continue
      const agentResponse = await apiClient.chat("");

      if (agentResponse.copilotRequests && agentResponse.copilotRequests.length > 0) {
        setCopilotRequests(agentResponse.copilotRequests);
      } else {
        setCurrentActor(agentResponse.actor);
      }

      // Update messages
      const allMessages = await apiClient.getMessages();
      setMessages(allMessages);

      // Update unprocessed tool calls
      setUnprocessedToolCalls(agentResponse.unprocessedToolCalls);

    } catch (error) {
      console.error("Error finishing copilot request:", error);
      setCurrentActor("user");
    }
  };

  const stop = () => {
    runningRef.current = false;
    abortController.current?.abort();
    setCurrentActor("user");
  };

  const compact = useCallback(async () => {
    const apiClient = getAPIClient();
    try {
      await apiClient.compact();
    } catch (error) {
      console.error("Error compacting history:", error);
    }
  }, []);

  const getMemoryStats = useCallback(async () => {
    const apiClient = getAPIClient();
    try {
      return await apiClient.getMemoryStats();
    } catch (error) {
      console.error("Error getting memory stats:", error);
      return null;
    }
  }, []);

  return {
    messages,
    currentActor,
    unprocessedToolCalls,
    submitAgent,
    copilotRequests,
    finishCopilotRequest,
    stop,
    compact,
    getMemoryStats,
  };
};
