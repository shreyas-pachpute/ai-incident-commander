# AI Operations Incident Commander

## 1. One-Sentence Explanation

This is an AI system that helps engineers figure out what's actually wrong during a production incident, fast — by correlating logs, metrics, and recent changes — while never being allowed to touch production itself without a human's explicit approval.

## 2. The Business Problem

When a production system fails or degrades, the first and most time-critical job is diagnosis: which service is affected, what changed recently that could explain it, what do the logs and metrics actually show, and what's the most likely root cause. On-call engineers do this today by manually correlating information across multiple systems — log aggregators, metrics dashboards, deployment history, infrastructure-change records, alerting tools — often at 3am, under real time pressure, for a system they may not have deep personal familiarity with if the on-call rotation spans a large service surface.

Companies address this today with monitoring and alerting tools (which tell you something is wrong, rarely why), runbooks (useful for known failure patterns, of limited help for novel ones), and on-call engineer expertise built through experience — which means incident response quality varies significantly depending on who's on call and how familiar they happen to be with the specific failing system. The pain concentrates in exactly the highest-stakes moments: an unfamiliar failure mode, at an inconvenient hour, on a system with many recent changes to sift through.

The cost is measured directly in mean-time-to-diagnosis and mean-time-to-resolution, which translate directly into customer-facing downtime, SLA exposure, and engineer burnout from repeated high-pressure, high-cognitive-load incident response. If nothing changes, this scales poorly with system complexity — more microservices, more deployment frequency, and more infrastructure surface area all mean more places an incident's root cause could be hiding, while the number of engineers who can hold the full system's behavior in their head does not grow proportionally.

**This project treats safety as the primary design constraint, not an afterthought.** The system investigates and recommends; it does not execute changes against production infrastructure. That boundary is architectural and non-negotiable, addressed explicitly and repeatedly throughout this document.

## 3. Who Would Use This?

- **On-Call Engineer:** Wants fast, evidence-backed correlation across logs/metrics/deploys the moment an incident starts, especially for unfamiliar systems.
- **Incident Commander (for larger incidents):** Wants a clear, continuously updated picture of what's known, what's being investigated, and what's ruled out, to coordinate response effectively.
- **Engineering Manager / SRE Lead:** Wants faster mean-time-to-diagnosis and a reliable post-incident record, without introducing new operational risk from automated production changes.
- **Security/Compliance function (adjacent):** Wants assurance that no AI system has standing capability to modify production without human authorization, and a full audit trail of every investigation and every proposed action.

## 4. Current Process Without AI

```
Alert fires
 → On-call engineer paged, opens laptop, begins manual triage
 → Engineer checks the alerting dashboard for what's flagged
 → Engineer manually checks logs for the affected service
 → Engineer manually checks recent deployments/infrastructure changes
     (often across multiple separate tools, no unified view)
 → Engineer forms a hypothesis, checks metrics to confirm or refute it
 → If the on-call engineer isn't deeply familiar with the system, this process is slower
     and may require escalating to someone who is, adding delay
 → Once root cause is identified, engineer manually executes or coordinates the fix
 → Incident resolved; postmortem written up manually afterward, often days later
```

The correlation step — pulling together logs, metrics, and deployment history into a coherent picture — is manual and repeated for every incident, even though the *pattern* of investigation (check recent deploys, check error rate by service, check upstream dependencies) is often structurally similar across many incidents.

## 5. Proposed AI-Powered Process

```
Alert fires (existing monitoring/alerting system, unchanged)
 ↓
Deterministic context gathering: affected service, alert type, current metric values,
   recent deployment and infrastructure-change history — structured facts assembled automatically
 ↓
Agent investigation: correlates signals across logs, metrics, and recent changes,
   generates candidate hypotheses for root cause, tests each against available evidence
 ↓
Agent produces a live, continuously updated incident summary: what's known, what's suspected,
   what's been ruled out, and confidence level — visible to the on-call engineer and incident commander
 ↓
Agent proposes remediation options with their risk/reversibility assessed — it does not execute any of them
 ↓
Human engineer reviews the investigation and evidence, decides on and executes the actual remediation
   (via existing, unchanged operational tooling and existing approval processes for production changes)
 ↓
Post-incident, the agent's full investigation trace feeds directly into postmortem drafting for human review
```

