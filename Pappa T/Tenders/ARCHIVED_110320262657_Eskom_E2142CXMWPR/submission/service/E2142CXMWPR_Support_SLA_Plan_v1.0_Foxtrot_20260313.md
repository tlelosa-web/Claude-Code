Eskom GIT Enterprise Historian — Support & SLA Plan
Version: v1.0 (2026-03-13)
Owner: Foxtrot (Service Delivery Lead)
Reference: ITT E2142CXMWPR — Aligns to Annexure N (Scope), Annexure P (SDL), Annexure Q (Returnables), NEC3 PSC, Eskom SHE & Quality Specs

1. Purpose and Scope
This plan defines the support and maintenance operating model, service levels, governance, and reporting for the Enterprise Historian solution across in-scope Eskom/GIT plants and systems. It aligns with contractual expectations and internal operational capabilities and integrates with OT/IT processes.

2. Service Model
2.1 Service Hours and Tiers
- Tier 0: Knowledge base and runbooks (self-help), 24x7 access.
- Tier 1 (Service Desk): Business Hours (BH) 08:00–17:00 SAST, Mon–Fri excl. public holidays; optional Extended Hours 06:00–22:00; optional 24x7 for P1/P2.
- Tier 2 (Application/Systems): BH with on-call for P1/P2 out of hours.
- Tier 3 (Vendor/SME): BH with best-effort after-hours by prior arrangement or under 24x7 option.

2.2 Support Channels
- Primary: Service Desk (ticketing portal/email), Phone for P1.
- Secondary: Teams/Collaboration for working sessions, CAB meetings for changes.

2.3 Roles by Tier
- L1: Intake, triage, user comms, basic checks, escalation.
- L2: Historian app/services, Windows/SQL checks, integrations, remediation.
- L3: Product vendor engagement, complex defects, hotfix coordination.

3. Incident, Problem, and Change Management
3.1 Incident Management
- Prioritization:
  - P1 Critical: Total loss of historian in production or safety impact.
  - P2 High: Major degradation, data latency affecting operations KPIs.
  - P3 Medium: Partial loss, non-critical function issues.
  - P4 Low: Service request/minor defect, cosmetic.
- Lifecycle: Log → Triage → Diagnose → Workaround/Restore → Root cause capture → Closure with user confirmation.
- Communications: Initial acknowledgement within SLA; progress updates until restoration; post-incident summary for P1/P2.

3.2 Problem Management
- Trigger: Recurrent incidents, major defects, or significant root cause candidates.
- Activities: Problem record, trend analysis, corrective actions, known error database, RCA with action plan and due dates.
- Target: RCA for P1/P2 within 5 BH days post-restoration, unless vendor dependency extends.

3.3 Change Management
- Process: Request → Impact/Risk → CAB Approval → Schedule → Implement → Validate → Close.
- Windows: Standard maintenance windows coordinated with plant operations; emergency changes allowed under E-CAB for P1/P2.
- Artefacts: Implementation plan, backout plan, validation checklist, comms plan.

4. Escalation Matrix and Communications
4.1 Escalation Paths
- Operational: L1 SD Supervisor → L2 Application Lead → L3 SME Lead → Service Delivery Manager.
- Management: SDM → PM (Echo) → Contracts/Legal (Juliet) for contractual escalations.

4.2 Communications Plan
- P1: Acknowledgement within response target; status updates per cadence; incident channel opened; post-incident report within 2 BH days.
- P2: Acknowledgement and updates at reduced cadence; summary on resolution.
- P3/P4: Standard comms via ticket updates; batch summaries available in MSR.

5. KPIs and SLAs
5.1 Definitions
- Response Time: Time from ticket log to first qualified human response.
- Restore Time: Time to restore service to acceptable functional level (temporary or permanent fix).
- Availability: Percentage of agreed service hours with service available, excluding approved maintenance and exclusions.

5.2 Target Matrix (Baseline; contractual finalization in Annexure O/Contract)
- P1: Response 15 min (24x7 if option), Restore 4 hours, Comms every 30–60 min.
- P2: Response 30 min (BH; 24x7 if option), Restore 8 hours, Comms every 60–120 min.
- P3: Response 4 BH hours, Restore 2 BH days.
- P4: Response 1 BH day, Restore 5 BH days.
- Availability (Production Historian core services): 99.5% during BH; optional 99.9% under 24x7 premium.

5.3 Measurement and Exclusions
- Clock pauses for: Awaiting user, vendor delay beyond reasonable control, approved maintenance windows, force majeure, network/power outages outside scope.
- Measurement sources: Ticketing system timestamps, monitoring alerts, service checks.

6. Operational Level Agreements (OLAs)
- Systems/DB (Charlie): DB backups success ≥ 99%; DB maintenance compliance; OLA Response P1 15 min, P2 30 min (on-call if 24x7 option).
- Network/Security (Delta): Connectivity, firewalls, certificates; change lead times per CAB; OLA Response P1 15 min.
- OT Integration (Beta): Data source connectors, collectors, tag mappings; planned changes coordination; OLA Restore tied to plant windows.

7. Governance and Reporting
- Monthly Service Review (MSR): SLA performance, incidents, problems, changes, capacity, risks.
- Quarterly Service Review (QSR): Trend analysis, improvement plan, roadmap, contract performance.
- Reporting Pack: SLA Dashboard, Incident/Problem log, Change metrics, Availability reports, Compliance items.

8. Tools and Monitoring
- Ticketing: ITIL-compliant tool with priority matrix and SLA timers.
- Monitoring: Service/process monitors, collector health, queue latency, OS/SQL metrics.
- Backups & DR: Daily backups with test restores quarterly; DR runbook; annual DR test.

9. Compliance and Constraints
- Aligns with NEC3 PSC obligations, Eskom SHE Rules, Supplier Quality Spec 240-105658000, Quality Specs 240-109253302/698.
- Changes follow QCP/ITP and CQP controls; safety-critical changes require SHE approval.

10. Resourcing and Feasibility
- Coverage: BH staffed; on-call rota for P1/P2; shift/rota avoids fatigue and meets statutory limits.
- Skills: L2 cross-skilling on historian, Windows, SQL; L3 vendor engagement budgets defined.
- Holiday/Peak: Backfill rules; freeze periods around critical plant operations.

11. Assumptions and Dependencies
- In-scope plants and tag counts per Clarifications 2; 24x7 coverage optional add-on.
- Access to Active Directory, network segments, and required admin rights established.
- CAB cadence and maintenance windows agreed with operations.

12. RACI (Summary)
- Incident Restore: R A (L2), C (L3), I (PM/Quality).
- Problem RCA: R (L2/L3), A (SDM), C (Systems/Network), I (PM).
- Change Implement: R (Change Owner), A (CAB), C (OT/IT Teams), I (Stakeholders).

13. Appendices
- A: Priority-to-SLA Table (detailed).
- B: Escalation Contacts and On-call Rota.
- C: Reporting Templates (KPIs dashboards outline).

End of Document
