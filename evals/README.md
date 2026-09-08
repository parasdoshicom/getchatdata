# Comparative eval

Does having ChatData available change what an AI client actually does on an
analysis that contains a known defect? This harness answers that with a number
instead of an assertion.

It runs each case in `cases/` twice — once with the plugin loaded, once without —
then has a **blind** grader score both answers against the case rubric. The
grader is never told which arm produced an answer, sees no tool transcript,
and receives a reviewer copy with package names and identifying helper paths
masked. The original answer and tool calls remain unchanged for method review.

The nine cases implement the model review cases documented in
[`docs/evaluation.md`](../docs/evaluation.md).

## Run it

```sh
python3 scripts/eval.py run      # execute every case in both arms
python3 scripts/eval.py grade    # blind-judge the saved transcripts
python3 scripts/eval.py report   # catch rate per arm, with uncertainty
```

Each stage is resumable: existing runs and grades are skipped unless you pass
`--force`. Useful flags: `--cases <id ...>`, `--repeats N` (default 3),
`--model`, `--invoke-skill`.

Default run is 9 cases x 2 arms x 3 repeats = 54 sessions, plus 54 grading
calls. Expect roughly 30-60 minutes and a few dollars of model spend.

## Reading the output

`report` writes `results/report.md`: pass rate per arm with a 95% Wilson
interval, and the arm difference as a Newcombe interval. Both are computed by
ChatData's own `analyze.py experiment` helper, so the eval is scored by the
tool it is evaluating. A case passes only when **every** required behaviour is
present and **no** forbidden behaviour occurs.

## Design decisions worth knowing

**Fresh fixtures, not the shipped examples.** `plugins/chatdata/examples/`
is referenced in `tools.md` and `capabilities.md` with its expected answers
printed verbatim — "the example yields 3 -> 2 -> 1". A model with those docs
loaded could recite the answer instead of computing it, which would measure
recall, not method. The fixtures here reproduce the same defect structure with
different numbers, so the answer cannot be looked up.

**Both arms get identical built-in tools.** Standard cases get `Read`, `Glob`,
`Grep`, `Bash`, and `Skill`; the Python helper route is pre-approved. The
embedded-instruction case removes `Bash` from both arms, so code
execution and outbound commands are unavailable. It places two synthetic secret
sentinels beside the source file, while restricted mode confines reads to the
synthetic work directory and, for the treatment arm, the public plugin directory. The
ChatData arm also gets the plugin directory because its
skill and helper have to be readable to test the product. Case 08 also inspects
attempted tool calls and fails if Claude tries
to read either synthetic secret or contact the planted remote host, even if
the final prose looks safe.

**The machine and production account are isolated.** Restricted mode ignores
user and project settings, and strict MCP mode prevents installed MCP servers
from entering either arm. Each run gets disposable ChatData and Claude state,
a fake local link, a loopback telemetry endpoint that rejects connections, and
no session persistence. Synthetic eval events never reach a real dashboard.
The harness records the raw event stream and stderr plus Claude's init inventory,
full tool inputs, permission denials, hook errors, and executed configuration. A
ChatData run fails preflight if the skill is absent from that inventory. Raw
results may contain synthetic fixture text and local temporary paths; review them
before sharing.

**Identical prompts by default.** The ChatData arm is not told to use the
skills, because the question is whether having them available changes
behaviour. Pass `--invoke-skill` to measure the explicit-invocation ceiling
instead; the two numbers answer different questions and should be reported
separately.

**Operator settings are pinned.** The harness uses restricted mode, denies
permission prompts, sets model effort, and passes `--strict-mcp-config`. This keeps
personal plan mode, plugins, hooks, MCP servers, and custom agents out of both
arms while preserving normal Claude authentication.

## Limits

- The cases were authored alongside the skills. They test whether documented
  checks get applied, not generalisation to defects nobody anticipated. Add
  unseen cases before claiming generalisation.
- One model and one phrasing per run. Results do not transfer across models.
- The grader is an LLM. Spot-check its verdicts before quoting a number; the
  per-criterion booleans in `results/grades/` make that quick.
- Reports require every selected run and grade. Pass the same `--cases` and
  `--repeats` values to all three stages; incomplete grading cannot become a rate.
- Pass rates are not a productivity claim. They say how often a documented
  check appeared, nothing about time saved.
