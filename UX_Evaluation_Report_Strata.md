# UX Evaluation Report: Strata | Modernization Intelligence

*Prepared as an independent UX/HCI review of a 15-page Streamlit analytics platform, based on a complete content audit (`ux_audit_dashboard_strata.md`). All findings are traced to specific pages, components, or code references documented in the audit.*

---

## Executive Summary

Strata is an ambitious piece of engineering. Across fifteen pages it takes a legacy PHP codebase and produces AST-level metrics, dependency graphs, security audits, ROI-ranked modernization strategies, and machine-readable export artifacts (SARIF, Cypher, Mermaid, JSON). The information architecture — five workflow stages from "Command Center" through "Artifact Center" — mirrors a genuine consulting methodology, and several individual components (the collapsible directory tree with role badges, the redundant color-plus-shape coding on the topology graph, the As-Is/To-Be simulator) show real UX instinct. This is not a project that needs its foundations rebuilt. It needs its seams tightened.

The three most consequential issues are, in order: **(1)** a confirmed crash bug that makes the entire Database Intelligence page unusable (`IndexError` from an off-by-one tab list), which is not a UX nuance but a hard blocker that will be the first thing an examiner hits if they click that nav item; **(2)** a cluster of **navigation-trust failures** — sidebar labels that don't match the page titles they lead to, buttons that reference dynamically-instantiated pages instead of the app's registered routes, and dead-end warning screens with no path back — all of which erode the single most important thing a data tool needs, which is the user's confidence that clicking something will do what it says; and **(3)** an **inconsistent severity vocabulary**, where the same underlying concept ("how bad is this file") is expressed as a 3-tier scale in one page, a 4-tier scale with the label "Moderate" in another, and a 4-tier scale with the label "Medium" in a third. None of these are visual polish problems — they are the kind of issues that make a technically excellent tool feel unfinished under examination.

The most impactful quick win is fixing the tab-index crash and, in the same pass, auditing every other `st.switch_page` / dynamic navigation call the same way. This is a few hours of work with an outsized payoff, because a marker/examiner who hits a traceback on page 6 of 15 will discount everything that follows regardless of its quality — this is a well-documented halo effect in usability testing (an early critical failure biases perceived quality of the rest of a system, sometimes called the "first-impression penalty").

On submission readiness: the application is **not yet demo-safe** in its current state (the crash bug alone disqualifies it), but it is close. None of the fixes below require re-architecting Strata's information design — they require internal consistency, a small number of missing affordances (a "back to Dashboard" link, tooltips on first-page KPIs, confirmation on destructive actions), and, for the content-heavy pages, a rethink of *how* dense tabular and graph data is presented rather than *whether* it should be shown at all. A student who addresses the Critical and Major items below has a genuinely strong final-year submission; the Future Roadmap items exist to demonstrate vision in the report, not to be built.

---

## 1. Critical Flaw Analysis