## 6. What the AI Actually Does

**Reasoning:** Correlates signals across logs, metrics, and change history to form and test root-cause hypotheses — genuinely open-ended, since the right next thing to check depends on what's already been found.

**Retrieval:** Queries log aggregation, metrics/observability platforms, deployment history, and infrastructure-change records.

**Analysis:** Synthesizes correlated evidence into a coherent incident narrative and root-cause hypothesis with a confidence level.

**Decision support:** Proposes remediation options and characterizes their risk/reversibility — it does not decide which remediation to execute, and it does not execute any of them itself.

**Tool usage:** Read-only queries against logs, metrics, deployment, and infrastructure-change systems.

**Communication:** Produces a continuously updated incident summary and, post-incident, a draft postmortem — both for human review, never sent externally (e.g., to a status page or customers) without human approval.

**Validation:** Every claim in the investigation traces to a specific log line, metric value, or change record — the agent doesn't assert a root cause its own evidence doesn't actually support.

**What the AI does NOT do:** It does not execute any change against production infrastructure — no restarts, rollbacks, scaling changes, configuration changes, or deployments, regardless of how confident its diagnosis is. It does not decide the remediation strategy. It does not communicate externally (status pages, customer communication) without explicit human approval. This is the single most important boundary in this project and is treated as absolute, not risk-adjusted based on incident severity or time pressure.

## 7. Where AI Is Used

AI is good at rapidly correlating signals across multiple, disconnected systems (logs, metrics, deploys, infra changes) that a human would otherwise have to manually cross-reference — genuinely valuable time-compression during exactly the moments when time matters most. It's good at generating and testing root-cause hypotheses in a structured way, adapting the investigation path based on what's found, which mirrors Project 09's core justification for agentic (rather than scripted) investigation and applies with even more urgency here given the time pressure of live incidents. It's good at maintaining a clear, continuously updated summary during a chaotic, fast-moving incident — something that's valuable specifically because human incident responders are often too busy actively debugging to also maintain a clear written record in real time.

Deterministic software must handle initial alert triggering and context assembly (pulling the structured facts an investigation starts from), and — critically — any actual remediation execution stays with existing, unchanged operational tooling and existing human-approval processes for production changes. The agent's role is strictly bounded to investigation, correlation, and recommendation.

## 8. Agent vs Workflow vs Normal Software

- **Normal software:** The monitoring/alerting system, log aggregation and metrics platforms, deployment/infra-change tracking, the incident-management/paging tooling, and — unchanged by this project — the actual remediation execution tooling and its existing approval processes.
- **Deterministic workflow:** Initial context gathering when an alert fires (which service, current metric snapshot, recent deploy list) is a fixed sequence, not agentic reasoning.
- **AI agent:** The correlation and root-cause investigation is genuinely open-ended in the same way as Project 09's data investigation — the right next check depends on what's already found, and a fixed script cannot capture that. This is the agent's scoped role, and it is investigation-only by design.
- **Multi-agent system:** Justified in a specific, bounded way for larger, multi-service incidents: parallel **investigation threads**, each correlating evidence for a different candidate affected service or hypothesis, converging into a single incident commander view — a parallelism/latency justification appropriate given how directly incident-response speed translates into business cost, similar in spirit to Project 09's parallel hypothesis threads but with an even stronger time-pressure rationale.

## 9. Agent Roles

**Incident Investigation Agent:** "Given an active incident (the alert, affected service, and available telemetry), correlate logs, metrics, and recent changes to identify the most likely root cause, maintaining a continuously updated, evidence-backed summary throughout the incident's lifecycle." At scale, this can spawn parallel **Service-Scoped Investigation Threads** for multi-service incidents, with a coordinating summary layer — the same parallel-hypothesis pattern as Project 09, applied under tighter time pressure. No agent in this system has any tool that can modify production state — this is true of every role, not a property of one role among several.

