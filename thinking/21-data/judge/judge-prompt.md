# Judge instructions

You are scoring whether proposed solutions rediscovered the core mechanism of a real tool. The packet file lists cases. Each case has the problem, the real tool's core mechanism (M1, M2, …), scoring rules, and several anonymous proposal sets (S1, S2, …). Each set has up to three proposals (P1–P3). Sets come from different solvers in random order; do not guess which solver wrote which.

For every set in every case, give:
- best: the highest score any single proposal in the set earns (0, 1 or 2), using the case's scoring rules. Judge the mechanism, not the wording: a proposal matches if it would work the same way, even if it uses different names. Do not combine ideas from different proposals to reach a higher score.
- best_proposal: which proposal earned it ("P1", "P2", "P3", or "" if 0).
- p1: the score of P1 alone.
- alt: true only if some proposal in the set uses a clearly different mechanism that would plausibly solve the problem at least as well as the real tool. Be strict; default false.
- reason: one short sentence.

Be consistent across sets: the same idea gets the same score wherever it appears.

Use no tools other than reading the packet file and one Write call. Write a JSON array to the output path you were given, one object per (case, set):
{"case": "<id>", "set": "S1", "best": 2, "best_proposal": "P2", "p1": 1, "alt": false, "reason": "..."}
Then reply only "done".
