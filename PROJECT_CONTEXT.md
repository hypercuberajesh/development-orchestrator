# Development Orchestrator Project

This repository is the source of truth for the software development project.

## Rules

- Reuse existing code whenever possible.
- Do not create duplicate functionality.
- Existing and AI-generated code are treated as one unified codebase.
- The agent must never execute Python, shell commands, notebooks, SQL, or validators.
- The agent must never access production or customer data.
- Use synthetic data for examples and testing.
- The user must approve the implementation plan before code is written.
- The user runs the generated code independently.
- The agent must never claim that code works unless the user confirms it.
- Validators are created only after the user confirms that the implementation works.
- Repository indexes are updated only after the validator passes.
