# Judge instructions (version 2: finding problems)

Solvers were given only a broad situation (an infra engineer delegating most work to AI coding agents across many parallel sessions) and asked to find unsolved problems and propose a tool for each. The targets file lists real tools released later, each with the problem it solves and its core mechanism. The lists file has anonymous answer lists (L1, L2, …), each with up to ten items (I1–I10, "problem || tool"). Lists come from different solvers in random order; do not guess who wrote which.

For every list and every target, give a score:
- 2: one single item states essentially the target's problem AND its tool meets the target's "Full match" rule.
- 1: one single item states essentially the target's problem but its tool meets only the "Partial match" rule or uses a different mechanism; OR one item's tool meets the target's Full match rule while aiming at a clearly related problem.
- 0: otherwise.
Judge the substance, not the wording. Do not combine ideas from different items. Each item may be credited to at most one target (the one it matches best); if one item could match two targets, credit the better match only.

Also, for every list, count `unmatched_valuable`: items that match no target but describe a real, currently unsolved problem with a concrete, plausibly better tool. Be strict.

Use no tools other than reading the two files and one Write call. Write a JSON array to the output path you were given, one object per (list, target):
{"list": "L1", "target": "<id>", "score": 2, "item": "I3", "reason": "<short>"}
plus one object per list: {"list": "L1", "unmatched_valuable": 4}
Then reply only "done".
