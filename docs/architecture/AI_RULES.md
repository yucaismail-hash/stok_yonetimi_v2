# Stokonomi AI Rules

These rules consolidate the binding AI constraints in Documents 05–07. They do not replace the architecture specification.

| Rule ID | Binding rule | Source |
|---|---|---|
| AI-001 | AI Intelligence may use only validated analysis results. | Documents 05, 07 (SYS-043) |
| AI-002 | Company Memory is company-scoped and must not be shared between companies. | Documents 05, 06 |
| AI-003 | Pattern Memory is scoped to the relevant SKU and is independent from Company Memory. | Documents 05, 06 |
| AI-004 | Decision Intelligence is the only official producer of business decisions. | Documents 01, 05, 07 |
| AI-005 | A Recommendation Engine may communicate recommendations but cannot independently create a decision. | Documents 05, 07 |
| AI-006 | Explainability may explain a decision but cannot alter it. | Documents 05, 07 |
| AI-007 | Narrative content may communicate a decision but cannot change business logic or deterministic analytical outputs. | Documents 05, 07 |
| AI-008 | AI may not start execution. | Documents 05, 07 |
| AI-009 | AI may not invoke analytical capabilities directly. | Documents 05, 07 |
| AI-010 | AI may not modify Operational Data. | Documents 05–07 |
| AI-011 | AI Intelligence may not access repositories directly; persistence ownership must remain outside the AI decision responsibility. | Documents 01, 05, 07 |
| AI-012 | An AI Artifact may be created only after a completed Decision. | Documents 05, 07 (SYS-044) |
| AI-013 | Knowledge must be validated, versioned, traceable, and auditable. | Documents 05, 06 |
| AI-014 | Human oversight and auditability are mandatory for AI intelligence outputs and critical actions. | Documents 05, 06 |
| AI-015 | AI does not replace deterministic analysis. | ADR-020 |
| AI-016 | For Standalone Analysis, AI only explains the selected analysis result through an AI Explanation Artifact. | ADR-020 |
| AI-017 | Decision Intelligence is prohibited in Standalone Analysis. | ADR-020 |
| AI-018 | Decision Intelligence is required to produce the final operational decision of an accepted Business Workflow. | ADR-020 |
| AI-019 | Learning cannot retroactively change a completed deterministic result. | ADR-020 |
| AI-020 | External Intelligence affects analysis only through approved Company Learning, Pattern Intelligence, and AI Parameter Optimizer boundaries. | ADR-020 |
| AI-021 | AI Artifact type depends on Product Level: analysis explanation for Standalone Analysis and final operational-plan explanation for Business Workflow. | ADR-020 |
| AI-022 | Missing optional data invokes graceful degradation rather than unnecessary execution failure. | ADR-020 |
| AI-023 | The completed-Decision prerequisite in AI-012 governs final operational-plan AI Artifacts; a Standalone Analysis AI Explanation Artifact is governed by AI-016 and may be created after completion of its selected analysis. | ADR-020 |
| AI-024 | AI and user explanations must not expose internal runtime terminology. | ADR-028 |
| AI-025 | Invalid analytical results must not be explained as successful results. | ADR-027, ADR-028 |
| AI-026 | Technical details must remain separate from user-facing explanations. | ADR-028 |
| AI-027 | User-facing messages must be actionable and honest. | ADR-028 |
| AI-028 | Learning and Decision Intelligence must not consume invalid analytical results. | ADR-027, ADR-028 |

## Enforcement boundary

- AI consumes validated inputs; it does not become an execution, workflow, repository, or operational-data owner.
- Learning and AI Memory remain separate from Operational Data.
- Architecture exceptions are tracked in `DECISION_LOG.md`; an exception does not change these rules without explicit ADR approval.
