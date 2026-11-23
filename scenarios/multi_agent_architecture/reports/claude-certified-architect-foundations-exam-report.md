# Claude Certified Architect – Foundations (CCAR-F): Exam Report

## Executive Summary

The Claude Certified Architect – Foundations (CCAR-F) exam validates that a candidate can make informed tradeoff decisions when implementing real-world solutions with Claude Code, the Agent SDK, the Claude API and MCP. It is a closed-book, proctored exam of 60 multiple-choice and multiple-response items, delivered in 120 minutes, with 4 scenarios drawn at random from a bank of 6. The pass mark is 720 on a 100-1000 scaled score, and the fee is $125 USD per attempt. The credential is valid for 12 months. Content is split across five weighted domains: Agentic Architecture and Orchestration (27%), Tool Design and MCP Integration (18%), Claude Code Configuration and Workflows (20%), Prompt Engineering and Structured Output (20%), and Context Management and Reliability (15%). The official exam guide (v1.1, Nov 2026) is the primary and preferred source. Web research is secondary because official Anthropic and Skilljar pages returned 403. Several claims remain unverified, including the Partner Network requirement, free pricing for partners, and whether the Dec 7, 2026 content update affects CCAR-F. Candidates testing after Dec 7 should confirm with Anthropic.

**Source key:** [Guide] = official exam guide v1.1, Nov 2026 (file: /home/wappnet-7/Downloads/course_completion_certificate/guide/Claude_Certified_Architect_-_Foundations_Exam_Guide (1).pdf). [Web] = web research, mostly Pearson VUE and third-party pages (official Anthropic/Skilljar pages returned 403). Where they conflict, the Guide is preferred.

---

## 1. Overview
- **Purpose:** Validates that a candidate can make informed tradeoff decisions when implementing real-world solutions with Claude Code, the Agent SDK, the Claude API and MCP. [Guide; Web consistent]
- **Audience:** Solution architects building production applications with Claude, with 6+ months hands-on experience with the APIs, Agent SDK, Claude Code and MCP. [Guide]. [Web]: this is guidance, not a formal prerequisite.
- **Exam code:** CCAR-F (Guide and Pearson). "CCA-F" appears only in third-party sources.
- **Related exams (third-party only, unverified):** Associate-Foundations CCAO-F $99; Developer-Foundations CCDV-F $125; Architect-Professional CCAR-P $175.

## 2. Exam Format
| Item | Value | Source |
|---|---|---|
| Items | 60, multiple-choice and multiple-response (each item states how many to select) | Guide; Web agrees |
| Scenarios | 4 drawn at random from a bank of 6 | Guide; Web agrees |
| Duration | 120 minutes, no breaks (about 135 min including check-in) | Guide (120); Web (no breaks, 135) |
| Passing score | 720 on 100-1000 scaled | Guide; Web agrees |
| Book | Closed-book, proctored | Web; Guide rules consistent |
| Delivery | Online proctored (OnVUE) and/or Pearson VUE test center | Guide, Web |
| Fee | $125 USD per attempt | Guide, Web |
| Validity | 12 months from award | Guide, Web |
| Results | Pass/fail, scaled score, percent-correct by domain (informational only) | Guide |
| Scoring | Criterion-referenced, formal standard-setting, scaled equating | Guide |
| Credential | Credly badge on pass | Web only |

**Resolved conflict:** one web source claimed the live exam draws from thirteen scenarios; the Guide says 6, so use 6.

## 3. Domains and Weights [Guide; Web weights match]
| Domain | Weight | Task statements |
|---|---|---|
| D1 Agentic Architecture & Orchestration | 27% | 1.1-1.7 (7) |
| D2 Tool Design & MCP Integration | 18% | 2.1-2.5 (5) |
| D3 Claude Code Configuration & Workflows | 20% | 3.1-3.6 (6) |
| D4 Prompt Engineering & Structured Output | 20% | 4.1-4.6 (6) |
| D5 Context Management & Reliability | 15% | 5.1-5.6 (6) |

30 task statements total.

**In scope:** agentic loops, multi-agent orchestration, subagent context, tool design, MCP, error handling, escalation, CLAUDE.md, commands/skills, plan mode, structured output, few-shot, batch processing, context optimization, human review, provenance.