| ID | Flaw | Location in Audit | Severity | Heuristic(s) Violated |
|---|---|---|---|---|
| F01 | `IndexError` crash on Database Intelligence page — 4th tab referenced but not instantiated | `views/database_intelligence.py`, lines 74–78 & 281 | **Critical** | Error Prevention; Visibility of System Status |
| F02 | Sidebar nav label "Legacy Bootstrapper" leads to a page titled "Modernization Factory" | Nav menu vs. Page 14 header | **Major** | Match Between System & Real World; Consistency & Standards |
| F03 | Sidebar nav label "Modernization Risk" leads to a page titled "Security & Risk Audit" — and two buttons on Boundary Intelligence claim to navigate to "Modernization Risk" | Nav menu vs. Page 9 header; Page 10 buttons | **Major** | Match Between System & Real World; Consistency & Standards |
| F04 | Dead-end state: "No active analysis run detected" is plain text with no link back to the Dashboard | Multiple views (Monolith Navigator, Database Intelligence, Global State, etc.) | **Major** | User Control & Freedom; Help Users Recognize/Recover from Errors |
| F05 | In-page navigation buttons instantiate `st.Page()` objects on the fly instead of referencing registered routes | `views/risk_audit.py` 262–263; `views/boundary_intelligence.py` 107–108, 147–148 | **Major** | Visibility of System Status; Robustness (technical root cause, UX symptom is broken/unstable navigation) |
| F06 | Async synthesis status requires manual, repeated clicking of "Refresh Status" — no polling or auto-refresh | `views/artifact_center.py` 63–73 | **Major** | Visibility of System Status |
| F07 | Graphs above 500 nodes are fully suppressed with a warning and no simplified fallback | `views/extraction_simulator.py` 116–118 | **Major** | Flexibility & Efficiency of Use; graceful degradation |
| F08 | Severity/risk taxonomy is inconsistent across pages: 3-tier (High/Medium/Low) vs. 4-tier "Critical/High/**Moderate**/Stable" vs. 4-tier "Critical/High/**Medium**/Low" | Page 2 (Structural Complexity) vs. Page 9 KPI strip vs. Page 8 Era Signals table | **Major** | Consistency & Standards |
| F09 | The five core KPIs on the very first page a user sees have zero help text or tooltips | Page 1, System Vitality KPI Matrix table | **Major** | Help & Documentation; Recognition Over Recall |
| F10 | The single control that determines what data every page shows (`Active Analysis Run`) is described as "visually collapsed" | Global Sidebar, Global Context Switcher | **Critical** | Visibility of System Status; Signifiers (Norman) |
| F11 | State-changing actions ("Re-Scan", "Sync with Database" — which clears cache) fire immediately with no confirmation | Page 1 controls; Page 15 controls | **Minor–Major** | Error Prevention |
| F12 | Generated diagrams (Mermaid) and query scripts (Cypher) are shown only as raw, copy-only code blocks — never rendered | Page 11 (AI Intelligence Log), Page 12 (To-Be export), Page 13 (Export tab) | **Minor** | Recognition Over Recall; Aesthetic & Minimalist Design |
| F13 | Tab-nesting is extensive (up to 4 tabs on a single page, repeated across ~8 of 15 pages) with no indication of what's inside an unopened tab | Pages 6, 7, 8, 9, 10, 12, 13 | **Minor** | Recognition Over Recall; relates to Hick's Law (choice load) |

### Detailed breakdown

**F01 — The Database Intelligence crash (Critical).** This is not a UX judgment call, it's a functional defect with a UX consequence: the audit is explicit that the tab list is instantiated with three entries while the render logic writes to `tabs[3]`, guaranteeing an `IndexError` the moment the page loads. In Nielsen's terms this is the most severe possible violation of *error prevention* — the system doesn't even reach the point of giving the user a chance to make a mistake, it fails on its own. Practically, this page holds three of the audit's most interesting datasets (CRUD taxonomy, credential/security risk, table ownership) and none of them are reachable. Fix this first; everything else in this report is secondary until it is.

**F02 & F03 — Navigation label drift (Major).** Two of fifteen nav items don't lead where their label implies. This matters more than it sounds: Krug's usability heuristic "don't make me think" rests on the idea that clicking a label should require zero interpretive effort. When a user clicks "Legacy Bootstrapper" and lands on a page titled "Modernization Factory," or clicks a button that explicitly says it navigates to "Modernization Risk" and arrives at a page titled "Security & Risk Audit," the user has to pause and verify they're in the right place — a small tax paid repeatedly across a 15-page tool, and a credibility hit in a graded demo where an examiner is actively testing whether things behave as labeled.

**F04 — Dead-end no-run state (Major).** Multiple pages show the same warning ("No active analysis run detected. Please execute a scan from the Dashboard.") as inert text. This is a textbook violation of Nielsen's "user control and freedom": the system correctly diagnoses the problem but offers the user no lever to resolve it, forcing a manual return to the sidebar tree. Given that Strata has 15 nav items across 5 categories, this is a meaningfully worse recovery path than it needs to be.

