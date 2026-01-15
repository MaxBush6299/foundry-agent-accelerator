/**
 * =============================================================================
 * FOUNDRY AGENT ACCELERATOR - Chat Input Component
 * =============================================================================
 * 
 * This component renders the text input field where users type their messages.
 * It uses FluentUI Copilot's ChatInput component for a polished UI experience.
 * 
 * WHAT THIS FILE DOES:
 * --------------------
 * 1. Renders a text input with send button
 * 2. Handles user input and submission
 * 3. Shows loading state while the AI is generating a response
 * 4. Supports keyboard submission (Enter key)
 * 5. Supports file attachments (images and documents)
 * 
 * COMPONENT PROPS:
 * ----------------
 * - onSubmit: Function called when user sends a message (with optional attachments)
 * - isGenerating: Boolean indicating if AI is currently responding
 * - currentUserMessage: Optional preset message text
 * 
 * SUPPORTED FILE TYPES:
 * ---------------------
 * - Images: JPEG, PNG, GIF, WebP
 * - Documents: PDF, TXT, MD, JSON, CSV
 * 
 * =============================================================================
 */

import React, { useState, useEffect, useRef } from "react";
import {
  ChatInput as ChatInputFluent,
  ImperativeControlPlugin,
  ImperativeControlPluginRef,
} from "@fluentui-copilot/react-copilot";
import { Button, Tooltip } from "@fluentui/react-components";
import { AttachRegular, DismissCircleRegular, DocumentRegular } from "@fluentui/react-icons";
import { ChatInputProps, IFileAttachment } from "./types";

// Supported file types for attachments
const SUPPORTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"];
const SUPPORTED_DOC_TYPES = ["application/pdf", "text/plain", "text/markdown", "application/json", "text/csv"];
const ALL_SUPPORTED_TYPES = [...SUPPORTED_IMAGE_TYPES, ...SUPPORTED_DOC_TYPES];
const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB max file size

/**
 * Chat Input Component
 * 
 * Renders the message input field at the bottom of the chat interface.
 * Handles text input, file attachments, validation, and submission.
 * 
 * @param {ChatInputProps} props - Component properties
 * @param {function} props.onSubmit - Callback when user submits a message
 * @param {boolean} props.isGenerating - True when AI is generating response (disables input)
 * @param {string} [props.currentUserMessage] - Optional preset message to display
 * 
 * @example
 * <ChatInput
 *   onSubmit={(text, attachments) => console.log("User sent:", text, attachments)}
 *   isGenerating={false}
 * />
 */
