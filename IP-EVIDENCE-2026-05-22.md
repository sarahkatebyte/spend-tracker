# Intellectual Property Evidence Document
**Created:** May 22, 2026 — prior to Vellum contractor engagement (begins May 25, 2026)
**Author:** Sarah Kate (sarahkate / sarahkatebyte)
**Purpose:** Timestamped record of independently developed ideas, frameworks, and work product created before any IP assignment agreement was signed.

---

## 1. Context Engineering Framework

Developed independently through use of personal AI assistant (Astrid/Vellum platform) beginning April 2026. Core thesis: the right foundational context (system prompt architecture) doesn't make a model smart — it gives it a method. Recursion applies: each loop of detection makes the system better. Documented and iterated through personal use, journaling, and application development.

Key contributions:
- Context-level learning algorithm at the system level, not user level
- The "detective novels as system prompt" architecture metaphor (Sheep Detectives source, May 22, 2026)
- Context engineering failure taxonomy (hallucination from partial signal — "Nooklyn Property Management" case study, May 22, 2026)

---

## 2. Spend Observability Closed-Loop Architecture

**The core thesis:** Token cost observability should be a runtime primitive, not a point-in-time CLI intervention. The meaningful metric is the delta — how spend changes after an optimization event — not the absolute cost.

First implemented: May 19, 2026 (see git history in this repo).
Tracker operational: May 19, 2026. 481+ snapshots collected independently before trial.

Architecture components developed prior to signing:
- Time-series SQLite collector polling `assistant usage breakdown --group-by call_site`
- Optimization event logging with before/after delta comparison
- 7-day rolling window correction (correct total = latest snapshot, not sum across snapshots)
- Model-to-call-site mapping revealing Opus running on background tasks without overrides
- Delta-as-signal framing: "The money moved. You just can't explain why." — the attribution gap

Key finding developed independently (May 22, 2026):
- Memory Consolidation, Memory Extraction, Memory Retrieval, Filing Agent, Compaction Agent all running on claude-opus-4-6 with no model override
- Estimated ~$52/week in recoverable savings from background task routing alone
- Compaction Agent growing 128% while other call sites drop — unattributed, unflagged

---

## 3. Responsible AI Market Positioning Thesis

Developed May 22, 2026. Core argument: open-source AI platforms with data sovereignty, spend control, and community-owned guardrails have a structural advantage that closed-source players (OpenAI, Anthropic, etc.) cannot replicate without contradicting their own business model.

Key components:
- **Structural conflict of interest argument:** Closed-source revenue depends on token spend. Showing customers how to spend less is against their model. Vellum doesn't have that conflict. That's a moat.
- **"Accidental consumer data protection by design"** positioning
- **Community as guardrails AND marketing:** open-source community self-polices privacy violations and serves as credible third-party advocates
- **The window thesis:** decisions about what AI becomes are being made now, not in 5 years. A 25-person company can stake out unclaimed territory. In 5 years the defaults are locked.
- **Third path framing:** Not "stop AI" (impossible). Not full acceleration (Sam Altman path). Distribute benefit instead of concentrating it.
- **"We don't have to convince anyone we're better. We make it visibly irresponsible to choose the alternative."**

Market sizing developed independently (May 22, 2026):
- TAM: $15-20B annualized LLM API spend (2026)
- SAM: $2.69B LLM observability market (2026) → $9.26B by 2030 at 36.2% CAGR
- SOM: $50-250M ARR at 2-5% SAM capture by 2028-2030
- Asymmetric advantage: SOM expands when cost attribution is native to platform, not bolt-on

---

## 4. Impact-Weighted Vesting / Comp Structure Thesis

Developed independently. Core thesis: standard vesting schedules optimize for retention, not output or impact. The industry conflates tenure with value delivered. A shorter vesting cliff with impact-weighted triggers aligns incentives to actual contribution.

Key formulation:
- **"Tenure is NOT the signal — the impact of the work is."**
- Upfront grant (0.25% immediate vest) acknowledging that trial periods are unpaid value delivery
- 6-month cliff rather than 12-month (contribution is demonstrable before 12 months)
- Impact triggers as an alternative/supplement to time-based cliffs

---

## 5. Mission Statement (May 22, 2026)

*"I want to show people what responsible wealth could look like so they have nothing to say."*

The goal is not fame or credit. The goal is to build a proof of concept — that mission and money are not in conflict, that AI can distribute rather than concentrate power, that responsible development scales — that is so complete it removes the counter-argument entirely.

Work to be done anonymously where possible. Credit is not the point. The world the nephew inherits is the point.

---

## Supporting Evidence

- This git repository: `sarahkatebyte/spend-tracker` (private) — commit history timestamps
- Spend tracker running since May 19, 2026 — 481+ snapshots, 7,214 rows in spend.db
- Streamlit visualization (viz.py) developed May 22, 2026
- Conversation log: Astrid session 2026-05-22T17-34-23 (local Vellum workspace)
- Housing legal strategy, Vellum thesis curriculum, market analysis: all conducted on personal machine

---

*This document was created on personal equipment using personal accounts prior to the start of any Vellum contractor engagement. It is intended as a timestamped record of independently developed intellectual property.*