**Out of scope:** fine-tuning, API auth/billing, language/framework detail, deploying MCP servers, model internals/training, Constitutional AI/RLHF, embeddings/vector DBs, computer use, vision, streaming/SSE, rate limits/pricing, OAuth/key rotation, cloud config, benchmarking, prompt caching implementation, token counting. [Guide]

## 4. Scenarios [Guide]
1. **Customer Support Resolution Agent:** Agent SDK, MCP tools get_customer, lookup_order, process_refund, escalate_to_human, 80%+ first-contact resolution target. Domains 1, 2, 5.
2. **Code Generation with Claude Code:** slash commands, CLAUDE.md, plan mode. Domains 3, 5.
3. **Multi-Agent Research System:** coordinator with web search, document analysis, synthesis, report subagents. Domains 1, 2, 5.
4. **Developer Productivity with Claude:** built-in tools (Read/Write/Bash/Grep/Glob) plus MCP. Domains 2, 3, 1.
5. **Claude Code for CI:** code review, test generation, PR feedback, minimal false positives. Domains 3, 4.
6. **Structured Data Extraction:** JSON schema validation, edge cases. Domains 4, 5.

## 5. Task Objectives [Guide only]

### D1 Agentic Architecture & Orchestration
- **1.1 Agentic loops:** control flow on stop_reason (tool_use continues, end_turn terminates). Anti-patterns: parsing natural language for completion, arbitrary iteration caps as primary stop, checking assistant text.
- **1.2 Coordinator-subagent:** hub-and-spoke; subagents do not inherit coordinator history; dynamic selection, scope partitioning, iterative refinement; all communication via the coordinator.
- **1.3 Subagent invocation:** allowedTools must include "Task"; pass context explicitly; AgentDefinition; fork-based sessions; parallel subagents via multiple Task calls in one response.
- **1.4 Workflow enforcement/handoff:** programmatic gates (hooks, prerequisite blocks) beat prompt guidance, e.g. block process_refund until get_customer returns verified ID; structured handoff summaries.
- **1.5 SDK hooks:** PostToolUse normalizes data formats; interception hooks block policy violations (e.g. refunds over $500).
- **1.6 Task decomposition:** fixed prompt chaining vs dynamic adaptive; per-file passes plus cross-file integration pass.
- **1.7 Session state:** --resume <session-name>, fork_session, inform resumed session of file changes, start fresh with structured summary when tool results are stale.

### D2 Tool Design & MCP Integration
- **2.1 Tool interfaces:** descriptions are the primary selection mechanism; overlapping tools (analyze_content vs analyze_document) hurt; split generic tools; review system prompts for keyword-sensitive instructions.
- **2.2 Structured MCP errors:** isError flag; categories transient/validation/business/permission; errorCategory, isRetryable, readable description; distinguish access failures from valid empty results.
- **2.3 Tool distribution and tool_choice:** too many tools (18 vs 4-5) degrades selection; scoped per-role access; tool_choice auto/any/forced.
- **2.4 MCP server integration:** project .mcp.json (shared) vs user ~/.claude.json; env var expansion (${GITHUB_TOKEN}); MCP resources expose catalogs; prefer existing community servers.
- **2.5 Built-in tools:** Grep content, Glob paths, Read/Write full files, Edit targeted; fall back to Read+Write when Edit fails on non-unique text.

### D3 Claude Code Configuration & Workflows
- **3.1 CLAUDE.md hierarchy:** user ~/.claude/CLAUDE.md, project, directory-level; @import; .claude/rules/; /memory to debug.
- **3.2 Slash commands and skills:** project .claude/commands/ vs personal ~/.claude/commands/; SKILL.md frontmatter context: fork, allowed-tools, argument-hint.
- **3.3 Path-specific rules:** .claude/rules/ with YAML paths: globs; loaded only when matching files are edited; preferred over subdirectory CLAUDE.md for cross-directory conventions.
- **3.4 Plan mode vs direct execution:** plan for large multi-file/architectural work, direct for small; Explore subagent isolates verbose discovery.
- **3.5 Iterative refinement:** 2-3 examples, test-driven iteration, interview pattern; one message for interacting problems, sequential for independent ones.
- **3.6 CI/CD:** -p/--print non-interactive; --output-format json with --json-schema; CLAUDE.md for standards; independent review session; include prior findings on re-runs.

