import { Spinner, ToolbarButton } from "@fluentui/react-components";
import { bundleIcon, EditFilled, EditRegular, DocumentRegular } from "@fluentui/react-icons";
import { UserMessageV2 as CopilotUserMessage } from "@fluentui-copilot/react-copilot-chat";
import { Suspense } from "react";

import { useFormatTimestamp } from "./hooks/useFormatTimestamp";
import { IUserMessageProps } from "./chatbot/types";

import { Markdown } from "../core/Markdown";

import styles from "./AgentPreviewChatBot.module.css";

const EditIcon = bundleIcon(EditFilled, EditRegular);

// Image MIME types for preview display
const IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"];

export function UserMessage({
  message,
  onEditMessage,
}: IUserMessageProps): JSX.Element {
  const formatTimestamp = useFormatTimestamp();

  return (
    <CopilotUserMessage
      key={message.id}
      actionBar={
        <ToolbarButton
          appearance="transparent"
          aria-label="Edit"
          icon={<EditIcon aria-hidden={true} />}
          onClick={() => {
            onEditMessage(message.id);
          }}
        />
      }
      className={styles.userMessage}
      timestamp={
        message.more?.time ? formatTimestamp(new Date(message.more.time)) : ""
      }
    >
      {/* Display attached files */}
      {message.attachments && message.attachments.length > 0 && (
        <div style={{ 
          display: "flex", 
          flexWrap: "wrap", 
          gap: "8px", 
          marginBottom: message.content ? "8px" : "0"
        }}>
          {message.attachments.map((attachment, index) => (
            <div key={index} style={{ 
              display: "flex", 
              alignItems: "center",
              gap: "6px"
            }}>
              {IMAGE_TYPES.includes(attachment.type) ? (
                <img 
                  src={attachment.previewUrl || `data:${attachment.type};base64,${attachment.data}`}
                  alt={attachment.name}
                  style={{ 
                    maxWidth: "200px", 
                    maxHeight: "150px", 
                    borderRadius: "8px",
                    border: "1px solid var(--colorNeutralStroke1)"
                  }} 
                />
              ) : (
                <div style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                  padding: "6px 10px",
                  backgroundColor: "var(--colorNeutralBackground3)",
                  borderRadius: "6px",
                  fontSize: "12px"
                }}>
                  <DocumentRegular />
                  <span>{attachment.name}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      
      {/* Display text content */}
      {message.content && (
        <Suspense fallback={<Spinner size="small" />}>
          <Markdown content={message.content} />
        </Suspense>
      )}
    </CopilotUserMessage>
  );
}
