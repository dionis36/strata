Let me audit the existing Insight sections across Module B and C before giving the behavioral report.

Searched for "INTERPRETATION"
Searched for "EVIDENCE"
Searched for "RECOMMENDATION"

This is the deep audit needed. Here is the full behavioral specification.

---

## Insight Model: Behavioral Specification

### The Core Problem

The current Insight sections fall into three failure modes across the pages:

**Failure Mode 1 — The Textbook Definition** *(most common)*
The Interpretation describes what the metric *is*, not what it *means for this specific system*. Example from `boundary_intelligence.py`:
> *"Legacy applications often rely on 'Direct File Access' instead of a centralized Router."*

This is a Wikipedia summary. The user already knows what a router is. What they need to know is: *"What does the absence of one mean for __my__ migration?"*

**Failure Mode 2 — The Premature Directive** *(Recommendation)*
Several recommendations give hard operational commands that only belong in a later "Migration Playbook" module. Examples:
> *"Immediately rip out these libraries"*
> *"You must implement an API Gateway (like Kong or Nginx)"*
> *"Do not attempt to automatically migrate or refactor files"*

This terminates the user's thinking. The Insight section's job is to *expand* understanding, not close it.

**Failure Mode 3 — Thin Evidence** *(boundary_intelligence, risk_audit)*
Evidence like `"3 Pure Scripts detected as direct entry points"` is a raw count, not a finding. Evidence must connect the metric to what it *implies* about the system's structure.

---

### The Correct Behavioral Model

Each Insight block should operate on three behavioral principles:

**1. METRIC → Names what was measured and why it was chosen**
Concise. One sentence maximum. Names the specific technical instrument used, not a generic description. It anchors the user: *"This is what the engine looked at."*

**2. INTERPRETATION → Translates the measurement into a finding about THIS system**
This is the most important block. It must:
- Be data-driven: it should change based on actual numbers returned
- Talk about *this* system's structural condition, not about PHP in general
- Build intuition: help the user understand *why* this pattern emerged architecturally

The test: if you could copy-paste this text into a report about a completely different codebase and it would still read correctly → it has failed.

**3. EVIDENCE → 2 to 3 numbered findings derived from actual data**
Each evidence point must express a *finding*, not a count:
- ❌ `"52 critical files detected"`  
- ✅ `"52 files (11.4% of the codebase) exceed the CC threshold of 20 — meaning they cannot be safely extracted without deep manual refactoring"`

Evidence should be specific enough to make an architect nod and say *"Yes, that is a real problem."*

**4. RECOMMENDATION → Opens the next question, does not close the current one**
The recommendation in early discovery modules must act as a **cognitive bridge** — it should direct the user's attention toward patterns they have not looked at yet, either on this page or on a related page. It must **never** prescribe an implementation step (that belongs in Section D: Strategic Advisory).

- ❌ *"You must implement an API Gateway"*
- ✅ *"The distribution of entry points above tells you how users arrive at this application. Before planning a migration, consider: are these entry points clustered around specific features, or scattered arbitrarily? The answer changes your extraction strategy significantly."*

---

### Page-by-Page Assessment Before Fix 

| Page | Interpretation Quality | Evidence Quality | Recommendation Quality |
|---|---|---|---|
| `monolith_navigator.py` | ✅ Strong — talks about this system | ✅ Uses real numbered data points | ✅ Guides to next action correctly |
| `layered_architecture.py` | ✅ Strong — contextual, domain-specific | ✅ Good numbered evidence | ⚠️ Occasionally too prescriptive ("immediate action required") |
| `database_intelligence.py` | ⚠️ Acceptable — partially generic | ✅ Good evidence structure | ✅ Correctly cross-references other tabs |
| `global_state_intelligence.py` | ✅ Strong — highly contextual | ✅ Multi-point evidence | ✅ Excellent cross-tab references |
| `legacy_intelligence.py` | ✅ Strong | ✅ Good | ✅ Correctly bridges to Pattern tab |
| `risk_audit.py` | ⚠️ Partially generic | ⚠️ Thin — counts only | ❌ Too prescriptive ("do not attempt") |
| `boundary_intelligence.py` | ❌ Generic — textbook definitions | ❌ Raw counts, no implication | ❌ Premature directives |

---

### Page-by-Page Assessment After Fix

Let me read the full current state of each file that needs fixing before making any changes.

Viewed risk_audit.py:1-226
Viewed boundary_intelligence.py:1-129
Viewed layered_architecture.py:115-145
Viewed layered_architecture.py:283-395

I now have a full picture. Let me fix all three files simultaneously — starting with `risk_audit.py`, then `boundary_intelligence.py`, then the few weak instances in `layered_architecture.py`.

Edited risk_audit.py
Edited boundary_intelligence.py

Now fix the two weak instances in `layered_architecture.py` — the "Immediate action required" Recommendation in Circular Dependencies and the over-generic Structural Bottlenecks recommendation:

Edited layered_architecture.py

All weak instances have been corrected across **3 files**, **7 insight blocks** total. Here is a summary of what changed and why:

---

### What Was Fixed

**`risk_audit.py` — 3 blocks rewritten**
| Block | Before | After |
|---|---|---|
| Tab 0 — File Risk | Generic textbook definition of MI/CC | Data-driven: reports exact % of CRITICAL files, quotes SEI industry thresholds, tells user to cross-reference Sinks column |
| Tab 1 — Security | One-line count + "remediation required" | Full breakdown of RCE/SQLi/LFI counts with OWASP class references; Recommendation bridges user to the Matrix tab, not to a remediation prescription |
| Tab 2 — Architectural Rot | "Prioritize PSR-4 first, then inject globals" | Explains *why* global coupling is a hidden constraint, breaks down all 3 defect types by count; Recommendation guides user to the Extraction Profile and asks the strategic question *before* moving to Advisory |

**`boundary_intelligence.py` — 3 blocks rewritten**
| Block | Before | After |
|---|---|---|
| Presentation Coupling | "Fat views are hardest to migrate" (generic) | Explains *why* this system built this way (no MVC layer); Recommendation asks whether fat views are clustered vs. scattered — that question changes the strategy |
| API Surface | Generic definition of "Direct File Access" | Reports exact counts of Pure Scripts, JSON emitters, and Procedural Routers for *this* system; Recommendation asks user to think about active vs. dead entry points |
| Vendor Intelligence | "Cannot be patched, must be replaced" | Reports Composer-managed vs. manually embedded ratio; Recommendation frames the informal dependency strategy as the root cause, not just the symptom |

**`layered_architecture.py` — 2 blocks fixed**
| Block | Before | After |
|---|---|---|
| Structural Bottlenecks | "Extract to shared library or untangle" | Asks *why* the bottleneck accumulated those connections — the answer drives the decomposition strategy |
| Circular Dependencies | "Immediate action required. You must break these loops" | Reframes as a diagnostic question: did these form by necessity or convenience? That determines the correct resolution pattern |


### Summary

The pages to focus on when coding are **`boundary_intelligence.py`** (newly created, all three insight blocks need a full rewrite) and **`risk_audit.py`** (Recommendation blocks are terminating the user's thinking instead of expanding it). The Module B pages (`layered_architecture`, `monolith_navigator`) are the **gold standard** to reference — they have naturally strong Interpretations that talk about this system specifically.

When ready to proceed with the Insight rewrites, I will apply this behavioral model across all affected pages.