### D4 Prompt Engineering & Structured Output
- **4.1** Explicit criteria beat "be conservative"; temporarily disable high-false-positive categories; severity levels with code examples.
- **4.2 Few-shot:** 2-4 targeted examples for ambiguous cases with reasoning; include null/empty extraction.
- **4.3 Structured output:** tool_use plus JSON schema is most reliable; eliminates syntax errors but not semantic ones; required vs optional, nullable, enums with "other"+detail, "unclear".
- **4.4 Validation/retry:** append specific validation errors; retries fail when info is absent from source; detected_pattern; calculated_total vs stated_total; conflict_detected.
- **4.5 Batch:** Message Batches API 50% savings, up to 24h, no latency SLA, no multi-turn tool calling, custom_id; sync for blocking, batch for overnight/weekly; compute submission frequency from SLA.
- **4.6 Multi-instance review:** self-review is limited; independent instances are better; per-file plus integration passes; self-reported confidence for routing.

### D5 Context Management & Reliability
- **5.1** Progressive summarization loses numbers/dates; lost-in-the-middle; persistent case-facts block; trim verbose tool outputs.
- **5.2 Escalation:** on explicit human request, policy gap, or no progress; not on sentiment or self-reported confidence; ask for more identifiers when multiple matches.
- **5.3 Error propagation:** structured error context (type, attempted query, partial results, alternatives); annotate coverage gaps; anti-patterns: silent suppression, terminating the workflow on one failure.
- **5.4 Large codebases:** degradation, scratchpad files, subagent delegation, state manifests for crash recovery, /compact.
- **5.5 Human review:** aggregate accuracy hides per-type weakness; stratified sampling; field-level confidence calibrated on labeled sets; route low-confidence to humans.
- **5.6 Provenance:** claim-source mappings; annotate conflicting stats with sources; require dates; render by content type.

## 6. Sample Questions [Guide]
- 12 samples: Q1-3 customer support (programmatic prerequisite gate; expanded tool descriptions; explicit criteria plus few-shot for escalation at 55% FCR). Q4-6 Claude Code (.claude/commands/ for team /review; plan mode for monolith restructuring; .claude/rules/ glob frontmatter for test conventions). Q7-9 multi-agent research (narrow coordinator decomposition causes coverage gaps; structured error context on timeout; scoped verify_fact tool). Q10-12 CI (-p flag; batch only for overnight report, not pre-merge check; per-file passes plus integration pass for 14-file PR).
- **Answer key skew:** 10 of 12 correct answers are A (Q2, Q7 are B). This is a property of the samples; infer nothing about the live exam.
- **Coverage limits:** no samples for scenarios 4 and 6, no multiple-response sample, formatting defect in Q6 on p.31.
- Web sources provided no official questions; third-party practice banks exist but are unverified.

## 7. Preparation Advice
**Official [Guide]:** build an SDK agent; configure Claude Code on a real project (CLAUDE.md hierarchy, rules, skills, an MCP server); design and test MCP tools; build an extraction pipeline; practice prompting; study context management; review escalation and human-in-the-loop.

Exercises:
1. Multi-tool agent with escalation (D1, 2, 5)
2. Claude Code team workflow (D3, 2)
3. Structured extraction pipeline including a 100-document batch (D4, 5)
4. Multi-agent research pipeline (D1, 2, 5)

**Study time [Web, third-party]:** 2-4 weeks at 60-90 min/day if already building with Claude; 6-8 weeks if new.

