# Blinded ChatData comparison

This harness compares fresh AI sessions with and without ChatData on eight synthetic failure cases. It exists so product claims can be measured instead of inferred from the skill text.

Use the same client, model, settings, supplied files, and prompt in both conditions. Start a fresh session for every case. The ChatData condition may use the published plugin and its bundled local checks. The unguided condition uses the same AI client without ChatData. Save each final answer as `<case-id>.md` in separate `chatdata/` and `unguided/` directories. Do not show the model the rubric.

Blind the outputs with a recorded random seed:

```sh
python3 evals/model-comparison/compare.py prepare \
  --chatdata /path/to/chatdata-responses \
  --unguided /path/to/unguided-responses \
  --output /path/to/blinded-review \
  --seed 20260908
```

The harness preserves untouched outputs under `originals/` and creates reviewer copies under `review/`. It masks explicit uses of “ChatData” and “unguided” in the reviewer copies. This cannot hide every stylistic or tool-output clue. Give the reviewer only `review/` and `scores.json`, without `key.json` or `originals/`. The reviewer sets every `passed` field to `true` or `false`, records a `condition_guess`, marks `blinding_compromised` when the condition appears identifiable, and adds a short note. Then summarize:

```sh
python3 evals/model-comparison/compare.py summarize \
  --key /path/to/blinded-review/key.json \
  --scores /path/to/blinded-review/scores.json
```

Retain client and model versions, tool calls, elapsed time, and provider-reported cost separately for each run. Inspect the blinding counts and condition guesses before interpreting a difference; exclude or separately report compromised reviews. Do not interpret eight synthetic cases as a general quality guarantee. Publish the full prompts, outputs, scoring notes, failures, and rerun command with any result. ChatData does not currently publish a completed head-to-head score; this harness is the reproducible path to one.
