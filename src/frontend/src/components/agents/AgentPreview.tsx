/**
 * =============================================================================
 * FOUNDRY AGENT ACCELERATOR - Agent Preview Component
 * =============================================================================
 * 
 * This is the main chat interface component. It handles:
 * - Displaying the chat conversation (user messages + AI responses)
 * - Sending messages to the backend API
 * - Receiving and processing streaming responses from the AI
 * - Managing chat state (message history, loading states)
 * 
 * HOW THE CHAT FLOW WORKS:
 * ------------------------
 * 1. User types a message and clicks send (or presses Enter)
 * 2. The message is added to the chat display
 * 3. A POST request is sent to /chat endpoint with the conversation history
 * 4. The backend sends the response as a stream (word by word)
 * 5. We process each chunk and update the UI in real-time
 * 6. When streaming completes, we show the final response
 * 
 * SSE (Server-Sent Events):
 * -------------------------
 * The backend uses SSE to stream responses. This means instead of waiting
 * for the complete response, we receive it piece by piece. This provides
 * a better user experience as they see the response being "typed out".
 * 
 * Message Types from Server:
 * - { type: "message", content: "..." } - A chunk of the response
 * - { type: "completed_message", content: "..." } - The full response
 * - { type: "stream_end" } - Stream finished, stop processing
 * 
 * =============================================================================
 */

import { ReactNode, useState, useMemo } from "react";
import {
  Body1,
  Button,
  Caption1,
  Title2,
} from "@fluentui/react-components";
import { ChatRegular, MoreHorizontalRegular } from "@fluentui/react-icons";

import { AgentIcon } from "./AgentIcon";
import { SettingsPanel } from "../core/SettingsPanel";
import { AgentPreviewChatBot } from "./AgentPreviewChatBot";
import { MenuButton } from "../core/MenuButton/MenuButton";
import { IChatItem, IFileAttachment } from "./chatbot/types";

import styles from "./AgentPreview.module.css";

/**
 * Agent Interface
 * Defines the structure of agent configuration data
 */
interface IAgent {
  id: string;
  object: string;
  created_at: number;
  name: string;
  description?: string | null;
  model: string;
  instructions?: string;
  tools?: Array<{ type: string }>;
  top_p?: number;
  temperature?: number;
  tool_resources?: {
    file_search?: {
      vector_store_ids?: string[];
    };
    [key: string]: any;
  };
  metadata?: Record<string, any>;
  response_format?: "auto" | string;
}

/**
 * Agent Preview Props Interface
 */
interface IAgentPreviewProps {
  resourceId: string;
  agentDetails: IAgent;
}


/**
 * Agent Preview Component
 * 
 * The main chat interface component that manages the conversation with the AI agent.
 * Handles sending messages, receiving streaming responses, and displaying the chat.
 * 
 * @param {IAgentPreviewProps} props - Component properties
 * @param {string} props.resourceId - Identifier for the chat resource
 * @param {IAgent} props.agentDetails - Agent configuration (name, description, logo)
 * 
 * @returns {ReactNode} The complete chat interface
 */
