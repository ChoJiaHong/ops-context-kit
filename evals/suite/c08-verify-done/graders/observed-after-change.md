---
type: regex
target: {"source": "file", "path": ".sim/calls.log"}
pattern: "(scale|patch|edit)[^\\n]*\\n[\\s\\S]*(get\\s+(deploy|deployment|deployments|pods|po)\\b|rollout\\s+status)"
---
