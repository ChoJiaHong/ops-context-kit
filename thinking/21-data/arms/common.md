# Common instructions (all arms)

You will receive several independent problems. Each describes a real situation faced by engineers who use AI coding agents. For each problem, think about how it should be solved, then propose solutions.

Rules:
- Do not use any tools except one final Write call to save your answer. No web search, no file reading, no code execution. Work from your own knowledge and reasoning only.
- Treat each problem independently.
- Output format for each problem (exactly this structure):

```
## <case id>
### Analysis
<your working, at most 400 words>
### Proposals
P1: <short name> — <mechanism, at most 80 words: what it does and how it works>
P2: <short name> — <mechanism, at most 80 words>
P3: <short name> — <mechanism, at most 80 words>
```

- P1 is the proposal you think is best. You may give fewer than three proposals, never more.
- Describe mechanisms concretely enough that an engineer could build them. Do not just name a category ("add monitoring").
- Save the whole answer with one Write call to the path given at the end of your instructions, then reply only "done".