**F05 — Fragile dynamic routing (Major, technical root cause).** `st.switch_page(st.Page(...))` re-instantiates a `Page` object at call time rather than referencing the object registered when the app's navigation was configured. Streamlit's routing model expects the *exact same* registered `Page`/path — this is documented, known-fragile behavior. The UX symptom is unpredictable: sometimes a clean switch, sometimes a stale state or hard refresh that resets scroll position and any un-persisted view filters. Intermittent bugs are worse for trust than consistent ones, because the user (or examiner) can't form a reliable mental model of when navigation is safe.

**F06 — Manual-only status polling (Major).** During AI synthesis, the Artifact Center shows a static "please wait" message and requires a manual click to check progress. This directly violates "visibility of system status" — Nielsen's first heuristic, and arguably the one users notice fastest when it's broken, because it makes an actively-working system look frozen or abandoned.

**F07 — Hard graph cutoff with total removal (Major).** At >500 nodes, the interactive graph is replaced entirely by a warning with no diagram at all. For a tool whose entire value proposition is *making a large legacy monolith comprehensible*, losing the visualization exactly when the codebase is large enough to need it most is a serious functional gap, not just an edge case.

**F08 — Severity taxonomy fragmentation (Major).** Page 2 classifies class complexity as High/Medium/Low (3 tiers, >20/>10/else). Page 9's KPI strip counts files as Critical/High/**Moderate**/Stable (4 tiers). Page 8's Era Signals table uses Critical/High/**Medium**/Low (4 tiers, different label for tier 3 and tier 4 than Page 9). A user forming a mental model of "what does Critical mean in this app" is forced to relearn it per page — this is precisely what Nielsen's "consistency and standards" heuristic exists to prevent, and it's an easy, high-value fix because it's a data-labeling issue, not a redesign.

**F09 — No tooltips on first-page KPIs (Major).** The audit records "Help Text / Tooltip: None" for all five System Vitality metrics on the Executive Dashboard — the page every user sees first, and the page that sets the tone for whether the tool feels self-explanatory. "Connectivity: 318" and "Avg Complexity: 4.2" are meaningless to a stakeholder without a modernization background, and this is the one page where that audience is most likely to be looking.

**F10 — Buried global context switcher (Critical).** The "Active Analysis Run" control changes the underlying data for *every single page* in the app, yet its label is described as visually collapsed. This inverts the relationship Norman's concept of *signifiers* calls for: the visual prominence of a control should scale with its consequence. A control this powerful being easy to miss risks a genuinely bad failure mode — a user reviewing data thinking they're looking at the current scan when they're actually looking at a stale or different run.

**F11–F13 (Minor–Major, grouped).** Missing confirmation on state-mutating actions is a standard error-prevention gap, worth fixing but lower stakes since the actions (re-scan, cache clear) are recoverable rather than destructive. Un-rendered Mermaid/Cypher output forces a context-switch to an external tool just to see a diagram the system already generated — a missed opportunity given Streamlit does have community components for this. Heavy tab nesting isn't wrong (tabs are appropriate for mutually exclusive content) but at this frequency, with zero indication of tab contents, it adds real cumulative interaction cost.

---

## 2. Content Representation Redesign

### 2.1 System Vitality KPI Matrix (Page 1)

