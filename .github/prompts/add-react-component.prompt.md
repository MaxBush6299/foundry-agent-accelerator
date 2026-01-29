---
description: Create a new React component with CSS module following project conventions
name: add-react-component
agent: agent
tools:
  - changes
  - codebase
---

# Add New React Component

Create a new React component for the Foundry Agent Accelerator frontend.

## Steps

1. **Create the component file** at `src/frontend/src/components/{folder}/ComponentName.tsx`

2. **Use this template**:

```tsx
/**
 * =============================================================================
 * COMPONENT NAME - Brief Description
 * =============================================================================
 * 
 * WHAT THIS FILE DOES:
 * --------------------
 * 1. First responsibility
 * 2. Second responsibility
 * 
 * HOW TO CUSTOMIZE:
 * -----------------
 * - Customization instructions
 * 
 * =============================================================================
 */

import { ReactNode, useState } from "react";
import { Button, Body1 } from "@fluentui/react-components";

import styles from "./ComponentName.module.css";

/**
 * Props Interface
 */
interface IComponentNameProps {
  title: string;
  onAction?: () => void;
}

/**
 * ComponentName
 * 
 * Description of what this component renders and when to use it.
 * 
 * @param {IComponentNameProps} props - Component props
 * @returns {ReactNode} The rendered component
 */
export function ComponentName({ title, onAction }: IComponentNameProps): ReactNode {
  // -------------------------------------------------------------------------
  // STATE
  // -------------------------------------------------------------------------
  const [isActive, setIsActive] = useState(false);

  // -------------------------------------------------------------------------
  // HANDLERS
  // -------------------------------------------------------------------------
  const handleClick = () => {
    setIsActive(!isActive);
    onAction?.();
  };

  // -------------------------------------------------------------------------
  // RENDER
  // -------------------------------------------------------------------------
  return (
    <div className={styles.container}>
      <Body1>{title}</Body1>
      <Button onClick={handleClick} appearance="primary">
        Click Me
      </Button>
    </div>
  );
}
```

3. **Create the CSS module** at `src/frontend/src/components/{folder}/ComponentName.module.css`:

```css
.container {
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 8px;
}
```

4. **Import and use** in parent component:

```tsx
import { ComponentName } from "./ComponentName";

// In render:
<ComponentName title="My Title" onAction={() => console.log("clicked")} />
```

## Component Location Guide

| Component Type | Location |
|----------------|----------|
| Agent/Chat related | `components/agents/` |
| Shared/Reusable | `components/core/` |
| Theme related | `components/core/theme/` |
| Chat input | `components/agents/chatbot/` |
| Custom hooks | `components/agents/hooks/` |

## Checklist

- [ ] JSDoc header with description
- [ ] Interface prefixed with `I`
- [ ] Props destructured in function signature
- [ ] CSS module created with matching name
- [ ] Fluent UI components used where appropriate
- [ ] TypeScript types for all props and state
