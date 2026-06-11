---
name: ci-watch
description: announce when CI fails on a repo
watch:
  interval_secs: 300
action:
  command: gh run list -R OWNER/REPO -L 1 --json conclusion,displayTitle --jq '.[] | select(.conclusion=="failure") | "CI failed on REPO: " + .displayTitle'
requires:
  bins: [gh]
---
Install: copy to ~/.remy/skills/ci-watch/ and replace OWNER/REPO.
Needs `gh auth login` once. Speaks only when the failing run changes;
silent while CI is green.
