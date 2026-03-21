# Phase 4.5 Exit Report: Risk Explainability Engine

## 1. Objective Met

Phase 4.5 successfully transforms Strata from a numbers system into a **decision-support tool**. The system now answers:

> "WHY is this component at risk?"

Every answer is deterministic, rule-based, and backed by concrete evidence.

## 2. Architecture Delivered

### Backend

- `domain/explanation/rules.py` — 8 configurable rules with centralized THRESHOLDS. Zero hardcoded values inside conditions.
- `domain/explanation/reasoner.py` — `RiskReasoner`: evaluates, sorts by weight DESC, caps at 5 explanations.
- `domain/explanation/evidence_builder.py` — `EvidenceBuilder`: graph JSON reader, dependent extractor, file path resolver.
- `domain/explanation/explanation_model.py` — Pydantic contracts (`ExplanationItem`, `ComponentExplanation`).
- `application/services/explanation_service.py` — Stateless orchestrator. No DB writes. On-the-fly computation.

### API

- `GET /explain/{run_id}` — Separate from `/risk/{run_id}`. Returns full structured explanation + evidence per component.

### Frontend

- `2_Risk_Analysis.py` — Slim table (Component | Risk Level | Final Risk | 🔍 Explain).
- `@st.dialog` modal with 3 tabs: **Risk Summary** / **Why Risky** (grouped by category) / **Evidence** (dependents, SCC, file path).

## 3. Design Guarantees

| Guarantee       | Implementation                                            |
| --------------- | --------------------------------------------------------- |
| Deterministic   | Same input → identical ordered output, always             |
| Bounded         | Max 5 explanations per component enforced                 |
| Traceable       | Each explanation maps to a rule name + metric values      |
| Evidence-backed | Dependent components and file path surfaced per component |
| No LLM          | Pure rule evaluation — no external dependencies           |

## 4. Next Steps

System is tagged `v0.6-explainability`. Ready for **Phase 5**.