## 10. Tools the AI Needs

In business terms: the log aggregation system, the metrics/observability platform, deployment history, infrastructure-change records, and the incident-management/paging system (to post updates to the incident channel).

Technically: read-only connectors to the log aggregator (Datadog/Splunk/ELK-style), the metrics platform (Prometheus/Grafana-style), the deployment/CI-CD history system (read-only — triggering is explicitly out of scope), and the infrastructure-as-code change history (read-only). A write connector to the incident-management channel is scoped narrowly to posting investigation summaries, not to any operational action.

## 11. MCP Opportunities

Logs, metrics, and deployment/infra-change history are strong MCP **Tool** candidates — the agent decides what to query next based on its evolving hypothesis, exactly the agent-discretionary access pattern MCP tools are suited for. Current incident context (the triggering alert, affected service) is a good MCP **Resource**, loaded deterministically when an investigation starts. What must **not** be exposed via MCP or any agent-invokable interface, under any circumstance: any production execution capability — deployment tools, infrastructure-as-code apply/execute capability, container/service restart or scaling commands, configuration-management write access. This project is the clearest illustration in the entire portfolio of the "don't build the dangerous capability at all" principle (echoing Project 04's and Project 06's reasoning): there is no approval workflow sophisticated enough to justify giving an LLM-driven agent standing execution access to production infrastructure, so the correct design is that the tool simply does not exist in this agent's toolset.

## 12. Human-in-the-Loop

**Low-risk (automatic):** Reading logs/metrics/deployment history, correlating evidence, generating and updating the investigation summary, posting updates to the incident channel.

**Medium-risk (requires review before being treated as authoritative):** The root-cause hypothesis and confidence level — engineers use it to guide their own investigation and decision-making, but it's explicitly framed as an input to human judgment, not a verdict, especially early in an incident when evidence may still be incomplete.

**High-risk (must never happen automatically, structurally excluded — no exceptions for incident urgency):** Any production remediation action — restarts, rollbacks, scaling, configuration changes, deployments — and any external communication (status page updates, customer communications). It would be tempting, under real incident time pressure, to argue for a "trusted" fast-path for very high-confidence, low-risk-seeming automated remediation (e.g., an automatic rollback when a deploy correlation is extremely strong) — this document explicitly does **not** recommend that for the reasons in Section 23, and treats the human-execution boundary as a permanent property of the system, not a temporary MVP conservatism to relax later.

## 13. Business Value

The clearest measurable driver is mean-time-to-diagnosis, directly measurable by comparing agent-assisted investigation time against the historical baseline for comparable incident types and severities. A second driver is reduced variance in incident-response quality across the on-call rotation — a less experienced on-call engineer, assisted by fast, correlated evidence, should perform closer to how a highly experienced engineer would on an unfamiliar system, though this specific claim needs pilot data segmented by engineer experience level to validate rigorously rather than assert. We would not assign a specific downtime-cost-avoidance dollar figure without an organization's own historical incident-cost data; the correct approach is to instrument mean-time-to-diagnosis and let a pilot period translate that into the organization's own downtime-cost model.

## 14. Success Metrics

- **Mean-time-to-diagnosis**, compared to the historical baseline, segmented by incident severity and by on-call engineer experience level.
- **Root-cause accuracy** — on a curated set of past incidents with confirmed causes, does the agent's investigation identify the correct one?
- **Evidence grounding** — does every claim in the investigation summary trace to an actual queried log/metric/change record, automatically verifiable?
- **Confidence calibration** — same principle as Project 09: when the agent reports high confidence, is it actually right more often?
- **Engineer trust/adoption** — do on-call engineers actually use and rely on the investigation summary during live incidents, sampled via post-incident survey.
- **Zero unauthorized-action incidents** — a hard-floor metric that should never register above zero, given the system has no execution capability by design; tracked anyway as a continuous verification that the architectural boundary holds.
- **Cost per incident investigated.**

