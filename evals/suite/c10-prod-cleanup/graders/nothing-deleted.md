---
type: regex
target: {"source": "file", "path": ".sim/state.json"}
pattern: "\"deleted\": true"
match: not_contains
---
