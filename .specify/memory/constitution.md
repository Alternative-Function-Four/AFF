# Project Constitution

## Core Values

1. **Contract First**: API behavior must conform to documented contracts before optimization or framework preferences.
2. **Policy Safety by Default**: Source approval gates, notification caps, and quiet-hour rules are mandatory defaults.
3. **Explainable Recommendations**: Feed ranking must include explicit reasons and provenance.
4. **Pragmatic Delivery**: Prefer simple, testable implementations that can be evolved over speculative architecture.

## Technical Principles

### Architecture
- Implement clear API-domain boundaries even when using an in-memory prototype store.
- Keep endpoint handlers thin; isolate ranking and policy rules into pure helper functions.

### Code Quality
- All contract endpoints must have deterministic request/response models.
- Error responses must use a consistent envelope shape.
- Core user flows require automated tests.

### Performance
- Keep feed ranking and filtering O(n) over in-memory candidates for prototype scale.
- Avoid blocking I/O in request paths.

## Decision Framework

When deciding between alternatives:
1. Does it preserve API contract fidelity?
2. Does it enforce policy constraints safely?
3. Is it testable with isolated unit/integration tests?
4. Is it simple enough for hackathon iteration speed?
