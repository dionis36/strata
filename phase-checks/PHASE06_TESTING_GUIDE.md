# 🧪 Phase 6: Automated Testing & Evaluation Playbook

Unlike Phases 1 through 5, Phase 6 _is_ the testing pipeline itself. It automates thousands of manual verification steps by iteratively running the Strata engine against an isolated ground truth.

This guide dictates exactly how to control the laboratory parameters and interpret the results.

---

## 🔬 1. Running the Automated Baseline (The "One Click" Test)

The entire scientific pipeline is exposed directly inside the UI. You do not need the terminal.

1. **Open the Dashboard:** Run `streamlit run frontend/Home.py`
2. **Navigate:** Click on `Experiment Results` in the sidebar.
3. **Trigger:** Click the `▶ Run Experiment Suite` button.

**What to Observe:**

- Within ~10 seconds, the engine will run Phase 2 through Phase 5 multiple times in memory.
- You will see the **Classification Ablation (F1 Score)** charts render natively to the screen.
- You will see the **Ranking Sensitivity (Kendall Tau/Top-k)** line plot showing structural resilience.

---

## 🛠️ 2. Manual Testing: Modifying the "Ground Truth"

To prove the engine works on different codebases, you need to change the "answer key."

1. **Locate:** Open `/evaluation/ground_truth/graph_1_truth.json`
2. **Action:** This file dictates which modules _should_ be extracted (`SAFE_TO_EXTRACT`) and which _must not_ (`DO_NOT_EXTRACT`).
3. **Change it:** Swap some of the strings to match nodes in your current `data/graph_1.json`.
4. **Re-Run:** Click `▶ Run Experiment Suite` in the UI.
5. **Verify:** You will immediately see the F1 Precision/Recall metrics wildly plummet or surge depending on whether the algorithmic engine correctly grouped the nodes you specified in the ground truth file!

---

## 🧪 3. Manual Testing: Shifting the Configuration Bounds

To manually stress-test the heuristics, you can overwrite the baseline parameters.

1. **Locate:** Open `/evaluation/config.yaml`
2. **Action:** Find the `weights.cluster_factors` dictionary.
3. **Change it:** Set `"isolation": 0.90` and `"cohesion": 0.05`. (This tells the engine to completely ignore internal cluster density and radically favor network boundaries).
4. **Re-Run:** Click `▶ Run Experiment Suite` in the UI.
5. **Verify:** Watch the **Sensitivity & Consistency** tracking chart. Did the ranking order completely collapse under the new rigid config? Or did the Top-5 predictions overlap?

---

## 📊 4. Examining Raw Output (JSON Dumps)

If you want to read the raw computational outputs of the automated experiments instead of the Matplotlib charts:

1. Look inside `/evaluation/results/`
2. Open `report.json`
3. You will see the JSON dictionary explicitly tracking:

```json
{
  "ablation_metrics": { ... precision / recall bounds ... },
  "sensitivity_overlaps": { ... decimal limits ... }
}
```

By tweaking the **Config** and the **Ground Truth File**, you can scientifically stress-test any legacy PHP monolith graph processed by Phase 1!
