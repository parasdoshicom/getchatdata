# Claude Code funnel comparison — ChatData 1.7.1

Run on September 8, 2026 with Claude Sonnet 5 in Claude Code 2.1.263: one
synthetic funnel case, one prompt, two arms, and three fresh sessions per arm.

| Arm | Rubric passes | Loaded ChatData skill | Ran bundled funnel helper | Provider cost | Elapsed |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0/3 | 0/3 | 0/3 | $0.116 | 76s |
| ChatData 1.7.1 | 3/3 | 3/3 | 3/3 | $0.225 | 108s |

The fixture includes a duplicate purchase, an out-of-order purchase, and one
entrant whose 48-hour conversion window extends past the observation cutoff.
Every ChatData run reported the checked mature funnel of 5 visits, 4 signups,
and 2 purchases. Every baseline run reported the partial-cohort funnel of 6,
5, and 2 as its primary result, treating the immature entrant as a
non-converter.

The evaluator ran Claude in restricted mode with the same prompt and built-in
tools in both arms. Personal settings, plugins, hooks, MCP servers, and session
history were excluded. The ChatData arm received only the public plugin under
test. Its usage state was disposable and its telemetry endpoint was loopback,
so no synthetic events reached a production dashboard. The grader saw final
answers only, in shuffled order, with package-identifying text masked. Original
answers and tool calls were inspected separately to verify method adoption. The
[public run record](claude-funnel-v1.7.1.json) includes the six answers, tool
calls, grades, executed settings, elapsed time, provider-reported cost, client and
model versions, and fixture hash with local paths removed.

This result shows that ChatData changed Claude's behavior on this one known
synthetic funnel defect. It does not establish a general accuracy rate, prove
performance on unseen defects or other models, or measure time and dollar
savings. Run the other cases and add unseen fixtures before making a broader
claim.

Reproduce it from the repository root:

```sh
python3 scripts/eval.py run --cases funnel-ordering --repeats 3 --model sonnet --out /tmp/chatdata-funnel-v1.7.1
python3 scripts/eval.py grade --cases funnel-ordering --model sonnet --out /tmp/chatdata-funnel-v1.7.1
python3 scripts/eval.py report --cases funnel-ordering --out /tmp/chatdata-funnel-v1.7.1
```
