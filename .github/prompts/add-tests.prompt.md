---
description: Add unit and integration tests using pytest (backend) or Vitest (frontend)
name: add-tests
agent: agent
tools:
  - changes
  - codebase
  - terminal
---

# Add Tests

Add unit and integration tests to the Foundry Agent Accelerator.

## Testing Stack

| Component | Framework | Runner |
|-----------|-----------|--------|
| Python Backend | pytest | pytest |
| React Frontend | React Testing Library | Vitest |

## Backend Testing (Python)

### Setup

```bash
# Install test dependencies
cd src
pip install pytest pytest-asyncio pytest-cov httpx

# Create tests directory
mkdir -p tests
```

### Test File Structure

```
src/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Shared fixtures
│   ├── test_routes.py        # API endpoint tests
│   ├── test_main.py          # App initialization tests
│   └── test_util.py          # Utility function tests
```

### Example Test File

```python
# tests/test_routes.py
"""
Tests for API routes.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import Mock, patch, AsyncMock

from api.main import create_app


@pytest.fixture
def app():
    """Create test application."""
    with patch.dict('os.environ', {
        'AZURE_EXISTING_AIPROJECT_ENDPOINT': 'test-endpoint',
        'AZURE_AI_CHAT_DEPLOYMENT_NAME': 'test-model',
        'AZURE_AI_AGENT_NAME': 'test-agent',
        'AGENT_CONFIG_SOURCE': 'local'
    }):
        return create_app()


@pytest.fixture
async def client(app):
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_homepage_returns_html(client):
    """Test that the homepage returns HTML."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_chat_endpoint_requires_messages(client):
    """Test that chat endpoint validates input."""
    response = await client.post("/chat", json={})
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_chat_endpoint_streams_response(client):
    """Test that chat endpoint returns streaming response."""
    # Mock the agent response
    with patch('api.routes.get_openai_client') as mock_client:
        mock_stream = AsyncMock()
        mock_stream.__aiter__.return_value = [
            Mock(choices=[Mock(delta=Mock(content="Hello"))])
        ]
        mock_client.return_value.chat.completions.create.return_value = mock_stream
        
        response = await client.post("/chat", json={
            "messages": [{"content": "Hi", "role": "user"}]
        })
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
```

### Shared Fixtures

```python
# tests/conftest.py
"""
Shared test fixtures.
"""

import pytest
from unittest.mock import Mock, patch


@pytest.fixture(autouse=True)
def mock_azure_credentials():
    """Mock Azure credentials for all tests."""
    with patch('azure.identity.DefaultAzureCredential') as mock:
        mock.return_value = Mock()
        yield mock


@pytest.fixture
def sample_chat_request():
    """Sample chat request data."""
    return {
        "messages": [
            {"content": "Hello, how are you?", "role": "user"}
        ]
    }


@pytest.fixture
def sample_agent():
    """Mock Foundry agent."""
    return Mock(
        id="agent_123",
        name="test-agent",
        model="gpt-4o-mini",
        instructions="You are a test agent."
    )
```

### Running Tests

```bash
cd src

# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov-report=html

# Run specific test file
pytest tests/test_routes.py

# Run with verbose output
pytest -v
```

## Frontend Testing (React)

### Setup

```bash
cd src/frontend

# Install test dependencies
pnpm add -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

### Vitest Configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/setupTests.ts'],
  },
});
```

### Setup File

```typescript
// src/setupTests.ts
import '@testing-library/jest-dom';
```

### Example Component Test

```tsx
// src/components/__tests__/AgentIcon.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AgentIcon } from '../agents/AgentIcon';

describe('AgentIcon', () => {
  it('renders with default avatar', () => {
    render(<AgentIcon />);
    const img = screen.getByRole('img');
    expect(img).toBeInTheDocument();
  });

  it('renders with custom logo', () => {
    render(<AgentIcon logo="custom-logo.svg" />);
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', expect.stringContaining('custom-logo.svg'));
  });
});
```

### Testing Streaming Behavior

```tsx
// src/components/__tests__/AgentPreview.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AgentPreview } from '../agents/AgentPreview';

// Mock fetch for streaming
beforeEach(() => {
  global.fetch = vi.fn();
});

describe('AgentPreview', () => {
  const mockAgent = {
    id: 'test-id',
    object: 'chatbot',
    created_at: Date.now(),
    name: 'Test Agent',
    description: 'A test agent',
    model: 'gpt-4o',
    metadata: { logo: 'test.svg' }
  };

  it('renders agent name', () => {
    render(<AgentPreview resourceId="test" agentDetails={mockAgent} />);
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
  });

  it('sends message on form submit', async () => {
    const mockResponse = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode('data: {"type":"message","content":"Hi"}\n\n'));
        controller.close();
      }
    });

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      body: mockResponse
    });

    render(<AgentPreview resourceId="test" agentDetails={mockAgent} />);
    
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.submit(input.closest('form')!);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/chat', expect.any(Object));
    });
  });
});
```

### Running Frontend Tests

```bash
cd src/frontend

# Run tests
pnpm test

# Run with coverage
pnpm test -- --coverage

# Run in watch mode
pnpm test -- --watch
```

## Test Patterns

### Mocking Azure SDK

```python
@pytest.fixture
def mock_project_client():
    """Mock AIProjectClient."""
    with patch('api.main.AIProjectClient') as mock:
        mock_instance = Mock()
        mock_instance.agents.create_version.return_value = Mock(
            id="agent_123",
            name="test-agent"
        )
        mock_instance.get_openai_client.return_value = Mock()
        mock.from_connection_string.return_value = mock_instance
        yield mock_instance
```

### Testing SSE Streams

```python
@pytest.mark.asyncio
async def test_sse_stream_format(client):
    """Verify SSE stream format."""
    response = await client.post("/chat", json={
        "messages": [{"content": "test", "role": "user"}]
    })
    
    content = response.text
    lines = content.split('\n\n')
    
    for line in lines:
        if line:
            assert line.startswith('data: ')
            data = json.loads(line[6:])
            assert 'type' in data
```

## Checklist

- [ ] Test directory created
- [ ] Test dependencies installed
- [ ] Conftest.py with shared fixtures
- [ ] Unit tests for utility functions
- [ ] Integration tests for API endpoints
- [ ] Mock Azure SDK properly
- [ ] Test streaming behavior
- [ ] Frontend component tests (if applicable)
- [ ] Tests pass locally
- [ ] Code coverage > 80%
