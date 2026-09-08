# Claude Code rollback-counterfactual comparison — ChatData 1.7.2

This is a narrow regression check on one synthetic activation analysis. The aggregate rate falls after a release even though both segment rates improve. A correct answer must reconcile the arithmetic and avoid claiming what the release caused or what a rollback would do.

| Condition | Full rubric | Root-cause skill | Link check | Bundled decomposition | Permission denials | Provider cost | Elapsed time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline Claude | 0/3 | — | — | — | 1 | $0.131 | 106s |
| ChatData 1.7.2 | 3/3 | 3/3 | 3/3 | 3/3 | 0 | $0.251 | 146s |

All six answers calculated the descriptive result: activation fell from 68% to 37%, with −36 percentage points from the segment mix and +5 points from within-segment movements. The three baseline answers then treated the observed +5 points as evidence that the release helped and predicted that rollback would forfeit the gain or fail to fix the cause. Those claims are not identified by the data, so all three failed.

All three ChatData sessions selected `chatdata:root-cause` from the ordinary prompt, read the working agreement, checked the isolated local link, and ran `analyze.py decompose` as a standalone Python command. They stated that the release effect and rollback effect were unknown and named the exposure or comparison evidence needed for a decision. No ChatData run had a permission denial, hook error, or recorded run error.

The harness used Claude Sonnet 5 through Claude Code 2.1.265. Each session had a fresh project, restricted tools, no MCP servers or session persistence, a disposable ChatData home, a fake installation credential, update checks disabled, and an unreachable loopback telemetry endpoint. Synthetic usage did not reach the production dashboard.

The [public run record](claude-activation-rollback-v1.7.2.json) contains all six final answers, sanitized tool calls, blind grades, executed settings, timing, provider-reported cost, client/model versions, and run hashes. One baseline session had a denied Python call; its final answer still completed the arithmetic and failed for unsupported causal and counterfactual claims.

## What this result does and does not show

This result shows repeatable skill discovery, link checking, helper adoption, and causal restraint on one known synthetic defect. It does not establish a general accuracy rate, real-world productivity, or a 10× claim. The fixture became part of the regression suite after the first Claude run exposed the defect, so future passes measure regression prevention rather than generalization.

## Reproduce it

```sh
python3 scripts/eval.py run --cases activation-rollback --repeats 3 --model sonnet --out /tmp/chatdata-activation-v1.7.2
python3 scripts/eval.py grade --cases activation-rollback --repeats 3 --model sonnet --out /tmp/chatdata-activation-v1.7.2
python3 scripts/eval.py report --cases activation-rollback --repeats 3 --out /tmp/chatdata-activation-v1.7.2
```