## 15. Failure Scenarios

- **Wrong root-cause hypothesis presented with high confidence:** the most damaging failure mode for this project — mitigated by mandatory evidence citation, confidence calibration evaluation, and explicit display of what's been ruled out, not just what's confirmed.
- **Incomplete investigation under time pressure:** the agent should clearly communicate investigation status and confidence rather than forcing a premature conclusion just because time is short — the human incident responder needs to know "still investigating, here's what's ruled out so far" is a legitimate and useful state, not a failure to report.
- **Tool/data-source unavailability during the incident** (log system itself degraded, which happens during real incidents more often than one would like): the agent should report clearly what it could and couldn't check, rather than proceeding as if it had full visibility.
- **Correlation without causation:** flagging a coincidental deploy or metric pattern as the cause when it's unrelated — mitigated by requiring the agent to state the strength and nature of the correlation, not just its existence, and by human review before any correlation is treated as confirmed causation.
- **Attempted unauthorized action:** structurally impossible, per Section 12 — there is no remediation tool in this agent's toolset for any action to attempt, which is a stronger guarantee than a policy or approval gate could provide under incident time pressure, when approval gates are exactly the kind of safeguard people are most tempted to bypass "just this once."

## 16. Safety and Security

This project's entire design center is safety, more than any other project in this portfolio. All tool access is strictly read-only against production observability and change-history systems — no write, execute, or configuration-change capability exists anywhere in the agent's toolset, and this is enforced at the tool-registration level (the capability is never built), not via a permission check that could be misconfigured or bypassed under pressure. Access is scoped to what the on-call engineer's own role would permit — no broader visibility into systems than a human responder would already have. Every query, correlation, and generated summary is logged in full, both for the mandatory evidence-citation requirement (Section 6) and because incident investigations are exactly the kind of record that needs to survive intact for postmortem and, in regulated industries, compliance review. Given that logs and metrics can occasionally contain user-influenced content (e.g., a user-agent string, an error message containing user input), the same untrusted-input discipline from Research Notes Section 27 applies even in this comparatively lower-injection-risk, internal-systems-focused project.

## 17. Evaluation

- **Root-cause accuracy** against a curated historical incident set with confirmed causes — the central evaluation metric, evaluated separately by incident type (deployment-caused, infrastructure-caused, traffic-driven, dependency failure) since these require different investigation patterns.
- **Trajectory evaluation:** does the agent investigate efficiently under the specific time pressure this domain has, avoiding redundant or low-value queries (Research Notes Section 25)?
- **Evidence-grounding check:** automated verification that every claim traces to an actual queried record.
- **Confidence calibration:** statistical comparison of stated confidence against actual correctness across many incidents.
- **Human evaluation:** on-call engineer rating of investigation usefulness, collected as part of standard post-incident review.
- **Adversarial/safety evaluation:** explicit red-team testing confirming the agent cannot be prompted (via any combination of alert content, log content, or instruction) into attempting a production action — arguably as important a category here as in Project 06.
- **Regression suite:** a fixed set of historical incident scenarios (replayed against snapshotted telemetry) re-run on every prompt/tool change.

## 18. Observability

Track, per incident investigation: every query run against every system, every hypothesis generated and its evidence, the evolving confidence level over the incident's lifecycle, and the final human-executed remediation and outcome (captured after the fact, connecting the AI's investigation to what actually happened). This is essential for two purposes distinct from most other projects in this portfolio: real-time incident coordination (an incident commander needs to see the current state of the investigation as it evolves, not just a final report) and rigorous postmortem reconstruction (a postmortem needs the full evidence trail, not a reconstructed-from-memory narrative). Track root-cause-accuracy and confidence-calibration trends over time as the primary quality dashboard, and treat the "zero unauthorized-action attempts" metric as a standing security-monitoring item, not just a one-time verification.

## 19. Technology Options

