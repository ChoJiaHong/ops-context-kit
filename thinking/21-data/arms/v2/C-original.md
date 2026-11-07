# Arm C: original model + three additions (English rendering of thinking/00-original-notes.md and the additions in thinking/16-model-selection.md)

Use this method. The items below are what you must look at; the order and any back-and-forth between them are up to you.

Core idea: innovation does not have to be a brand-new technology. Start from the problem, find the best existing solution and its limitation, narrow the situation until a specific difference appears, and use that difference to break the limitation. Innovation = existing solution + a situational difference that actually does work.

1. Treat the problem as stated as a hypothesis, not as fact. Abstract it into a general problem class A(P0).
2. Existing solutions Se: name the best existing solutions for this class that you actually know. Do not invent tools. If a mature solution already solves the problem, repackaging it is not a new solution.
3. Bottleneck L(Se, P): where the best existing solution is no longer the best choice here (efficiency, cost, resources, time, scalability, fit to the situation). Note which assumptions the existing solution is bound to.
4. Down loop (narrow): make the problem more specific, P0 → P1 → P2 …, along six dimensions: people, place, time, behavior, constraints, local resources. At each step, ask whether the added context difference D(Ps, Pg) gives a new constraint, a missing constraint, an available resource, or a changed assumption that would let a better solution exist. Look for resources that are already present and can be reinterpreted (example: a forestry railway that reaches deep into the mountains, reinterpreted as a mobile base for search drones).
5. Match(L, D): does the difference remove or reduce the bottleneck, provide a new resource, or change a constraint? If yes, build Sn = Adapt(Se, L, D). If not, narrow further or change angle.
6. Forced-fit test: remove the situational difference. If Sn still works just as well, the difference was only a label; reject it or keep looking.
7. Up loop (widen): remove specific context step by step, Ps → Ps−1 → …. At each level, Advantage(P, Sn) = U(P, Sn) − max over Se of U(P, Se). Continue while the advantage is positive; stop when it disappears. P* is the widest problem scope where Sn still wins.
8. Goal check: the goal of the final problem must equal the goal of the original problem.

Three additions:
- Existing solutions must be ones you can actually name and describe, not assumed.
- State the advantage as something that could be measured, not just asserted.
- Do not stop at the first idea; stop only after two consecutive rounds produce nothing new.

Your items should be the problems you found with their Sn (state the scope P* inside the item). If no difference beats the best existing solution for a problem, leave that problem out.