- **Current approach:** Five flat metric cards (Total Files, Lines of Code, Avg Complexity, Total Classes, Connectivity) as bare numbers with comma formatting, no tooltips, no comparison point.
- **What's suboptimal:** A number with no reference point is not information, it's trivia. "Avg Complexity: 4.2" tells the viewer nothing about whether that's healthy or alarming, and there's nowhere to find out without leaving the page. This also wastes the highest-value real estate in the app (first thing seen) on the lowest-context version of the data.
- **Recommended alternative:** Convert each card to a **summary-then-detail** pattern: keep the large number, but add (a) a one-line semantic judgment driven by threshold logic Strata already computes elsewhere ("Avg Complexity: 4.2 — *Healthy*" in green, vs. "*Elevated*" in amber), and (b) a native `st.metric` `help` tooltip explaining the metric in one sentence, and, where a prior scan exists, a delta indicator (`st.metric` supports this natively) so re-scans show trend, not just a fresh snapshot. This costs almost nothing to implement — Streamlit's `st.metric` already accepts `delta` and `help` as first-class arguments.
- **Cognitive rationale:** Pre-attentive processing research (Healey & Enns) shows color and size differences are perceived in under 250ms, before conscious attention — a colored semantic label lets a stakeholder scan five KPIs and know "which of these need my attention" almost instantly, versus reading and mentally evaluating five raw numbers (recall-heavy, System-2 thinking). This is also Shneiderman's "overview first" principle from the Visual Information-Seeking Mantra — the Dashboard's job is overview, and it should communicate meaning, not just magnitude.

### 2.2 File-Level Risk Matrix (Page 9, Tab 1)

