# Contributing to ERTY

This document describes the development workflow, branching strategy, commit conventions, pull request process, CI requirements, and release process for the ERTY project.

## Table of Contents
- [Contributing to ERTY](#contributing-to-erty)
  - [Table of Contents](#table-of-contents)
  - [1. Branching Strategy](#1-branching-strategy)
    - [Protected branches](#protected-branches)
    - [Development flow](#development-flow)
  - [2. Branch Naming](#2-branch-naming)
  - [3. Commit Convention](#3-commit-convention)
    - [Commit Format](#commit-format)
    - [Commit types](#commit-types)
  - [4. Pull Request Workflow](#4-pull-request-workflow)
  - [5. Pull Request Requirements](#5-pull-request-requirements)
  - [6. Code Review](#6-code-review)
  - [7. CI Requirements](#7-ci-requirements)
  - [8. Merge Strategy](#8-merge-strategy)
  - [9. Release Strategy](#9-release-strategy)
    - [Release Process](#release-process)
    - [Versioning](#versioning)
    - [Expected development flow](#expected-development-flow)

---

## 1. Branching Strategy 

ERTY uses a lightweight Git branching strategy designed for a solo developer while maintaining a workflow similar to professional software development teams.

### Protected branches

The project has two main branches:

- `main`: represents production-ready code.
- `development`: integration branch where completed changes are merged before a release.

Changes must never be committed directly to `main` or `development`.

All changes must be introduced through Pull Requests.

### Development flow

Regular changes follow this flow:

```text
feat/fix/refactor/etc
    ↓
Pull Request
    ↓
development
    ↓
```
Releases follow this flow:

```text
development
    ↓
Release PR
    ↓
    main
    ↓
    Tag
    ↓
Releases
```

---

## 2. Branch Naming

Working branches must use one of the following prefixes:

| **Prefix**  |                **Purpose**                |         **Example**         |
| :---------: | :---------------------------------------: | :-------------------------: |
|   `feat/`   | New features or user-facing functionality |   feat/add-url-expiration   |
|   `fix/`    |                 Bug fixes                 |    fix/reject-empty-url     |
| `refactor/` |   Refactoring without behavior changes    |    refactor/url-service     |
|   `docs/`   |        Documentation-only changes         | docs/add-api-documentation  |
|   `test/`   |             Test-only changes             | test/add-url-creation-tests |
|  `chore/`   |   Maintenance and configuration changes   |  chore/update-dependencies  |

Branch names should be:

- concise;
- descriptive;
- written in kebab-case;
- based on the purpose of the change.

Examples:
```text
feat/add-url-expiration
fix/empty-storing-url
refactor/url-service
docs/add-api-documentation
test/add-url-creation-tests
chore/update-dependencies
```

---

## 3. Commit Convention

ERTY follows a commit message convention inspired by [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

### Commit Format

Commit messages should follow this format:

`<type>(<scope>): <short description>`

The `scope` is optional.

Examples

```text
feat(auth): add user authentication
fix(url): prevent duplicate aliases
docs(api): update installation instructions
test(auth): add login tests
chore(ci): update GitHub Actions
```

Commits without a scope are also valid:

```text
docs: update contributing guide
chore: update dependencies
```

### Commit types

- `feat`: adds a new feature.
- `fix`: fixes a bug.
- `docs`: changes documentation.
- `style`: changes formatting or code style without changing functionality.
- `refactor`: restructures existing code without changing its behavior.
- `test`: adds or updates tests.
- `chore`: performs maintenance tasks, such as dependency or configuration updates.

Commit messages should:

- use the imperative mood;
- be concise and descriptive;
- describe what the commit does;
- avoid unnecessary punctuation.

---

## 4. Pull Request Workflow

All changes must go through a Pull Request.

The standard workflow is:

1. Create a working branch from `development`.
2. Implement the changes.
3. Add or update tests when applicable.
4. Run local checks.
5. Push the branch.
6. Open a Pull Request targeting `development`.
7. Wait for CI to complete.
8. Perform a review.
9. Address any issues found during review or CI.
10. Ensure all required checks pass.
11. Squash merge the Pull Request into `development`.
12. Delete the working branch.

Release Pull Requests are an exception to this workflow and target `main`.

---

## 5. Pull Request Requirements

Before merging a Pull Request:

- The PR must have a clear and descriptive title.
- The PR description should explain what changed and why.
- The changes should be focused on a single purpose whenever possible.
- Tests must be added or updated when the change requires them.
- All required CI checks must pass.
- The Pull Request must be reviewed before merging.
- No known blocking issues should remain.
- The PR title should follow the same Conventional Commits format used for commit messages.

Pull Requests should avoid unrelated changes.

## 6. Code Review

Every Pull Request must be reviewed before merging.

Since ERTY is currently a solo-developed project, the author is responsible for performing a thorough self-review before merging their own Pull Requests.

The self-review should verify:

- correctness of the implementation;
- code readability;
- test coverage;
- error handling;
- unintended side effects;
- documentation updates when necessary;
- CI results.

AI-assisted code review may be used as an additional review mechanism.

AI-assisted review does not replace the author's responsibility for the final code.

---

## 7. CI Requirements

The following checks are required before a Pull Request can be merged:

**Required checks**
- linting;
- formatting;
- type checking;
- tests;
- code coverage.

The project will maintain a minimum coverage target of 85%.

Coverage requirements may evolve as the project grows, with emphasis on meaningful test coverage rather than maximizing the percentage alone.

All required CI checks must pass before merging.

The coverage threshold should be enforced automatically by CI.

---

## 8. Merge Strategy

ERTY uses **Squash Merge** for Pull Requests.

Squash merging combines all commits from a Pull Request into a single commit on the target branch.

Example:

```text
Before:

development ── A ── B ── C
                    \
                     D ── E ── F
                            ↑
                       Pull Request


After squash merge:

development ── A ── B ── C ── S
```

Where `S` represents the squashed Pull Request.

This keeps the history of `development` clean and focused on meaningful changes rather than individual development steps.

Each Pull Request should represent a meaningful logical change.

---

## 9. Release Strategy

Releases are created from the `development` branch.

The release process is:

```text
development
     │
     │ Release PR
     ▼
   main
     │
     ▼
   Tag
     │
     ▼
 Release
```

### Release Process

1. Ensure development is stable.
2. Open a Release Pull Request from development to main.
3. Ensure all CI checks pass.
4. Review the changes included in the release.
5. Merge the Release Pull Request into main.
6. Create a version tag on main.
7. Create the corresponding release.

### Versioning

ERTY follows Semantic Versioning:

```text
MAJOR.MINOR.PATCH
```

Example:

```text
v0.1.0
```

Version numbers should be incremented according to the type of change:

- **MAJOR**: incompatible or breaking changes.
- **MINOR**: new backwards-compatible functionality.
- **PATCH**: backwards-compatible bug fixes.

For example:

```text
v0.1.0 → v0.2.0
```

indicates a new backwards-compatible feature, while:

```text
v0.1.0 → v0.1.1
```

indicates a bug fix.

### Expected development flow

The expected development flow is:

```text
              ┌──────────────┐
              │  development │
              └──────┬───────┘
                     │
              Create branch
                     ↓
              feat/fix/etc.
                     ↓
                Pull Request
                     ↓
              CI + Self Review
                     ↓  
              Squash Merge
                     ↓
              development
                     │
                Release PR
                     ↓
                   main
                     │
                  Tag/Release
```

---