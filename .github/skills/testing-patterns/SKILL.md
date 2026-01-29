---
name: testing-patterns
description: Skill for testing the Foundry Agent Accelerator. Use when writing pytest tests for the Python backend, Vitest tests for the React frontend, mocking Azure services, or testing SSE streaming.
---

# Testing Patterns Skill

This skill provides patterns and guidance for testing the Foundry Agent Accelerator.

## Testing Stack

| Component | Framework | Runner |
|-----------|-----------|--------|
| Python Backend | pytest | pytest |
| React Frontend | React Testing Library | Vitest |

## Backend Testing (pytest)

### Setup

```bash
cd src
pip install pytest pytest-asyncio pytest-cov httpx
mkdir -p tests
```

### Test File Structure

```
src/tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── test_routes.py        # API endpoint tests
├── test_main.py          # App initialization tests
└── test_util.py          # Utility function tests
```

### Shared Fixtures (conftest.py)

```python
# tests/conftest.py
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

### API Endpoint Tests

```python
# tests/test_routes.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

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
async def test_chat_endpoint_validates_input(client):
    """Test that chat endpoint validates input."""
    response = await client.post("/chat", json={})
    assert response.status_code == 422
```

### Running Backend Tests

```bash
cd src

# Run all tests
pytest

# With coverage
pytest --cov=api --cov-report=html

# Specific file
pytest tests/test_routes.py -v
```

## Frontend Testing (Vitest)

### Setup

```bash
cd src/frontend
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

### Component Tests

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
});
```

### Testing SSE Streams

```tsx
// Mock fetch for streaming
import { vi, beforeEach } from 'vitest';

beforeEach(() => {
  global.fetch = vi.fn();
});

it('processes streaming response', async () => {
  const mockResponse = new ReadableStream({
    start(controller) {
      controller.enqueue(
        new TextEncoder().encode('data: {"type":"message","content":"Hi"}\n\n')
      );
      controller.close();
    }
  });

  (global.fetch as any).mockResolvedValueOnce({
    ok: true,
    body: mockResponse
  });

  // Render and interact with component...
});
```

### Running Frontend Tests

```bash
cd src/frontend

# Run tests
pnpm test

# With coverage
pnpm test -- --coverage

# Watch mode
pnpm test -- --watch
```

## Mocking Patterns

### Mock Azure SDK

```python
@pytest.fixture
def mock_openai_stream():
    """Mock streaming OpenAI response."""
    async def mock_stream():
        yield Mock(choices=[Mock(delta=Mock(content="Hello"))])
        yield Mock(choices=[Mock(delta=Mock(content=" world"))])
    
    return mock_stream()
```

### Mock Environment Variables

```python
@pytest.fixture
def mock_env():
    with patch.dict('os.environ', {
        'AZURE_EXISTING_AIPROJECT_ENDPOINT': 'https://test.azure.com',
        'AZURE_AI_CHAT_DEPLOYMENT_NAME': 'gpt-4o-test',
        'AZURE_AI_AGENT_NAME': 'test-agent'
    }):
        yield
```

## Test Coverage Goals

- **Unit tests**: Cover utility functions and helpers
- **Integration tests**: Cover API endpoints end-to-end
- **Component tests**: Cover React component rendering
- **SSE tests**: Verify streaming behavior

Target: 80%+ code coverage
