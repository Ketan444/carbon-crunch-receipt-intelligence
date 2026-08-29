# AGENTS.md — Carbon Crunch Receipt Intelligence

## Coding Conventions

- Use Python 3.11+ type hints
- Follow PEP 8 style (formatted with ruff/black)
- Use snake_case for function/variable names, PascalCase for classes
- Docstrings for all public functions
- Return type annotations on all functions

## Architecture

The project uses a modular pipeline architecture:

```
Receipt Image → Input Validation → Quality Check → Preprocessing → OCR
→ Normalization → Extraction → Validation → Confidence → Conflict Resolution
→ Structured JSON → Financial Summary → Evaluation
```

Each stage is an independent module under `src/receipt_ai/`.

## Testing Rules

- Write unit tests for every module in `tests/`
- Use pytest for test execution
- Tests must be independent (no shared state)
- Use fixtures for reusable test data
- Integration tests use actual receipt images from `data/raw/`
- Never hardcode receipt-specific outputs in tests
- Regression tests must be added after bug fixes

## Windows Path Rules

- Use `pathlib` for all path operations
- Never hardcode `/home` or `/usr` paths
- Use `os.path.expanduser(`~$)` for user directory resolution
- All project-relative paths are relative to the project root
- Use raw strings or double backslashes for Windows paths
- Example: `Path("data/raw")` works cross-platform

## Token-Efficient Behavior

- Do not repeatedly explain architecture or roadmap
- Inspect existing code before making changes
- Prefer concise status updates over narrative explanations
- Read AGENTS.md and PROJECT_CONTEXT.md before starting work
- Repository is the source of truth — do not invent facts

## Debugging Rules

1. Reproduce the bug before fixing
2. Identify root cause — never manually patch individual receipt outputs
3. Fix the general pipeline, not individual receipts
4. Add regression test after fix
5. Re-run to verify

## No Hardcoded Receipt-Specific Hacks

- Never write: `if receipt_id == "receipt_003": total = "267.75"`
- All receipt-specific logic must be generalizable
- Configuration (not code) drives behavior differences
- Extraction patterns must work across receipt layouts

## Documentation Requirements

- Update PROJECT_CONTEXT.md after meaningful milestones
- Keep README.md current with new features
- Document important design decisions in PROJECT_CONTEXT.md
- Maintain CHANGELOG-style updates for significant changes

## Definition of Done

- All applicable checklist items from PROJECT_CONTEXT.md satisfied
- Unit tests pass
- CLI works on Windows
- Full dataset processed without crashes
- Evaluation report generated
- JSON outputs valid
- Code review completed
- No secrets committed