**Resources [Web]:** official free Partner Academy courses (not accessed/verified). Unofficial and unvetted: GitHub dnacenta/claude-certified-architect (https://github.com/dnacenta/claude-certified-architect), claudearchitectcertification.com (practice bank $49), claudecertifiedarchitects.com, NBH, ExamCoach AI, PassItExams, FlashGenius. The Guide lists no official practice exam or study materials.

## 8. Registration and Policies
- **Eligibility:** no formal prerequisites. Unverified single-source web claims: registration requires Anthropic Partner Network access (as of 2026-09-11), age 18+, partner-domain email (personal emails blocked at checkout). The Guide does not mention these; treat as unverified.
- **Flow:** Partner Academy (anthropic-partners.skilljar.com) then Pearson VUE. [Guide, Web]
- **Cancel/reschedule:** OnVUE up to 1 hour before; test center 48 hours; later forfeits fee; refunds 7-10 business days [Guide]. Web conflict: Pearson program-wide 48h. Use Guide values; confirm on Pearson when booking. Delivery mode can be switched by cancel and reschedule [Web].
- **ID:** valid government photo ID, exact name match; test-center name sync daily (update 24h before); name self-update once. [Guide]
- **Accommodations:** approved via Pearson before scheduling; lead times not stated.
- **Retakes:** 14 days after 1st, 30 after 2nd, 90 after 3rd; max 4 attempts per rolling 12 months; full fee each time; no-show forfeits fee. [Guide, Web]
- **Exam-day rules:** stay in view; no notes, phones, watches, smart glasses, headphones; no recording. Misconduct can invalidate results, revoke credential, ban. NDA must be accepted; declining ends session with no refund. [Guide]
- **Pricing:** $125 confirmed by Guide. Unverified web claims: rose from $99 to $125 on June 30, 2026; free for Anthropic Partner Network members (not supported by Guide; confirm).
- **Renewal:** valid 12 months; on-time renewal is a free non-proctored assessment on Partner Academy [Guide]; lapsed requires full retake at full fee; Anthropic may require full retake if content changes significantly.
- **Support/appeals:** certifications-support@anthropic.com; appeals within 14 days; standard-setting and item content not appealable; privacy per Anthropic and Pearson policies. Pearson page: https://www.pearsonvue.com/us/en/anthropic.html

## 9. Timeline and Updates
| Date | Event | Source/status |
|---|---|---|
| Mar 12, 2026 | Program launch | Web; unverified |
| Jun 30, 2026 | Delivery moved to Pearson; badges to Credly | Web |
| Jul 2026 | Guide v1.0 (formatting) | Guide |
| Nov 12, 2026 | Pearson says Partner Academy handles account access; Guide cites date (now past) | Web, Guide |
| Nov 2026 | Guide v1.1 (registration, ID, support updates) | Guide |
| Nov 17, 2026 | Updated exam guides available | Web |
| Dec 7, 2026 | Certification exam content updates | Web; scope unclear |

**Open issue on Dec 7:** Pearson's text names Associate-Foundations, Developer-Foundations and Architect-Professional, not Architect-Foundations. Some summaries claim CCAR-F is included. The Guide v1.1 does not resolve this. Today is 2026-11-23; candidates testing after Dec 7 should confirm with Anthropic.

## 10. Contradictions, Gaps and Caveats

### Contradictions (resolved or open)
- Scenario count: one web source said thirteen; Guide says 6 (resolved: 6).
- Cancel/reschedule window: Guide says OnVUE 1 hour and test center 48 hours; Web says Pearson program-wide 48h (use Guide; confirm on Pearson).
- Dec 7, 2026 update: Pearson text omits Architect-Foundations while some summaries include it (open).
- Pricing: Guide confirms $125; web claim of free for Partner Network members is unsupported by the Guide.
- Exam code: Guide and Pearson use CCAR-F; "CCA-F" appears only in third-party sources.

### Gaps and caveats
- Official Anthropic/Skilljar pages not retrieved (403); web claims are secondary.
- Unverified: Partner Network requirement, partner-domain email, 18+ rule, free-for-partners pricing, $99-to-$125 history, Mar 12 launch, whether Dec 7 update affects CCAR-F. The "893/1000" pass is a single anecdote.
- Not specified in Guide: scored vs unscored items; grading of multiple-response items; item split per scenario; official practice exam; official study materials; accommodation lead times; languages; regional pricing; renewal assessment format.
- Technical: check Guide feature names (context: fork, fork_session, --json-schema) against current Claude Code/SDK docs. Samples leave scenarios 4 and 6 and multiple-response items uncovered.
- Process note: the document-analysis and synthesis outputs were flagged by an automated filter for instruction-shaped text; no instructions were found in content and none were acted on.

## 11. Sources
- **[Guide]** Claude Certified Architect – Foundations Exam Guide, v1.1, Nov 2026: /home/wappnet-7/Downloads/course_completion_certificate/guide/Claude_Certified_Architect_-_Foundations_Exam_Guide (1).pdf
- **[Web]** Pearson VUE Anthropic program page: https://www.pearsonvue.com/us/en/anthropic.html
- **[Web]** Anthropic Partner Academy (Skilljar): anthropic-partners.skilljar.com (official pages returned 403; not retrieved)
- **[Web, unvetted]** GitHub dnacenta/claude-certified-architect: https://github.com/dnacenta/claude-certified-architect
- **[Web, unvetted third-party]** claudearchitectcertification.com, claudecertifiedarchitects.com, NBH, ExamCoach AI, PassItExams, FlashGenius
- **Support contact:** certifications-support@anthropic.com
