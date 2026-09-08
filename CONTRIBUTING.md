# Contributing to MultiPost English

Thanks for your interest in contributing! Here's how to get started.

## Quick Start

1. **Fork** this repository
2. **Clone** your fork locally
3. **Install** dependencies:
   ```bash
   pnpm install
   ```
4. **Start** the dev server:
   ```bash
   pnpm dev
   ```
5. Make your changes, commit, and push

## Development

This project uses **Electron + Vite + React + TypeScript**.

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start development environment |
| `pnpm build:mac` | Package for macOS |
| `pnpm build:win` | Package for Windows |
| `pnpm lint` | Run ESLint |

## Guidelines

### Code Style

- Always use `interface` over `type` for object types
- Avoid `enum` — use const objects or maps
- Function components only, early returns for error handling
- Use Zod for form validation
- Comments explain **why**, not **what**

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new platform support
fix: resolve login detection issue
docs: update installation guide
chore: update dependencies
refactor: simplify IPC handlers
```

### Pull Requests

- Keep PRs focused on a single change
- Describe what changed and why
- Reference any related issues
- Ensure `pnpm lint` passes before submitting

## Translation Help

If you'd like to help translate the UI into additional languages, the main strings are in:

- `src/main/platforms/` — Platform-specific publishing scripts
- `src/renderer/` — UI components and labels

## Questions?

Open a [Discussion](../../discussions) or check existing [Issues](../../issues).