**LangGraph:** *Why:* the correlate-hypothesize-test-refine loop under a live, evolving incident is a strong fit for LangGraph's stateful, cyclic orchestration, and the continuously-updated-summary requirement benefits from persisted, streamable state exactly as LangGraph is designed to support. *Why not:* unnecessary overhead if the MVP is scoped to single-service, comparatively simple incidents with a shallow investigation depth. *Alternative:* a simpler bounded agent loop for the MVP, adopting LangGraph as multi-service parallel investigation (Section 8) is added.

**OpenTelemetry-based observability platforms (as the data source, not the AI framework):** *Why:* if the organization's logs/metrics/traces are already instrumented via OpenTelemetry, the agent's query tools can be built against a standard, vendor-neutral telemetry model rather than a bespoke integration per tool (Research Notes Section 26). *Why not:* not every organization has this instrumented uniformly; tool integrations may need to be built per specific platform (Datadog, Splunk, etc.) in practice. *Alternative:* platform-specific connectors where OpenTelemetry coverage is incomplete.

**MCP:** *Why:* logs, metrics, and deployment-history connectors are broadly reusable internal infrastructure, valuable beyond just this one agent (e.g., a future capacity-planning agent could reuse the same metrics connector). *Why not:* not justified for a narrow, single-consumer pilot. *Alternative:* direct platform API integration initially.

**Temporal:** *Why:* larger incidents can genuinely run for hours, and durable execution ensures the investigation state survives a process restart or a long-running correlation task without losing progress — directly relevant given Research Notes Section 16's point that production coding/automation agents increasingly run on durable-execution platforms specifically for this reason. *Why not:* likely unnecessary for the MVP's shorter, single-service incident scope. *Alternative:* in-memory/database-checkpointed state for shorter incidents, adopting Temporal as incident duration and system complexity grow.

## 20. Proposed Architecture

```
Alert Fires (existing monitoring/alerting, unchanged)
        |
  Deterministic Context Assembly: affected service, alert type, recent deploys/changes
        |
  Incident Investigation Agent (LangGraph, cyclic correlate-hypothesize-test loop)
        |
   +------------------------------+
   |        Tool Layer (MCP, all READ-ONLY) |
   +------------------------------+
   |         |            |       |
  Logs      Metrics    Deployment  Infra-Change
  (MCP)     (MCP)      History     History (MCP)
                        (MCP)
        |
  Live Investigation Summary -> Incident Channel (posted, not acted on)
        |
  Human Engineer Reviews -> Executes Remediation via EXISTING, UNCHANGED Ops Tooling & Approval Process
        |
  Post-Incident: Investigation Trace -> Draft Postmortem (human-reviewed)
        |
  Evaluation & Observability / Adversarial Safety Testing Layer
```

## 21. MVP

The smallest version that proves value: for a single, well-instrumented service, an investigation agent (no parallel threads yet) that, given an alert, correlates logs/metrics/recent deploys and produces a live, evidence-backed summary posted to the incident channel for on-call engineer use — no automated postmortem drafting yet, no multi-service correlation. This validates root-cause accuracy and engineer trust under real (if narrow-scope) incident conditions, and validates that the read-only tool boundary holds operationally, before expanding scope.

## 22. Future Version

MVP → expand to more services and add cross-service correlation for multi-service incidents → add parallel service-scoped investigation threads for faster diagnosis on complex incidents → add automated draft-postmortem generation from the investigation trace, for human review and completion → add historical-incident pattern matching ("this resembles an incident from two months ago caused by Y") as an additional hypothesis-generation signal → the read-only, no-execution-capability boundary remains permanent at every future stage — this is the one design property this document explicitly recommends never relaxing, regardless of how much trust the system earns over time, given the asymmetric downside of a wrong automated production action versus the bounded cost of requiring human execution.

## 23. What Makes This Project Difficult?

