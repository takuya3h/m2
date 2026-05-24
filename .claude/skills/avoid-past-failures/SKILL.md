---
name: avoid-past-failures
description: Read the project's incident log before modifying code with documented past failures. Triggers on auth, credentials, OAuth, tokens, deployments, CI/CD, database migrations, schema changes, third-party API integrations, library upgrades, or any task in a subsystem where a previous attempt broke and was rolled back. Source of truth in priority order - .claude/incidents.md, INCIDENTS.md at repo root, docs/incidents.md. Skipping this leads to re-implementing approaches that already failed and were reverted.
---

# Avoid Past Failures

## Why this skill exists

A new session starts with no memory of past mistakes. Without a written log,
the same broken approach gets attempted again, sometimes within weeks of a
previous failure. This skill makes the institutional failure log discoverable
and enforceable.

## When to invoke

Read the incident log before any of the following:

- Modifying authentication, tokens, OAuth, credentials, or secrets handling
- Changing CI/CD configuration, deployment scripts, or release tooling
- Touching database migrations or schema
- Changing third-party API integrations or SDK versions
- Replacing a library, upgrading a major version, or removing a dependency
- Refactoring code with hints of past trouble (revert commits in `git log`,
  `// do not change`, `// legacy` comments)
- Any task in a subsystem whose name appears in the incident log titles

When uncertain, read the log anyway. It is short and cheap.

## Where the log lives

Look in this order and use the first match:

1. `.claude/incidents.md`
2. `INCIDENTS.md` at repo root
3. `docs/incidents.md`

If none exist and you are about to make a non-trivial change, ask the user
whether one should be created.

## Incident log format

Each entry follows this template:

```
### Incident N - Short title (YYYY-MM-DD)

- What was tried:
- What broke:
- Root cause:
- Fix / mitigation:
- Prohibited going forward:
```

The "Prohibited going forward" line is the most important. It is the rule a
future session must follow.

## How to apply

1. **Read every entry**, not just the ones that look related. Cross-cutting
   incidents often apply outside their original subsystem.
2. **Cross-reference your planned change against every "Prohibited going
   forward" line**. If a planned action matches a prohibition, stop and ask
   the user before proceeding.
3. **If a prohibition is ambiguous for your case**, surface the incident and
   ask for explicit confirmation rather than guessing.
4. **After resolving a new failure during the session**, append a new entry
   in the same format. The log is self-maintaining only if every session
   that hits a new failure writes it down.

## Reusing this skill in another project

The skill body is project-agnostic. To adopt it elsewhere:

1. Copy `.claude/skills/avoid-past-failures/` into the new project.
2. Create `.claude/incidents.md` and add the first entry the first time a
   recurring or expensive failure is resolved.

No edits to this file are needed per project.