export function AgentPreview({ agentDetails }: IAgentPreviewProps): ReactNode {
  // -------------------------------------------------------------------------
  // STATE MANAGEMENT
  // -------------------------------------------------------------------------
  
  /** Controls whether the settings panel is visible */
  const [isSettingsPanelOpen, setIsSettingsPanelOpen] = useState(false);
  
  /** Array of all messages in the conversation */
  const [messageList, setMessageList] = useState<IChatItem[]>([]);
  
  /** True when waiting for/receiving AI response */
  const [isResponding, setIsResponding] = useState(false);

  // -------------------------------------------------------------------------
  // EVENT HANDLERS
  // -------------------------------------------------------------------------

  /**
   * Handle settings panel visibility changes
   * @param {boolean} isOpen - Whether the panel should be open
   */
  const handleSettingsPanelOpenChange = (isOpen: boolean) => {
    setIsSettingsPanelOpen(isOpen);
  };

  /**
   * Start a new chat conversation
   * Clears all messages and resets the session
   */
  const newThread = () => {
    setMessageList([]);
    deleteAllCookies();
  };

  /**
   * Delete all browser cookies for the current session
   * Used when starting a new chat to ensure clean state
   */
  const deleteAllCookies = (): void => {
    document.cookie.split(";").forEach((cookieStr: string) => {
      const trimmedCookieStr = cookieStr.trim();
      const eqPos = trimmedCookieStr.indexOf("=");
      const name =
        eqPos > -1 ? trimmedCookieStr.substring(0, eqPos) : trimmedCookieStr;
      document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
    });
  };

  // -------------------------------------------------------------------------
  // CHAT MESSAGE HANDLING
  // -------------------------------------------------------------------------

  /**
   * Send a message to the AI agent
   * 
   * This is the main function that handles sending user messages to the backend.
   * It creates a user message, adds it to the chat, sends it to the /chat endpoint,
   * and sets up streaming to receive the AI's response.
   * 
   * @param {string} message - The user's message text
   * @param {IFileAttachment[]} attachments - Optional file attachments (images, documents)
   */
  const onSend = async (message: string, attachments?: IFileAttachment[]) => {
    // Step 1: Create the user message object
    const userMessage: IChatItem = {
      id: `user-${Date.now()}`,
      content: message,
      role: "user",
      attachments: attachments,
      more: { time: new Date().toISOString() },
    };

    // Step 2: Add user message to the chat display
    setMessageList((prev) => [...prev, userMessage]);

    try {
      // Step 3: Prepare the request payload
      // Include all messages (history + new message) for context
      // Convert attachments to the format expected by the backend
      const messages = [...messageList, userMessage].map((item) => ({
        role: item.role,
        content: item.content,
        attachments: item.attachments?.map((att) => ({
          name: att.name,
          type: att.type,
          data: att.data,
        })) || [],
      }));
      const postData = {messages};
      // IMPORTANT: Add credentials: 'include' if server cookies are critical
      // and if your backend is on the same domain or properly configured for cross-site cookies.

      setIsResponding(true);      
      const response = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(postData),
        credentials: "include", // <--- allow cookies to be included
      });

      // Log out the response status in case there’s an error
      console.log(
        "[ChatClient] Response status:",
        response.status,
        response.statusText
      );

      // If server returned e.g. 400 or 500, that’s not an exception, but we can check manually:
      if (!response.ok) {
        console.error(
          "[ChatClient] The server has returned an error:",
          response.status,
          response.statusText
        );
        return;
      }

      if (!response.body) {
        throw new Error(
          "ReadableStream not supported or response.body is null"
        );
      }

      console.log("[ChatClient] Starting to handle streaming response...");
      handleMessages(response.body);
    } catch (error: any) {
      setIsResponding(false);
      if (error.name === "AbortError") {
        console.log("[ChatClient] Fetch request aborted by user.");
      } else {
        console.error("[ChatClient] Fetch failed:", error);
      }
    }
  };

  const handleMessages = (
    stream: ReadableStream<Uint8Array<ArrayBufferLike>>
  ) => {
    let chatItem: IChatItem | null = null;
    let accumulatedContent = "";
    let isStreaming = true;
    let buffer = "";

    // Create a reader for the SSE stream
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    
    const readStream = async () => {
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          console.log("[ChatClient] SSE stream ended by server.");
          break;
        }

        // Convert the incoming Uint8Array to text
        const textChunk = decoder.decode(value, { stream: true });
        console.log("[ChatClient] Raw chunk from stream:", textChunk);

        buffer += textChunk;
        let boundary = buffer.indexOf("\n");

        // We process line-by-line.
        while (boundary !== -1) {
          const chunk = buffer.slice(0, boundary).trim();
          buffer = buffer.slice(boundary + 1);

          console.log("[ChatClient] SSE line:", chunk); // log each line we extract

          if (chunk.startsWith("data: ")) {
            // Attempt to parse JSON
            const jsonStr = chunk.slice(6);
            let data;
            try {
              data = JSON.parse(jsonStr);
            } catch (err) {
              console.error("[ChatClient] Failed to parse JSON:", jsonStr, err);
              boundary = buffer.indexOf("\n");
              continue;
            }

            console.log("[ChatClient] Parsed SSE event:", data);

            if (data.error) {
              if (!chatItem) {
                chatItem = createAssistantMessageDiv();
                console.log(
                  "[ChatClient] Created new messageDiv for assistant."
                );
              }

              setIsResponding(false);
              appendAssistantMessage(
                chatItem,
                data.error.message || "An error occurred.",
                false
              );
              return;
            }

            // Check the data type to decide how to update the UI
            if (data.type === "stream_end") {
              // End of the stream
              console.log("[ChatClient] Stream end marker received.");
              setIsResponding(false);
              
              break;
            } 
            
            else {
              if (!chatItem) {
                chatItem = createAssistantMessageDiv();
                console.log(
                  "[ChatClient] Created new messageDiv for assistant."
                );
              }

              if (data.type === "completed_message") {
                clearAssistantMessage(chatItem);
                accumulatedContent = data.content;
                isStreaming = false;
                console.log(
                  "[ChatClient] Received completed message:",
                  accumulatedContent
                );

                setIsResponding(false);
              } else {
                accumulatedContent += data.content;
                console.log(
                  "[ChatClient] Received streaming chunk:",
                  data.content
                );
              }

            //   // Update the UI with the accumulated content
              appendAssistantMessage(chatItem, accumulatedContent, isStreaming);
            }
          }

          boundary = buffer.indexOf("\n");
        }
      }
    };

    // Catch errors from the stream reading process
    readStream().catch((error) => {
      console.error("[ChatClient] Stream reading failed:", error);
    });
  };

  const createAssistantMessageDiv: () => IChatItem = () => {
    var item = { id: crypto.randomUUID(), content: "", isAnswer: true, more: { time: new Date().toISOString() } };
    setMessageList((prev) => [...prev, item]);
    return item;
  };
  const appendAssistantMessage = (
    chatItem: IChatItem,
    accumulatedContent: string,
    isStreaming: boolean,
  ) => {
    try {
      // Preprocess content to convert citations to links using the updated annotation data

      if (!chatItem) {
        throw new Error("Message content div not found in the template.");
      }

      // Set the innerHTML of the message text div to the HTML content
      chatItem.content = accumulatedContent;
      setMessageList((prev) => {
        return [...prev.slice(0, -1), { ...chatItem }];
      });

      // Use requestAnimationFrame to ensure the DOM has updated before scrolling
      // Only scroll if stop streaming
      if (!isStreaming) {
        requestAnimationFrame(() => {
          const lastChild = document.getElementById(`msg-${chatItem.id}`);
          if (lastChild) {
            lastChild.scrollIntoView({ behavior: "smooth", block: "end" });
          }
       });
      }
    } catch (error) {
      console.error("Error in appendAssistantMessage:", error);
    }
  };

  const clearAssistantMessage = (chatItem: IChatItem) => {
    if (chatItem) {
      chatItem.content = "";
    }
  };
  const menuItems = [
    {
      key: "settings",
      children: "Settings",
      onClick: () => {
        setIsSettingsPanelOpen(true);
      },
    },
    {
      key: "terms",
      children: (
        <a
          className={styles.externalLink}
          href="https://aka.ms/aistudio/terms"
          target="_blank"
          rel="noopener noreferrer"
        >
          Terms of Use
        </a>
      ),
    },
    {
      key: "privacy",
      children: (
        <a
          className={styles.externalLink}
          href="https://go.microsoft.com/fwlink/?linkid=521839"
          target="_blank"
          rel="noopener noreferrer"
        >
          Privacy
        </a>
      ),
    },
    {
      key: "feedback",
      children: "Send Feedback",
      onClick: () => {
        // Handle send feedback click
        alert("Thank you for your feedback!");
      },
    },
  ];

  const chatContext = useMemo(
    () => ({
      messageList,
      isResponding,
      onSend,
    }),
    [messageList, isResponding]
  );

  return (
    <div className={styles.container}>
      <div className={styles.topBar}>
        <div className={styles.leftSection}>
          {messageList.length > 0 && (
            <>
              <AgentIcon
                alt=""
                iconClassName={styles.agentIcon}
                iconName={agentDetails.metadata?.logo}
              />
              <Body1 className={styles.agentName}>{agentDetails.name}</Body1>
            </>
          )}
        </div>
        <div className={styles.rightSection}>
          {" "}
          <Button
            appearance="subtle"
            icon={<ChatRegular aria-hidden={true} />}
            onClick={newThread}
          >
            New Chat
          </Button>{" "}
          <MenuButton
            menuButtonText=""
            menuItems={menuItems}
            menuButtonProps={{
              appearance: "subtle",
              icon: <MoreHorizontalRegular />,
              "aria-label": "Settings",
            }}
          />
        </div>
      </div>
      <div className={styles.content}>          <>
            {messageList.length === 0 && (
              <div className={styles.emptyChatContainer}>
                <AgentIcon
                  alt=""
                  iconClassName={styles.emptyStateAgentIcon}
                  iconName={agentDetails.metadata?.logo}
                />
                <Caption1 className={styles.agentName}>
                  {agentDetails.name}
                </Caption1>
                <Title2>How can I help you today?</Title2>
              </div>
            )}
            <AgentPreviewChatBot
              agentName={agentDetails.name}
              agentLogo={agentDetails.metadata?.logo}
              chatContext={chatContext}            />          </>
      </div>

      {/* Settings Panel */}
      <SettingsPanel
        isOpen={isSettingsPanelOpen}
        onOpenChange={handleSettingsPanelOpenChange}
      />
    </div>
  );
}
