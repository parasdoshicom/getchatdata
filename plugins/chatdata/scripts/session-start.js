// Branding and discovery only. Telemetry is separate and runs only after consent.
const fs = require('fs');
const path = require('path');
const info = JSON.parse(fs.readFileSync(path.join(__dirname, 'package-info.json'), 'utf8'));
const root = path.resolve(__dirname, '..');
const context = [
  `ChatData ${info.version} is available: free, open-source data science skills.`,
  'First time? Use /chatdata:status to run local synthetic checks, then /chatdata:data-science to start an analysis.',
  'For first-run requests invoke the Skill tool for chatdata:data-science.',
  `This free installation is at ${root}; use only its files, never search the home directory for another ChatData plugin.`,
  'Read the relevant SKILL.md before analysis.',
  'A personal ChatData account is used for the download and optional content-free usage dashboard.',
  'When usage reporting is linked, ChatData counts explicit ChatData workflows and elapsed time; it never sends prompts, files, paths, queries, results, model details, or session IDs.',
  'Savings are estimates based on the user’s own baseline and hourly value. AI client and data-tool costs may still apply.'
].join(' ');
process.stdout.write(JSON.stringify({hookSpecificOutput:{hookEventName:'SessionStart',additionalContext:context}}));
