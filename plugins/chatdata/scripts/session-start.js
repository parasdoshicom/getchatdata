// Branding and discovery only. No settings edits, network calls, or data access.
const fs = require('fs');
const path = require('path');
const info = JSON.parse(fs.readFileSync(path.join(__dirname, 'package-info.json'), 'utf8'));
process.stdout.write(JSON.stringify({hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:`ChatData ${info.version} is available: free, open-source data science skills. First time? Use /chatdata:status to run local synthetic checks, then /chatdata:data-science to start an analysis. For first-run requests invoke the Skill tool for chatdata:data-science. This free installation is at ${path.resolve(__dirname, "..")}; use only its files, never search the home directory for another ChatData plugin. Read the relevant SKILL.md before analysis. ChatData needs no account; your AI client and data tools may have their own costs.`}}));
