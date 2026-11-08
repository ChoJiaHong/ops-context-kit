# Arm C2: original model + three additions, with the narrowing dimensions redesigned for agent tools (thinking/26)

Use this method. The items below are what you must look at; the order and any back-and-forth between them are up to you.

Core idea: innovation does not have to be a brand-new technology. Start from the problem, find the best existing solution and its limitation, narrow the situation until a specific difference appears, and use that difference to break the limitation. Innovation = existing solution + a situational difference that actually does work.

1. Treat the problem as stated as a hypothesis, not as fact. Abstract it into a general problem class A(P0).
2. Existing solutions Se: name the best existing solutions for this class that you actually know. Do not invent tools. If a mature solution already solves the problem, repackaging it is not a new solution.
3. Bottleneck L(Se, P): where the best existing solution is no longer the best choice here (efficiency, cost, resources, time, scalability, fit to the situation). Note which assumptions the existing solution is bound to.
4. Down loop (narrow): make the problem more specific, P0 → P1 → P2 …, along eight dimensions. Existing tools were mostly designed for a human operator or a classic program; where an AI agent takes that role, their assumptions break, and that is where new tools fit. On each dimension ask: what does the existing solution assume here, and how is the agent's situation different?
   - Actor: who acts, how many, under which identity, how deterministic, how they read instructions. (Assumptions that break: one identity = one operator; the operator understands what is meant.)
   - Control point: where actions can be seen or intercepted: hooks, wrappers, proxies, MCP servers, CI, the filesystem. (Breaks: you can only read logs afterwards.)
   - State and concurrency: which state is shared, its scope (file, cluster, account), who changes it at the same time. (Breaks: a lock around one command is enough; one person changes things at a time.)
   - Context and memory: what the agent knows at each moment, for how long, and whether it goes stale. (Breaks: the operator remembers what they did.)
   - Lifecycle: synchronous or not, whether anyone is present, interruption, resume, handoff, when effects appear. (Breaks: effects are visible at once; the operator stays present.)
   - Verification: what can confirm what actually happened: tests, dry runs, read-only queries, logs. (Breaks: whoever did it saying it is done means it is done.)
   - Trust boundary: credentials, secrets, sandboxes, untrusted input, permissions. (Breaks: what the operator sees stays with the operator.)
   - Budget: tokens, usage limits, latency, and the scarcest one, human attention. (Breaks: a human has time to review every change.)
   On every dimension also ask: what already exists here that could be reinterpreted for a new purpose? (Examples: Kubernetes Lease objects reused as locks between agents; terraform plan JSON reused as the basis for approval; the hook layer reused to coordinate all sessions rather than only to grant permissions.)
   At each step, ask whether the added context difference D(Ps, Pg) gives a new constraint, a missing constraint, an available resource, or a changed assumption that would let a better solution exist.
5. Match(L, D): does the difference remove or reduce the bottleneck, provide a new resource, or change a constraint? If yes, build Sn = Adapt(Se, L, D). If not, narrow further or change angle.
6. Forced-fit test: remove the situational difference. If Sn still works just as well, the difference was only a label; reject it or keep looking.
7. Up loop (widen): remove specific context step by step, Ps → Ps−1 → …. At each level, Advantage(P, Sn) = U(P, Sn) − max over Se of U(P, Se). Continue while the advantage is positive; stop when it disappears. P* is the widest problem scope where Sn still wins.
8. Goal check: the goal of the final problem must equal the goal of the original problem.

Three additions:
- Existing solutions must be ones you can actually name and describe, not assumed.
- State the advantage as something that could be measured, not just asserted.
- Do not stop at the first idea; stop only after two consecutive rounds produce nothing new.

For each problem here, the problem statement, existing solutions and their shortcomings are given; still apply the method (abstract the problem, check the best existing solution and its bottleneck, narrow along the eight dimensions to find a difference that breaks the bottleneck, forced-fit test, widen to the scope where the advantage holds). Your solution for each problem is the Sn you found. Record each step's result in the design record fields.
