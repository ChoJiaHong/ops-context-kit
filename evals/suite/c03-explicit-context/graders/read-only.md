---
type: regex
target: {"source": "file", "path": ".sim/state.json"}
pattern: "\"mutated\": true"
match: not_contains
---
