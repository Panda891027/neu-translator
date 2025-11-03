/**
 * Shared types for the expense agent frontend.
 * These types match the Python backend API responses.
 */

export type MessageRole = "user" | "assistant" | "tool" | "system";

export type TextContent = {
  type: "text";
  text: string;
};

export type ImageContent = {
  type: "image";
  image_url: string;
};

export type ToolCallPart = {
  type: "tool-call";
  toolCallId: string;
  toolName: string;
  args: Record<string, any>;
};

export type ToolResultPart = {
  type: "tool-result";
  toolCallId: string;
  toolName: string;
  output: any;
};

export type ContentPart = TextContent | ImageContent | ToolCallPart | ToolResultPart;

export type ModelMessage = {
  role: MessageRole;
  content: string | ContentPart[];
};

export type UserModelMessage = {
  role: "user";
  content: string | ContentPart[];
};

export type AssistantModelMessage = {
  role: "assistant";
  content: string | ContentPart[];
};

export type ToolModelMessage = {
  role: "tool";
  content: ToolResultPart[];
};

export type SystemModelMessage = {
  role: "system";
  content: string;
};

export type CopilotStatus = "approve" | "reject" | "refined";

export type CopilotRequest = {
  tool: {
    name: string;
    callId: string;
  };
  invoice_image: string;
  extracted_data: Record<string, any>;
};

export type CopilotResponse = {
  tool: {
    name: string;
    callId: string;
  };
  status: CopilotStatus;
  approved_data: Record<string, any>;
  reason: string;
};

export type NextActor = "user" | "agent";

export type AgentResponse = {
  actor: NextActor;
  messages: ModelMessage[];
  copilotRequests: CopilotRequest[];
  unprocessedToolCalls: ToolCallPart[];
  finishReason?: string;
};
