# Contributing to Strata

We enforce strict engineering discipline. Before submitting code, ensure you adhere to the following rules based on the `LAW_&_ORDER` specification.

## Branching Strategy

- **`main`**: Always stable. Contains tagged, tested, and fully functional vertical slices.
- **`develop`**: The active integration branch for the current phase.
- **Feature Branches**: Prefix with `feature/` (e.g., `feature/ast-parser`).

All feature branches must merge into `develop` via Pull Request. Direct commits to `main` are forbidden.

## Commit Message Format

Commit messages must document the phase and architectural layer being modified:
`<phase>: <layer>: <short description>`

Examples:

- `phase-1: domain: implement minimal ast node model`
- `phase-1: infrastructure: persist analysis run`
- `phase-1: api: add minimal file upload endpoint`

**Forbidden formats:**

- `fix stuff`
- `updates`
- `WIP`

## Layered Architecture Constraints

We enforce a strict one-directional dependency flow. Read `ARCHITECTURE.md` before writing code to ensure you do not create circular dependencies or cross architectural boundaries incorrectly.

- Code in `domain/` may not import from `infrastructure/` or `api/`.
- `frontend/` may only communicate with `api/` over HTTP. It cannot import application modules.
- `api/` must route logical operations to `application/` services.
- Only operations in `infrastructure/` may access the database or filesystem directly.

## Testing Requirement

Every formula, algorithm, or new domain model must be covered by a unit test.

When in doubt, open an issue to discuss design before writing code.
