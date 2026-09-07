# gemini-llm — A Minimal Agent Loop with the Gemini Interactions API

This repository contains the demonstration code from a live Google Meet session on the
**anatomy of an agent loop**: how a large language model, a set of tools, and a simple
control loop compose into an autonomous agent. The recording and supporting material for
the session are available [here](https://drive.google.com/drive/folders/1t31booWoh8K0hk4SsBHnBPcl930kLylH?usp=drive_link).

The implementation is deliberately small (~200 lines) so that every concept — turns,
trajectories, tool dispatch, context reconstruction — is visible in plain code rather
than hidden behind a framework.

## Conceptual model

### Steps, turns, and trajectories

Let a **step** be an atomic unit of the interaction: a user message (`um`), an assistant
message (`am`), a thought (`th`), a tool call (`tc`), or a tool result (`tr`).

A **turn** (or *trajectory segment*) is the complete sequence of steps triggered by a
single user message, terminating when the model produces a final assistant message:

```
turn := [um] · [th? (tc, tr)]* · [th? am]
```

Degenerate cases follow naturally:

- `um · am` — a direct answer, no tools required;
- `um · tc · tr · am` — one round of tool use;
- `um · th · tc · tr · tc · tr · … · am` — an arbitrarily deep tool-use chain,
  possibly interleaved with thoughts.

The **history** (context) of the conversation is the ordered concatenation of completed
turns `t₀, t₁, …, tₙ`. On every model invocation, the engine flattens
`history + current_turn` into a single step list and submits it as the model input —
the model is stateless; the trajectory *is* the state. The engine stores each step in
the exact order the model emitted it, so the replayed context is a faithful record of
the trajectory.

Because the context window is finite, the engine applies a **sliding window** over
completed turns (the last *k*, default 32): the turn is the natural unit of context
eviction — one summarises or evicts whole turns, never splits one.

A failed tool execution is returned to the model as an error-bearing tool result rather
than raised as an exception: **an error is an observation**, part of the trajectory,
which the model can react to and self-correct — the mechanism Reflexion builds upon.

### The loop

The control loop in `engine.py` implements a two-state machine:

1. **Await user input** — read a message, open a new turn.
2. **Generate** — call the model. For each emitted step:
   - *thought* → display the thinking summary, append it (with its signature) to the turn;
   - *model_output* → display the answer, append it to the turn;
   - *function_call* → accumulate it for execution.
3. If any function calls were emitted, execute them **concurrently**
   (`asyncio.gather`), append calls and results to the turn, and return to step 2
   without consulting the user. Otherwise, the turn is complete: commit it to the
   history and return to step 1.

This "generate → act → observe → generate" cycle, iterated until the model chooses to
answer, is the essential structure shared by every production agent system.

### Verbal reinforcement learning and self-reflection

The session also discussed **Reflexion** (Shinn et al., 2023,
[arXiv:2303.11366](https://arxiv.org/abs/2303.11366)), which frames trajectories as the
substrate of *verbal reinforcement learning*: instead of updating model weights, an
agent converts the feedback signal from a failed trajectory into a natural-language
self-reflection, stores it in memory, and conditions subsequent attempts on it. The
trajectory formalism above is precisely what makes this possible — a turn is an episode,
tool results are observations/rewards, and the context window serves as the episodic
memory into which reflections are written.

## Tools

The agent (persona **"Predator"**, defined in `prompt.py`) is equipped with three tools,
declared in `tool_schemas.py`:

| Tool | Implementation |
|---|---|
| `web_search` | A *nested* Gemini interaction using the built-in `google_search` server tool — an agent delegating to a sub-agent. |
| `google_maps` | Likewise, delegating to the built-in `google_maps` server tool. |
| `bash` | Local shell execution via `asyncio.create_subprocess_exec`, with a bounded timeout, returning `{exit_code, stdout, stderr}` as JSON. |

Each tool lives in its own sub-package under `tools/` as a callable class deriving from
`BaseTool`, which pairs an implementation (`__call__`) with its declared JSON schema
(`name`, `schema`). A `ToolsExecutor` holds the registry — the tool namespace is
exactly the instances handed to its constructor — exposes their schemas to the model,
and turns function calls into function results, concurrently and with errors returned
as observations. The executor is injected into `LLMEngine`, which therefore contains
nothing but the loop itself: adding a capability to the agent means writing a new
`BaseTool` subclass and adding one line in `main.py`.

 The system prompt specifies a
strict *announcement protocol* (formalised with an ordering relation `≺`) requiring the
model to announce each tool invocation before calling it and to ground its report in the
returned result.

## Project layout

```
main.py            Entry point: builds the client, tools, and executor; runs the REPL.
engine.py          LLMEngine — model invocation and the agent loop, nothing else.
prompt.py          System prompt (formal specification of the agent's behaviour).
settings.py        Pydantic settings (GEMINI_API_KEY from .env).
tools/
  base.py          BaseTool — abstract callable with a declared schema.
  executor.py      ToolsExecutor — registry, schemas, concurrent execution.
  web_search/      WebSearchTool (nested Gemini google_search interaction).
  google_maps/     GoogleMapsTool (nested Gemini google_maps interaction).
  bash/            BashTool (subprocess with bounded timeout).
```

## Running it

Requires Python ≥ 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
echo 'GEMINI_API_KEY=<your key>' > .env
uv sync
uv run main.py
```

Type messages at the `user:` prompt; type `quit` to exit.

> **Note.** This is pedagogical code from a live demo, not a production agent: there is
> no sandboxing around the `bash` tool, no persistence, and no error recovery beyond the
> loop itself.
