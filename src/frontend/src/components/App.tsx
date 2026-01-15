/**
 * =============================================================================
 * FOUNDRY AGENT ACCELERATOR - Main Application Component
 * =============================================================================
 * 
 * This is the root component of the React chat interface. It sets up the
 * application structure and provides the theme context for styling.
 * 
 * WHAT THIS FILE DOES:
 * --------------------
 * 1. Defines the agent's display information (name, description, logo)
 * 2. Wraps the application in a ThemeProvider for consistent styling
 * 3. Renders the AgentPreview component which contains the chat interface
 * 
 * HOW TO CUSTOMIZE:
 * -----------------
 * - Change agentDetails.name to update the displayed agent name
 * - Change agentDetails.description to update the agent's description
 * - Change agentDetails.metadata.logo to use a different avatar image
 *   (place your image in src/api/static/assets/template-images/)
 * 
 * NOTE: The actual agent behavior is controlled by the system prompt in
 *       src/api/prompts/system.txt, not this file. This file only controls
 *       how the agent LOOKS in the UI.
 * 
 * =============================================================================
 */

import { AgentPreview } from "./agents/AgentPreview";
import { ThemeProvider } from "./core/theme/ThemeProvider";

/**
 * Main Application Component
 * 
 * The root component that renders the entire chat interface.
 * Uses FluentUI theming via ThemeProvider for consistent Microsoft-style UI.
 * 
 * @returns The complete chat application UI
 */
const App: React.FC = () => {
  /**
   * Agent Display Configuration
   * 
   * This object controls how the agent appears in the UI.
   * Customize these values to match your agent's branding.
   * 
   * @property {string} id - Unique identifier for the agent
   * @property {string} name - Display name shown in the chat header
   * @property {string} description - Short description of the agent's purpose
   * @property {string} model - Model identifier (for display purposes only)
   * @property {object} metadata - Additional configuration like the avatar logo
   */
  const agentDetails ={
      id: "chatbot",
      object: "chatbot",
      created_at: Date.now(),
      name: "Chatbot",  // <-- CUSTOMIZE: Change this to your agent's name
      description: "This is a sample chatbot.",  // <-- CUSTOMIZE: Describe your agent
      model: "default",
      metadata: {
        logo: "Avatar_Default.svg",  // <-- CUSTOMIZE: Use your own avatar image
      },
  };

  return (
    // ThemeProvider: Provides Fluent UI theming (light/dark mode support)
    <ThemeProvider>
      <div className="app-container">
        {/* AgentPreview: The main chat interface component */}
        <AgentPreview
          resourceId="sample-resource-id"
          agentDetails={agentDetails}
        />
      </div>
    </ThemeProvider>
  );
};

export default App;
