---
description: Enable, restore, or inspect ChatData's Claude Code footer.
disable-model-invocation: true
argument-hint: <enable|restore|status>
---

This command is for Claude Code only. Accept exactly one argument: `enable`, `restore`, or `status`. If the argument is absent or different, show that usage and stop.

Run exactly:

```sh
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/footer.py" $ARGUMENTS
```

Claude substitutes the plugin root in this command content. Do not search for another ChatData installation. Do not edit Claude settings yourself. Report the helper's result plainly. `enable` saves the current footer before installing ChatData. `restore` puts that exact saved footer back when ChatData still owns the current footer. `status` only inspects the local state. None of these actions enables or changes usage reporting.