- **Current approach:** A single wide dataframe with twelve columns — File Name, Overall File Risk, Maintainability Index, Cyclomatic Complexity, Max Nesting Depth, Max Method LOC, Fan-Out, Security Sinks, Global Accesses, Domain Archetype, Test Coverage, Semantic Multiplier.
- **What's suboptimal:** Twelve columns forces horizontal scrolling or column-hiding on anything but an ultrawide monitor, and — more importantly — it flattens metrics that belong to different mental categories (complexity metrics, security metrics, and a maintainability composite are all given equal visual weight side-by-side). This is a Gestalt problem as much as a scanning problem: nothing in the layout signals which columns are *related*.
- **Recommended alternative:** Split into a **two-tier disclosure**: a compact primary table with File, Overall Risk (as a colored badge, not text), Maintainability Index (as an inline mini progress bar — the audit shows this pattern is already used elsewhere in the app, so it's consistent with existing conventions), and Test Coverage. Clicking a row (or an expander per row) reveals the remaining eight metrics **grouped into labeled clusters** — "Complexity" (Cyclomatic Complexity, Nesting Depth, Method LOC), "Coupling" (Fan-Out, Global Accesses), "Security" (Security Sinks), "Context" (Domain Archetype, Semantic Multiplier). A small-multiples strip of sparkline-style bars per cluster, rather than raw numbers, lets a reviewer compare files at a glance.
- **Cognitive rationale:** This directly applies Gestalt *proximity* and *common region* — grouping related metrics with whitespace/borders signals relatedness without requiring the user to already know the domain. It also respects visual working memory limits (commonly cited as roughly 3–4 chunks, per Cowan's revision of Miller's 7±2): twelve ungrouped columns exceed that; four labeled clusters do not. Tufte's data-ink ratio argument supports the progress-bar and badge substitution — a bar communicates "how much" faster than reading and comparing multi-digit numbers.

### 2.3 Force-Directed Graphs Used Across the App

- **Current approach:** PyVis force-directed node-link graphs are the default visualization for System Topology, the Extraction Simulator's As-Is Blast Radius and To-Be Ghost Graph, Boundary Intelligence's Shadow IT map, and Strategic Roadmap's Visual Summary — five distinct pages, five different underlying relationships, one visual metaphor.
- **What's suboptimal:** Force-directed layouts are excellent for showing *that* things are connected but poor at showing *direction*, *flow*, or *density* at scale — which is precisely why the app already has to hard-cut them off above 500 nodes (F07). Using the same graph type everywhere also means the user has to re-interpret "what does proximity mean here" on every page, since it means something different in a call-dependency graph than in a blast-radius graph.
- **Recommended alternative:** Match the graph type to the relationship, not to what PyVis makes easiest:
  - **Blast Radius / Ghost Graph (directional, before/after):** a **Sankey diagram** communicates directional flow and relative magnitude far better than a node cloud, and naturally shows "what feeds into what" for the As-Is vs. To-Be comparison.
  - **System Topology at high node counts:** an **adjacency matrix** (rows/columns = files, cells shaded by connection strength) scales far better visually than a node-link diagram once density crosses a threshold — this is a well-established finding (Ghoniem, Fekete & Castagliola's readability study found matrix representations outperform node-link diagrams for larger, denser graphs) and would directly solve F07 instead of just hiding the problem: offer a toggle between "Graph view" (below the node threshold) and "Matrix view" (above it) rather than nothing at all.
  - **Bounded Contexts / directory clustering:** a **treemap or circle-packing** view represents containment hierarchies (files within domains within the monolith) more intuitively than a force graph, since nesting is a spatial relationship a treemap shows directly.
- **Cognitive rationale:** This is Shneiderman's "the right representation for the task" principle in the Visual Information-Seeking Mantra, and it's the difference between a chart *looking* impressive and a chart being *readable*. It also converts F07 from a hard limitation into a designed feature (a matrix view that scales), which is a stronger thing to say in a project report than "we suppress the graph past 500 nodes."

### 2.4 Cross-Page Severity Taxonomy

- **Current approach:** Each page independently defines its own severity tiers and colors (see F08).
- **What's suboptimal:** Beyond the consistency violation itself, this means color can't be trusted as a signifier — red on Page 8 and red on Page 9 may not mean the same threshold, which quietly undermines the pre-attentive scanning benefit color is supposed to provide.
- **Recommended alternative:** Define one shared severity enum and color/token map (e.g., a `severity.py` constants module or, given the app already injects custom CSS, a small set of CSS custom properties like `--sev-critical`, `--sev-high`, `--sev-medium`, `--sev-low`) and use it everywhere risk, complexity, or quality is expressed. Render every instance as the same badge component.
- **Cognitive rationale:** Consistency is what allows *recognition over recall* to function at all — a user only benefits from "red means critical" if red reliably means critical across all fifteen pages.

### 2.5 Generated Diagrams and Scripts (Mermaid, Cypher, JSON)

- **Current approach:** Mermaid flowcharts, Neo4j Cypher scripts, and AI metadata chunks are presented as copyable raw text/code blocks with a download button.
- **What's suboptimal:** The system has already done the hard work of generating a diagram description, then hands the user a wall of syntax instead of the diagram itself, requiring a trip to an external Mermaid renderer to see what was actually generated.
- **Recommended alternative:** Render Mermaid inline using a community Streamlit component (`streamlit-mermaid` or an HTML component via `st.components.v1.html` embedding Mermaid.js) with the raw code available behind a small "view source" expander for users who do want to copy it elsewhere — best of both, and it's a low-effort addition given the app already uses custom HTML rendering elsewhere (the directory tree).
- **Cognitive rationale:** Recognition over recall again — a rendered diagram is recognized in one glance; a code block requires the user to mentally execute the syntax to imagine the shape, which most non-developer stakeholders (the audience this tool's "Executive" framing implies) will not do.

---

## 3. Prioritized Recommendations

### Quick Wins (achievable in a day or two)

- **Fix the tab IndexError** on Database Intelligence — either restore the fourth tab/render logic or remove the dead `tabs[3]` write. This single fix unblocks three whole feature sets.
- **Align every nav label with its destination page's `st.title()`** — rename Page 14's header to "Legacy Bootstrapper" (or rename the nav item to "Modernization Factory"), and do the same for Page 9/"Modernization Risk". Also update the two buttons on Boundary Intelligence to say the same thing the destination page says.
- **Add tooltips to all five Page 1 KPIs** using `st.metric(..., help="...")` — e.g., for Avg Complexity: *"Average cyclomatic complexity per method. Under 5 is generally maintainable; above 10 suggests refactor candidates."*
- **Add a "← Back to Dashboard" button** (`st.page_link`, referencing the real registered page) directly under every "No active analysis run detected" warning.
- **Replace every dynamically-instantiated `st.switch_page(st.Page(...))` call** with a reference to the `Page` object registered in `app.py`'s navigation config.
- **Standardize severity labels and colors** into one shared mapping used everywhere "Critical/High/Medium/Low" (recommend settling on this exact 4-tier set, since it already appears twice) is shown.
- **Add a lightweight confirmation** (`st.dialog`, already used for the User Guide, so the pattern exists in-app) before "Re-Scan" and "Sync with Database."

### Before Submission (worth doing for the final build)

- **Auto-refresh the synthesis status view** instead of requiring manual clicks — poll on a timer and re-render, with a step indicator ("Step 2 of 3: Synthesizing Findings…") instead of a single static spinner message.
- **Add a matrix-view fallback** for graphs exceeding 500 nodes, rather than removing the visualization outright (see 2.3).
- **Restructure the 12-column Risk Matrix** into the grouped/expandable card pattern described in 2.2.
- **Render Mermaid diagrams inline** rather than as copy-only code (see 2.5).
- **Add a filter/search box to the directory tree** on Layered Structure — at 245 files, manual expand-all is a real Fitts's-Law/interaction-cost problem.
- **Add a sample/demo dataset option** on the Dashboard so a grader can explore the full app without first sourcing and scanning a real legacy codebase — this alone materially de-risks the live demo.

### Future Roadmap (beyond project scope, demonstrates vision)

- A formal design-token system (shared CSS variables for color/severity/spacing) documented as a mini design system, replacing the current per-page custom CSS.
- A persistent, searchable in-app glossary panel (WMC, LCOM, FQN, Isolation Score, etc.) instead of per-page "Blueprint Key" expanders with inconsistent default-open states.
- Full WCAG AA accessibility pass — contrast audit on the dark theme, colorblind-safe palette validation for the severity and graph-node color coding, keyboard navigation testing on the custom HTML directory tree.
- Session continuity (remember last-viewed page/tab per project) and personalized "what changed since your last scan" summaries.
- Presentation/export mode that packages the Strategic Roadmap and ROI matrix into a stakeholder-ready slide view, extending the existing Artifact Center concept.

---

## 4. Academic Foundations

**Theoretical grounding.** The navigation and consistency findings (F01–F05, F08) draw on **Nielsen's ten usability heuristics**, particularly *visibility of system status*, *match between system and the real world*, *consistency and standards*, and *error prevention*. The buried global-context-switcher finding (F10) applies **Norman's** concept of signifiers and mapping from *The Design of Everyday Things* — the idea that a control's visual prominence should communicate its consequence. The dense-table and taxonomy recommendations lean on **Tufte's** data-ink ratio and small-multiples principles, and on **Gestalt** grouping laws (proximity, similarity, common region) as the mechanism by which visual grouping communicates conceptual grouping without requiring prior domain knowledge. The overview-first structure recommended for graphs and KPIs is **Shneiderman's** Visual Information-Seeking Mantra ("overview first, zoom and filter, then details on demand") — directly applicable since Strata's five-stage workflow is already, structurally, an overview-to-detail pipeline; the content within each page just doesn't always follow that same logic locally. **Krug's** "Don't Make Me Think" underpins the navigation-trust critique: self-evident labeling is treated as the baseline, not a nice-to-have. The graph-representation recommendation cites **Ghoniem, Fekete & Castagliola's** empirical readability comparison of node-link vs. matrix representations, which found matrix views outperform node-link diagrams as graphs grow larger and denser — directly relevant to Strata's own 500-node cutoff. Working-memory limits are referenced via **Miller's** 7±2 and **Cowan's** narrower revision (roughly 4 chunks), used to justify the recommended grouping of the twelve-column risk table into four clusters.

**Comparative examples.** For KPI presentation with semantic thresholds and trend deltas, look at how **Grafana** and **Datadog** dashboards pair a raw metric with a colored health state and sparkline rather than a bare number. For codebase-health visualization specifically — the closest domain match to Strata — **CodeScene** is worth studying directly: it visualizes legacy-system "hotspots" and technical debt trends using color-coded complexity over time, which is conceptually adjacent to Strata's Modernization Risk and Legacy PHP Intelligence pages. For progressive disclosure of dense, related data, look at how **Notion** handles toggle lists and inline databases — properties are grouped and collapsed by category rather than shown as one flat wide table, which is exactly the pattern recommended for the Risk Matrix. For large network visualization at scale, **Neo4j Bloom** and **Kumu.io** both offer clustering/aggregation views specifically because raw force-directed layouts become unreadable past a few hundred nodes — validating the matrix/cluster fallback recommendation over Strata's current hard cutoff.

**Trade-off discussion.** Some of these recommendations are genuinely constrained by Streamlit. Streamlit's rerun-on-interaction model makes true partial-page updates (e.g., live polling without a full page flash) harder than in a SPA framework — the auto-refresh recommendation is achievable but will feel less smooth than a native web app's polling, and that's a reasonable, disclosable limitation to note in a project report rather than a flaw to apologize for. Native Mermaid rendering isn't built into Streamlit and requires either a community component or an HTML/JS embed — both workable, but worth flagging as "third-party dependency" risk in a final-year project where installation reproducibility matters for grading. Conversely, several of the highest-value fixes here (routing consistency, label alignment, tooltips, confirmation dialogs, severity token unification) are pure Streamlit-native fixes with no framework fighting required — which is exactly why they belong in "Quick Wins" rather than "Future Roadmap."

---

## 5. Validation Strategy

**Heuristic evaluation.** Beyond this report, the student can run a formal heuristic evaluation pass: score each of the 15 pages 0–4 against Nielsen's ten heuristics (0 = not a problem, 4 = usability catastrophe), ideally with 2–3 evaluators independently, then average. This produces a defensible, citable severity table for the project report and gives a natural "before/after" comparison once fixes are applied — re-scoring after implementing the Quick Wins should show a measurable drop in average severity, which is strong evidence for a report.

**Usability testing tasks.** A short moderated session (5 participants is sufficient per Nielsen's own research on diminishing returns past that point) with tasks such as:
- *"Starting from the Dashboard, find every file with Critical risk severity."* — tests whether the unified severity taxonomy is actually understood consistently.
- *"Run an extraction simulation on a file of your choice and decide whether it's safe to extract."* — tests jargon comprehension (Blast Radius, Test Coverage threshold, Isolation Score) and whether the KPIs alone communicate a go/no-go decision.
- *"The app tells you there's no active analysis run. Get it working again."* — directly tests the F04 dead-end fix.
- *"Find where you'd download a report to send to a colleague."* — tests findability of the Artifact Center through the 5-category nav tree.

Track **task success rate**, **time on task**, and **error/backtrack count** (how many times a participant clicked the wrong nav item or had to retrace steps) as the core metrics.

**System Usability Scale (SUS).** A 10-item, 5-point Likert questionnaire (Brooke, 1996) administered after the tasks gives a single comparable score, with 68 as the widely-cited industry-average benchmark — useful as a target to state explicitly in the report ("aimed for and achieved a SUS score above X"). Running it once before the Quick Wins and once after gives a quantified, defensible improvement claim, which is exactly the kind of measurable outcome a final-year examiner will want to see rather than a purely qualitative "it feels better now."

---

*All severity ratings and recommendations above are grounded directly in the audit's documented behavior and in established HCI literature, with the aim of maximizing both the usability of the submitted application and the academic strength of the accompanying project report.*
