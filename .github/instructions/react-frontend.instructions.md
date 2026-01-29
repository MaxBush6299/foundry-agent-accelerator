---
description: Guidelines for modifying or creating React/TypeScript frontend components
globs:
  - "src/frontend/**/*.tsx"
  - "src/frontend/**/*.ts"
  - "src/frontend/**/*.css"
---

# React Frontend Development Guidelines

## File Structure

All frontend code lives in `src/frontend/`. Follow this structure:

```
src/frontend/
├── src/
│   ├── main.tsx              # App entry point
│   ├── components/
│   │   ├── App.tsx           # Root component
│   │   ├── agents/           # Chat-related components
│   │   │   ├── AgentPreview.tsx
│   │   │   ├── AgentPreview.module.css
│   │   │   ├── chatbot/      # Chat input components
│   │   │   └── hooks/        # Custom React hooks
│   │   └── core/             # Shared/reusable components
│   │       ├── Markdown.tsx
│   │       ├── SettingsPanel.tsx
│   │       ├── MenuButton/
│   │       └── theme/        # Theme provider and utilities
│   └── types/
│       └── chat.ts           # TypeScript interfaces
├── package.json
└── vite.config.ts
```

## Component Documentation Format

Every component file MUST start with this JSDoc block:

```tsx
/**
 * =============================================================================
 * COMPONENT NAME - Brief Description
 * =============================================================================
 * 
 * This component handles [primary responsibility].
 * 
 * WHAT THIS FILE DOES:
 * --------------------
 * 1. First key responsibility
 * 2. Second key responsibility
 * 3. Additional responsibilities...
 * 
 * HOW TO CUSTOMIZE:
 * -----------------
 * - Customization point 1: Instructions
 * - Customization point 2: Instructions
 * 
 * PROPS:
 * ------
 * @param {IProps} props - Component props
 * @param {string} props.propName - Description
 * 
 * =============================================================================
 */
```

## Interface Naming Convention

Prefix all interface names with `I`:

```tsx
interface IAgent {
  id: string;
  name: string;
  description?: string | null;
  model: string;
  metadata?: Record<string, any>;
}

interface IMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
}

interface IComponentProps {
  resourceId: string;
  agentDetails: IAgent;
}
```

## Component Definition Pattern

Use explicit return types and destructure props:

```tsx
import { ReactNode, useState, useMemo } from "react";

interface IMyComponentProps {
  title: string;
  onAction: () => void;
  children?: ReactNode;
}

export function MyComponent({ title, onAction, children }: IMyComponentProps): ReactNode {
  // State declarations
  const [isOpen, setIsOpen] = useState(false);
  
  // Memoized values
  const computedValue = useMemo(() => {
    return expensiveCalculation(title);
  }, [title]);
  
  // Event handlers
  const handleClick = () => {
    onAction();
    setIsOpen(true);
  };
  
  return (
    <div>
      <h1>{title}</h1>
      {children}
    </div>
  );
}
```

## CSS Modules

Use CSS modules for component styling:

### Naming Convention
- File: `ComponentName.module.css`
- Import: `import styles from "./ComponentName.module.css"`

### Example CSS Module

```css
/* MyComponent.module.css */

.container {
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.header {
  font-size: 1.5rem;
  font-weight: 600;
}

.content {
  flex: 1;
  overflow: auto;
}

/* Use kebab-case for multi-word class names */
.action-button {
  margin-top: 8px;
}
```

### Usage in Component

```tsx
import styles from "./MyComponent.module.css";

export function MyComponent(): ReactNode {
  return (
    <div className={styles.container}>
      <h1 className={styles.header}>Title</h1>
      <div className={styles.content}>Content</div>
      <button className={styles.actionButton}>Action</button>
    </div>
  );
}
```

## Fluent UI Components

Use Fluent UI for consistent Microsoft-style UI:

```tsx
import {
  Body1,
  Button,
  Caption1,
  Title2,
  Spinner,
  Input,
  Textarea,
} from "@fluentui/react-components";

import {
  ChatRegular,
  SendRegular,
  SettingsRegular,
  DismissRegular,
} from "@fluentui/react-icons";

export function ChatHeader(): ReactNode {
  return (
    <div className={styles.header}>
      <ChatRegular />
      <Title2>Agent Chat</Title2>
      <Button icon={<SettingsRegular />} appearance="subtle" />
    </div>
  );
}
```