export const ChatInput: React.FC<ChatInputProps> = ({
  onSubmit,
  isGenerating,
  currentUserMessage,
}) => {
  // Track the current text in the input field
  const [inputText, setInputText] = useState<string>("");
  
  // Track attached files
  const [attachments, setAttachments] = useState<IFileAttachment[]>([]);
  
  // Reference to the FluentUI control for programmatic access
  const controlRef = useRef<ImperativeControlPluginRef>(null);
  
  // Reference to hidden file input
  const fileInputRef = useRef<HTMLInputElement>(null);

  /**
   * Effect: Sync external message changes to the input field
   * This allows parent components to preset the input text if needed
   */
  useEffect(() => {
    if (currentUserMessage !== undefined) {
      controlRef.current?.setInputText(currentUserMessage ?? "");
    }
  }, [currentUserMessage]);

  /**
   * Convert a File to base64 string
   */
  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const result = reader.result as string;
        // Remove the data URL prefix (e.g., "data:image/jpeg;base64,")
        const base64 = result.split(",")[1];
        resolve(base64);
      };
      reader.onerror = (error) => reject(error);
    });
  };

  /**
   * Handle file selection from input
   */
  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    const newAttachments: IFileAttachment[] = [];

    for (const file of Array.from(files)) {
      // Validate file type
      if (!ALL_SUPPORTED_TYPES.includes(file.type)) {
        console.warn(`Unsupported file type: ${file.type}`);
        continue;
      }

      // Validate file size
      if (file.size > MAX_FILE_SIZE) {
        console.warn(`File too large: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`);
        continue;
      }

      try {
        const base64Data = await fileToBase64(file);
        const attachment: IFileAttachment = {
          name: file.name,
          type: file.type,
          data: base64Data,
          previewUrl: SUPPORTED_IMAGE_TYPES.includes(file.type) 
            ? URL.createObjectURL(file) 
            : undefined,
        };
        newAttachments.push(attachment);
      } catch (error) {
        console.error(`Failed to read file: ${file.name}`, error);
      }
    }

    setAttachments((prev) => [...prev, ...newAttachments]);
    
    // Reset the file input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  /**
   * Remove an attachment by index
   */
  const removeAttachment = (index: number) => {
    setAttachments((prev) => {
      const attachment = prev[index];
      // Revoke object URL to prevent memory leaks
      if (attachment.previewUrl) {
        URL.revokeObjectURL(attachment.previewUrl);
      }
      return prev.filter((_, i) => i !== index);
    });
  };

  /**
   * Handle message submission
   * Validates input is not empty, then calls the onSubmit callback
   * and clears the input field and attachments
   * 
   * @param {string} text - The message text to send
   */
  const onMessageSend = (text: string): void => {
    // Only send if there's actual content or attachments
    if ((text && text.trim() !== "") || attachments.length > 0) {
      onSubmit(text.trim(), attachments.length > 0 ? attachments : undefined);
      setInputText("");
      setAttachments([]);
      controlRef.current?.setInputText("");
    }
  };

  /**
   * Trigger file input click
   */
  const handleAttachClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div style={{ width: "100%" }}>
      {/* Attachment previews */}
      {attachments.length > 0 && (
        <div style={{ 
          display: "flex", 
          flexWrap: "wrap", 
          gap: "8px", 
          padding: "8px 12px",
          backgroundColor: "var(--colorNeutralBackground2)",
          borderRadius: "8px 8px 0 0",
          marginBottom: "-4px"
        }}>
          {attachments.map((attachment, index) => (
            <div 
              key={index} 
              style={{ 
                position: "relative",
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "4px 8px",
                backgroundColor: "var(--colorNeutralBackground1)",
                borderRadius: "6px",
                border: "1px solid var(--colorNeutralStroke1)"
              }}
            >
              {attachment.previewUrl ? (
                <img 
                  src={attachment.previewUrl} 
                  alt={attachment.name}
                  style={{ 
                    width: "40px", 
                    height: "40px", 
                    objectFit: "cover",
                    borderRadius: "4px"
                  }} 
                />
              ) : (
                <DocumentRegular style={{ fontSize: "20px" }} />
              )}
              <span style={{ 
                fontSize: "12px", 
                maxWidth: "100px", 
                overflow: "hidden", 
                textOverflow: "ellipsis",
                whiteSpace: "nowrap"
              }}>
                {attachment.name}
              </span>
              <Button
                appearance="subtle"
                size="small"
                icon={<DismissCircleRegular />}
                onClick={() => removeAttachment(index)}
                style={{ minWidth: "auto", padding: "2px" }}
              />
            </div>
          ))}
        </div>
      )}
      
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept={ALL_SUPPORTED_TYPES.join(",")}
        multiple
        style={{ display: "none" }}
      />
      
      {/* Chat input with attachment button */}
      <div style={{ display: "flex", alignItems: "flex-end", gap: "8px" }}>
        <Tooltip content="Attach images or documents" relationship="label">
          <Button
            appearance="subtle"
            icon={<AttachRegular />}
            onClick={handleAttachClick}
            disabled={isGenerating}
            style={{ marginBottom: "8px" }}
          />
        </Tooltip>
        
        <div style={{ flex: 1 }}>
          <ChatInputFluent
            aria-label="Chat Input"
            charactersRemainingMessage={(_value: number) => ``}
            data-testid="chat-input"
            disableSend={isGenerating}
            history={true}
            isSending={isGenerating}
            onChange={(
              _: React.ChangeEvent<HTMLInputElement>,
              d: { value: string }
            ) => {
              setInputText(d.value);
            }}
            onSubmit={() => {
              onMessageSend(inputText ?? "");
            }}
            placeholderValue={attachments.length > 0 
              ? "Add a message or send attachments..." 
              : "Type your message here..."}
          >
            <ImperativeControlPlugin ref={controlRef} />
          </ChatInputFluent>
        </div>
      </div>
    </div>
  );
};

export default ChatInput;
