---
name: task-engineer
description: Use quando criar, alterar ou otimizar tasks do VS Code/Cursor (startup, build, test, deploy).
---
CTX-ID: task-engineer@2

# Task Engineer

## Composição Superpowers

Task authoring specifics; verification follows the official process.

**REQUIRED SUB-SKILL:** Use `superpowers:verification-before-completion` — a task is done only after it was executed from the user's normal path and the real output was read.

Create tasks that are executable, reproducible and verified.

The goal is not to produce a syntactically valid task.
The goal is to produce a task that actually works from the user's normal execution path.

## 1. Discover before editing

Before changing anything:

- Identify the requested behavior and success criteria.
- Inspect the existing task definitions.
- Inspect scripts or commands called by the task.
- Find an existing working implementation or documented manual command when available.
- Determine:
  - operating environment;
  - shell;
  - working directory;
  - executable path;
  - required environment variables;
  - prerequisites;
  - ports;
  - files/directories;
  - containers/services involved;
  - whether the task is foreground or background;
  - whether other tasks depend on it.

Do not invent environment assumptions when they can be verified from the repository.

## 2. Establish the baseline

When safe:

Execute or validate the underlying command independently before changing the task.

Distinguish:

UNDERLYING_COMMAND_FAILURE
from
TASK_CONFIGURATION_FAILURE.

Do not modify task configuration to hide an underlying application/infrastructure problem.

## 3. Design the task

Prefer the smallest reliable configuration.

For VS Code/Cursor tasks:

- explicitly configure cwd when ambiguity exists;
- prefer args instead of composing complex shell strings;
- consider `process` instead of `shell` when shell behavior is unnecessary;
- use explicit workspace-folder references in multi-root environments;
- use `dependsOn` for real dependencies;
- use `dependsOrder: sequence` when ordering matters;
- do not assume a background dependency is ready merely because its process started;
- configure background readiness when necessary;
- avoid accidental duplicate instances;
- expose useful failure output.

Do not duplicate logic already implemented reliably in a script.
Prefer the task as a thin entry point over existing executable automation.

## 4. Validate statically

After editing:

- parse JSON/YAML as applicable;
- check referenced task labels;
- check referenced scripts/files;
- check cwd;
- check executables;
- check environment-variable references;
- check dependency graph;
- check task recursion/cycles;
- inspect paths for Windows/Linux/WSL confusion.

Static validation is necessary but NEVER sufficient.

## 5. Execute

Perform runtime validation when safe.

Test the same behavior the user will invoke.

Verify:

TASK_START
→ DEPENDENCIES
→ READINESS
→ EXPECTED_OPERATION
→ EXPECTED_FINAL_STATE.

Capture concrete evidence:
- command/task executed;
- exit status where applicable;
- relevant output;
- health/readiness evidence;
- failure details.

Starting a process is not proof of success.

## 6. Validate lifecycle

For persistent/background infrastructure check:

- process/container actually becomes ready;
- dependent task does not race readiness;
- duplicate execution does not create unexpected instances;
- ports are correct;
- termination/cleanup works when applicable;
- no obviously orphaned process is left behind.

For one-shot tasks:
- verify expected output/state;
- verify proper exit code.

## 7. Repeatability

Where safe, execute again.

The second execution must not fail merely because the first execution left unmanaged state.

If the task is intentionally non-idempotent, document that explicitly.

## 8. Independent verification

After implementation, delegate verification to `task-verifier`.

Provide the verifier:
- requested behavior;
- changed files;
- task name;
- expected success criteria;
- known prerequisites.

Do not tell the verifier that the implementation is correct.

## Definition of Done

A task is VERIFIED only when:

- configuration is valid;
- referenced resources exist;
- execution environment is correct;
- dependencies are correct;
- runtime execution was tested;
- expected result was observed;
- independent verification found no blocking problem.

Otherwise use:

UNVERIFIED
or
FAILED.

Never convert missing evidence into an assumption.

## Final report

Return:

STATUS: VERIFIED | UNVERIFIED | FAILED

TASK:
<name>

VALIDATED:
<short evidence>

EXECUTION:
<what actually ran>

RESULT:
<observed result>

VERIFIER:
<PASS or findings>

REMAINING RISKS:
<only concrete unresolved risks>