## Fluent UI Copilot Components

For chat interfaces, use the Copilot-specific components:

```tsx
import { CopilotProvider } from "@fluentui-copilot/react-provider";
import { CopilotChat, UserMessage, AssistantMessage } from "@fluentui-copilot/react-copilot-chat";

export function ChatContainer(): ReactNode {
  return (
    <CopilotProvider>
      <CopilotChat>
        {messages.map((msg) => (
          msg.role === 'user' 
            ? <UserMessage key={msg.id}>{msg.content}</UserMessage>
            : <AssistantMessage key={msg.id}>{msg.content}</AssistantMessage>
        ))}
      </CopilotChat>
    </CopilotProvider>
  );
}
```

## State Management Pattern

Use React hooks for state management:

```tsx
import { useState, useCallback, useEffect } from "react";

export function ChatComponent(): ReactNode {
  // -------------------------------------------------------------------------
  // STATE
  // -------------------------------------------------------------------------
  const [messages, setMessages] = useState<IMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // -------------------------------------------------------------------------
  // CALLBACKS
  // -------------------------------------------------------------------------
  const sendMessage = useCallback(async (content: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: [...messages, { content, role: "user" }] })
      });
      
      // Handle streaming response...
    } catch (err) {
      setError("Failed to send message");
    } finally {
      setIsLoading(false);
    }
  }, [messages]);
  
  // -------------------------------------------------------------------------
  // EFFECTS
  // -------------------------------------------------------------------------
  useEffect(() => {
    // Scroll to bottom when messages change
    scrollContainerRef.current?.scrollTo({ top: 99999, behavior: "smooth" });
  }, [messages]);
  
  return (/* JSX */);
}
```

## SSE (Server-Sent Events) Pattern

Handle streaming responses from the backend:

```tsx
const processStream = async (response: Response) => {
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  
  if (!reader) return;
  
  let buffer = "";
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";
    
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = JSON.parse(line.slice(6));
        
        switch (data.type) {
          case "message":
            // Append to current message
            appendToMessage(data.content);
            break;
          case "completed_message":
            // Final message received
            setFinalMessage(data.content);
            break;
          case "stream_end":
            // Stream completed
            setIsLoading(false);
            break;
        }
      }
    }
  }
};
```

## Custom Hooks

Place reusable logic in custom hooks under `hooks/`:

```tsx
// hooks/useFormatTimestamp.ts

import { useMemo } from "react";

export function useFormatTimestamp(timestamp: number): string {
  return useMemo(() => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }, [timestamp]);
}

// Usage
const formattedTime = useFormatTimestamp(message.timestamp);
```

## Theme Support

Use the ThemeProvider for consistent theming:

```tsx
import { ThemeProvider } from "./core/theme/ThemeProvider";

// In App.tsx
return (
  <ThemeProvider>
    <div className="app-container">
      <YourComponent />
    </div>
  </ThemeProvider>
);
```

## Common Imports

```tsx
// React core
import { ReactNode, useState, useCallback, useMemo, useEffect, useRef } from "react";

// Fluent UI
import { Body1, Button, Input, Spinner, Title2 } from "@fluentui/react-components";
import { SendRegular, ChatRegular, SettingsRegular } from "@fluentui/react-icons";

// Fluent Copilot (for chat components)
import { CopilotProvider } from "@fluentui-copilot/react-provider";
import { CopilotChat } from "@fluentui-copilot/react-copilot-chat";

// Local
import styles from "./ComponentName.module.css";
import { IMessage, IChatItem } from "../types/chat";
```

## File Attachment Handling

Handle file attachments in chat:

```tsx
interface IFileAttachment {
  name: string;
  type: string;  // MIME type
  data: string;  // Base64-encoded
}

const handleFileSelect = async (file: File): Promise<IFileAttachment> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = (reader.result as string).split(",")[1];
      resolve({
        name: file.name,
        type: file.type,
        data: base64
      });
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
};
```

## Markdown Rendering

Use react-markdown for rendering agent responses:

```tsx
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

export function MessageContent({ content }: { content: string }): ReactNode {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[rehypeKatex]}
    >
      {content}
    </ReactMarkdown>
  );
}
```
