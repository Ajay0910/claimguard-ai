## 2026-09-17T18:22:30Z
You are explorer_m2_charts (teamwork_preview_explorer).
Your working directory is: c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\explorer_m2_charts
Your task: Investigate and design the technical specification for Feature 6 (Executive KPI Cards with sparklines) and Feature 7 (DashboardCharts: interactive SVG/CSS Status Donut, Financial Waterfall, and Rule Conflict Bar).

MANDATORY INPUTS TO READ:
1. c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\ORIGINAL_REQUEST.md (Authoritative user requirements)
2. c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\orchestrator_2\PROJECT.md (Project specification)
3. Existing code in c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\src\components\common\MetricCard.jsx, src\services\api.js, src\services\mockData.js, tailwind.config.js

SCOPE & RESPONSIBILITIES:
- Design the 4 Executive KPI Cards:
  * Total Recovered Amount (with INR currency symbol, sparkline trend curve, variance pill +14.2%, recovery velocity)
  * Claims Under Audit / Flagged (amber/rose badges, discrepancy volume)
  * Total Processed Claims (volume count, throughput rate)
  * Disallowance Rate (%) (percentage metric, benchmark target pill)
- Design `src/components/dashboard/DashboardCharts.jsx`:
  * Interactive Status Distribution Donut Chart: Pure React/SVG donut chart showing Approved, Flagged, Under Review, Disallowed proportions with hover slice expansion, center total count label, interactive tooltip, and status legend.
  * Financial Recovery Waterfall Chart: SVG/CSS waterfall visualizing Billed Amount -> Insurer Approved -> Disallowed -> Disputed/Recoverable with medical color coding.
  * Rule Conflict Frequency Bar Chart: Top violated statutory rules (e.g., Clause 4.2 Room Rent, Proportionate Deduction, Tele-consultation exclusion, Consumables) with conflict count and percentage progress bars.
- Ensure all charts are pure React + SVG/Tailwind (no heavy external chart libraries needed, lightweight, zero runtime failure risk, perfectly responsive).
- Provide complete JSX code templates, SVG geometry math (stroke-dasharray / stroke-dashoffset formulas), and prop types.

OUTPUT REQUIREMENTS:
- Write your complete technical blueprint to: c:\Users\krusheek\Desktop\SIH\claimguard-ai\frontend\.agents\explorer_m2_charts\handoff.md
- Use the Handoff Protocol format.
- When done, notify parent via send_message with your findings and path to handoff.md.
