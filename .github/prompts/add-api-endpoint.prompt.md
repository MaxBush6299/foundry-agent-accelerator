---
description: Add a new API endpoint to the FastAPI backend following project conventions
name: add-api-endpoint
agent: agent
tools:
  - changes
  - codebase
---

# Add New API Endpoint

Add a new API endpoint to the Foundry Agent Accelerator backend.

## Steps

1. Open `src/api/routes.py`

2. Add the new route function following this pattern:

```python
@router.post("/your-endpoint")
async def your_endpoint_name(
    request: Request,
    your_request: YourRequestModel,
    auth: None = Depends(authenticate) if basic_auth_enabled else None
):
    """
    Brief description of what this endpoint does.
    
    This endpoint:
    1. First action
    2. Second action
    3. Returns result
    
    :param request: The FastAPI request object
    :param your_request: The request body model
    :returns: Response description
    """
    logger.info("Processing your endpoint request")
    
    try:
        # Your logic here
        result = await process_request(your_request)
        return JSONResponse(content={"result": result})
    except Exception as e:
        logger.error(f"Error in your_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

3. If you need a new request model, add it to `src/api/util.py`:

```python
class YourRequestModel(pydantic.BaseModel):
    """Description of the request model."""
    field1: str
    field2: Optional[int] = None
```

4. Import the model in routes.py:

```python
from .util import get_logger, ChatRequest, YourRequestModel
```

## Checklist

- [ ] Function has descriptive docstring
- [ ] Type hints on all parameters
- [ ] Proper error handling with try/except
- [ ] Logging for debugging
- [ ] Authentication dependency if route should be protected
- [ ] Response model defined if returning JSON
