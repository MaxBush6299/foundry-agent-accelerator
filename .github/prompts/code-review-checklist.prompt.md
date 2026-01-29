---
description: Review code changes using the project's code review checklist
name: code-review
agent: agent
tools:
  - codebase
  - changes
---

# Code Review Checklist

Use this checklist when reviewing code changes to the Foundry Agent Accelerator.

## General Checks

### Code Quality
- [ ] Code follows project naming conventions
- [ ] No commented-out code left behind
- [ ] No debug print statements
- [ ] No hardcoded secrets or credentials
- [ ] Complex logic has explanatory comments

### Documentation
- [ ] Python files have module docstrings (header block)
- [ ] React components have JSDoc headers
- [ ] Functions have docstrings with params/returns
- [ ] README updated if public API changed
- [ ] Environment variables documented if added

### Type Safety
- [ ] Python functions have type hints
- [ ] TypeScript interfaces prefixed with `I`
- [ ] No use of `any` type (TypeScript) without justification
- [ ] Pydantic models used for request/response bodies

## Python Backend Checks

### Style
- [ ] Section headers used (# === SECTION ===)
- [ ] Imports organized (stdlib, third-party, local)
- [ ] Logger used instead of print()
- [ ] Environment variables loaded from .env

### Security
- [ ] User input validated via Pydantic
- [ ] No SQL injection vulnerabilities
- [ ] Secrets not logged
- [ ] Authentication applied to protected routes

### Error Handling
- [ ] Try/except blocks for external calls
- [ ] Proper HTTP status codes returned
- [ ] Errors logged before re-raising
- [ ] User-friendly error messages

### Azure Integration
- [ ] DefaultAzureCredential used
- [ ] Connection strings from environment variables
- [ ] Resources cleaned up properly
- [ ] Retry logic for transient failures

## React Frontend Checks

### Style
- [ ] JSDoc header on component files
- [ ] Props interface defined
- [ ] CSS modules used (not inline styles)
- [ ] Fluent UI components used where appropriate

### State Management
- [ ] useState/useCallback/useMemo used appropriately
- [ ] No unnecessary re-renders
- [ ] Loading states handled
- [ ] Error states handled

### Accessibility
- [ ] Semantic HTML elements used
- [ ] ARIA attributes where needed
- [ ] Keyboard navigation works
- [ ] Focus management correct

### Performance
- [ ] Large lists virtualized
- [ ] Images optimized
- [ ] No memory leaks in useEffect
- [ ] Cleanup functions in useEffect

## Agent Configuration Checks

### system.txt Changes
- [ ] Personality clearly defined
- [ ] Boundaries/restrictions specified
- [ ] No conflicting instructions
- [ ] Tested with edge cases

### agent.yaml Changes
- [ ] Only necessary tools enabled
- [ ] Connection names verified
- [ ] Tool dependencies documented
- [ ] Changes tested locally

## Testing Checks

- [ ] New functionality has tests
- [ ] Edge cases covered
- [ ] Mocks used for external services
- [ ] Tests pass locally
- [ ] No flaky tests introduced

## Deployment Checks

- [ ] Environment variables documented
- [ ] No breaking changes to API
- [ ] Backward compatibility maintained
- [ ] Migration steps documented if needed

## Security Review

### Sensitive Data
- [ ] No credentials in code
- [ ] No PII logged
- [ ] .env.template updated (not .env)
- [ ] Secrets in secure storage

### Authentication
- [ ] Protected routes require auth
- [ ] Auth bypass not possible
- [ ] Session/token handling secure

### Input Validation
- [ ] All user input validated
- [ ] File uploads restricted
- [ ] Request size limits applied

## Final Checks

- [ ] PR description explains the change
- [ ] Related issues linked
- [ ] No merge conflicts
- [ ] CI checks pass
- [ ] Ready for merge

## Reviewer Notes Template

```markdown
## Review Summary

**Overall:** ✅ Approved / 🔄 Changes Requested / ❌ Not Ready

### What I Reviewed
- [ ] Code changes
- [ ] Tests
- [ ] Documentation

### Strengths
- 

### Issues Found
- 

### Suggestions (Optional)
- 

### Questions
- 
```