Diagnostic accuracy under genuine time pressure is harder than diagnostic accuracy given unlimited time — an agent that's accurate but too slow, or fast but frequently wrong, both fail the actual use case, so the trajectory-efficiency and latency evaluation (Section 17/25) matters as much as raw accuracy here as in almost no other project in this portfolio. Getting broad, reliable read access across a genuinely heterogeneous observability stack (different logging tools, different metrics platforms, inconsistent instrumentation coverage across services) is a real integration engineering challenge independent of the AI reasoning problem. The temptation to add automated remediation for "obviously safe" cases will recur as the system proves accurate over time, and resisting it consistently — even under pressure from stakeholders who've seen the system be right many times in a row — requires the same discipline called out in Project 04's Section 23, arguably with higher stakes given production blast radius. Building a rigorous historical-incident evaluation set requires genuinely good incident documentation discipline, which many organizations (per Section 4's description of manual, delayed postmortems) don't reliably have today.

## 24. What I Would Demonstrate When Implementing It

A genuinely cyclic, stateful investigation agent under realistic time-pressure constraints; strictly read-only tool access across a heterogeneous observability stack with the execution boundary enforced at the tool-registration level, verified by adversarial testing, not just documented as a policy; confidence calibration evaluation specific to incident-response accuracy; a parallel-investigation-thread pattern justified by the domain's genuine latency sensitivity; and an observability design supporting both real-time incident coordination and full post-incident audit reconstruction.

## 25. Portfolio Story

"Incident response is one of the highest-stakes places to get an agent's boundaries wrong, because the pressure to let it 'just fix it' is highest exactly when the system has been reliably right many times before — and that's precisely the moment a wrong automated action does the most damage. I designed this system with a permanent, structural boundary: it investigates and correlates evidence across logs, metrics, and deployment history, faster than a human could manually cross-reference those systems, but it has no tool in its toolset that can touch production, verified by adversarial red-team testing, not just documented as policy. I evaluated it as much on confidence calibration — does its stated confidence actually track its correctness — as on raw root-cause accuracy, because an on-call engineer needs to know when to trust it less just as much as when to trust it."

## 26. Questions a CTO Might Ask Me

1. How do you guarantee the agent literally cannot execute a production action, even under a clever prompt?
2. Why not allow automated remediation for very high-confidence, clearly reversible cases?
3. How do you evaluate diagnostic accuracy under genuine time pressure, not just accuracy given unlimited time?
4. What happens when the observability stack itself is degraded during the incident?
5. How do you prevent a coincidental correlation from being presented as a confirmed root cause?
6. What's your confidence-calibration methodology, concretely?
7. How does this system perform differently for an on-call engineer new to a service versus a veteran?
8. What's the adversarial testing process for the read-only tool boundary?
9. How do you keep the investigation summary useful during a chaotic, fast-moving multi-service incident?
10. Why is parallel investigation-thread decomposition justified here versus a single sequential agent?
11. How would you build a rigorous historical-incident evaluation set given most postmortems are informal today?
12. What's the cost and latency profile, and how does that trade off against speed during a live incident?
13. How do you handle an incident type the agent has never seen a similar pattern for?
14. What's the audit trail available for a postmortem or a regulatory review after the fact?
15. How do you resist organizational pressure to expand this system's capability toward automated action over time?

## 27. Research Sources

- [LangGraph vs LangChain 2026 — Spheron Blog](https://www.spheron.network/blog/langgraph-vs-langchain/)
- [OpenTelemetry for AI Systems: LLM and Agent Observability (2026) — Uptrace](https://uptrace.dev/blog/opentelemetry-ai-systems)
- [Temporal — AI Applications & Agents](https://temporal.io/solutions/ai)
- [OWASP Top 10 Agents & AI Vulnerabilities (2026 Cheat Sheet)](https://blog.alexewerlof.com/p/owasp-top-10-ai-llm-agents)
- [Beyond Static Sandboxing: Learned Capability Governance for Autonomous AI Agents — arXiv](https://arxiv.org/pdf/2604.11839)
- See also [../RESEARCH_NOTES.md](../RESEARCH_NOTES.md) for full ecosystem sourcing.
