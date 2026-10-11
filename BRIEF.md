# Product brief: Data-Layer Interoperability Checker
**Owner:** Angshuman Rudra · **Status:** v1 shipped (browser + CLI), score not yet validated against measured join rates

**Problem.** Teams buy a CDP and assume customer data is unified. Often it is not: tools use different identifiers, some are siloed, and nobody owns identity. A paid audit is the only way to find out.

**User.** Marketing ops and growth leads who suspect their "unified" stack is not, and need a gut-check before commissioning an audit.

**Decision it supports.** Commission an audit now, fix the obvious break first (name the isolated tool, assign an identity owner), or leave it.

**What v1 does.** Build a stack by tool and identifier; get a live 0-100 fragmentation score, specific flags, and a graph with isolated tools ringed.

**Success measures.** (1) Score tracks measured join rate on two audited stacks. (2) Flags false-alarm rate stays at 0 on clean stacks (measured: 0/100). (3) A marketer can say which tool to fix first after one read.

**Out of scope.** Live integrations, accounts, saving stacks, PDF export, probabilistic matching.

**Risks.** Self-report vs reality. Fixed identifier list. Graph connectivity is a proxy for joinability.

**Open decisions.** Weight the cost of each isolated tool by its spend? Let users mark the intended resolution key?
