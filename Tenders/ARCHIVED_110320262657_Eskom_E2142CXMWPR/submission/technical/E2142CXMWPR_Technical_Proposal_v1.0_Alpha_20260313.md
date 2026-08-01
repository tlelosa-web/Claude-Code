Title: Eskom GIT Enterprise Historian – Technical Proposal (ITT E2142CXMWPR)
Version: v1.0
Owner: Alpha (Solution Architect)
Date: 2026-03-13
Source Working File (authoring): submission\technical\E2142CXMWPR_Technical_Proposal_v1.0_Alpha_20260313.md
Target Deliverables:
 - submission\technical\E2142CXMWPR_Technical_Proposal_v1.0_Alpha_20260313.docx
 - submission\technical\E2142CXMWPR_Technical_Proposal_v1.0_Alpha_20260313.pdf

Document Control
 - Purpose: Provide the technical narrative, architecture, integrations, security, HA/DR, backup/restore, performance sizing, methodology, and compliance mapping aligned to Annexure N and Annexure P (SDL).
 - Audience: Eskom GIT evaluation teams (technical, quality, commercial) and internal reviewers.
 - References: Annexure N (Historic Enterprise scope), Annexure P (SDL), Annexure O (TEC), Annexure M (Costing), Supplier Quality 240-105658000, QCP/ITP and CQP templates.

Executive Summary
 - Solution overview and value proposition.
 - Alignment to Eskom objectives and Annexure N scope.
 - Compliance statement to SDL (Annexure P) with cross-reference to the Compliance Matrix section.
 - Summary of architecture, security, HA/DR, and performance posture.
 - Implementation approach, governance, and support model overview.

Architecture Overview
 - Enterprise Topology:
   - Central Enterprise Historian cluster (primary site) with optional DR site.
   - Site-level data acquisition nodes/collectors and buffering.
   - Data pathways, aggregation, compression, and archival tiers.
 - Logical Components:
   - Data acquisition layer, historian core services, storage layer, analytics/visualization consumers, integration APIs.
 - Deployment Model:
   - Windows Server, SQL components as applicable, Active Directory integration, time synchronization, endpoint hardening baseline.
 - Diagrams:
   - High-level logical architecture.
   - Network zones and trust boundaries (OT/DMZ/IT).
   - HA/DR topology (primary, secondary/DR).
 - Data Flow:
   - Protocol ingress (OPC UA/DA, MQTT, Modbus/TCP), validation, buffering, historian ingestion, egress to consumers.

Integrations
 - OPC UA/DA
   - Data collection strategy, redundancy, security (UA certificates), namespace management, tag governance.
   - Legacy DA bridging and DCOM minimization strategy where applicable.
 - MQTT
   - Broker options (internal/external), topic taxonomy, QoS strategy, retained messages, payload schema/JSON, TLS and client auth.
 - Modbus/TCP
   - Polling strategy, register maps, throughput considerations, error handling, scaling across collectors.
 - Other Interfaces (as required by Annexure N)
   - File drops, REST APIs, historian SDKs, event/condition streams.

Security (AD, PKI/TLS)
 - Identity & Access
   - AD-integrated RBAC, least privilege, service accounts, JIT/JEA where applicable.
 - Network Security
   - Segmentation across OT/DMZ/IT, firewall rulesets, inbound/outbound minimization, bastion access patterns.
 - Cryptography
   - PKI/TLS for all supported protocols and admin channels, certificate lifecycle management, cipher baseline.
 - Hardening & Logging
   - OS and application hardening baselines, secure configuration, central logging and SIEM integration, time sync and NTP sources.
 - Compliance
   - Alignment to Eskom Supplier Quality and security requirements; vulnerability management and patch cadence.

High Availability (HA) and Disaster Recovery (DR)
 - HA Strategy
   - Redundant collectors, clustered historian services, DB redundancy (if applicable), load distribution, failover testing.
 - DR Strategy
   - Secondary site topology, data replication, recovery runbooks, quarterly DR test cadence.
 - RPO/RTO Targets
   - Define performance targets and constraints aligned with Annexure N service expectations.
 - Monitoring
   - Health checks, alerting, SLOs/SLIs, escalation paths to support.

Backup and Restore
 - Scope
   - Configuration, runtime data, historical archives, metadata/catalogs, certificates/keys.
 - Frequency & Retention
   - Full/incremental plans, retention tiers, offsite storage.
 - Procedures
   - Automated backups, integrity checks, documented restore steps with validation.
 - Evidence
   - Test restore cadence and reporting.

Performance Sizing
 - Methodology
   - Tag counts from Asset Plant Breakdowns, update rates, compression, historian write rates, query concurrency profiles.
 - Calculations (Prototype)
   - Ingestion throughput targets, storage footprint forecast (hot/warm/cold), network bandwidth, CPU/RAM profiles per node.
 - Hardware/VM Profiles
   - Recommended server tiers for central/collector roles; baseline OS and storage (IOPS, latency).
 - Benchmarks & Tuning
   - Indexing, compression settings, cache sizing, query optimization.

Implementation Methodology
 - Phases
   - Initiation & discovery; design & HLD/LLD; build & configure; integrate & test (FAT/SAT/UAT); migration; go-live; hypercare.
 - Governance
   - RACI, change control, risk management, quality gates tied to QCP/ITP and CQP.
 - Deliverables
   - HLD/LLD packs, configurations, test reports, training, O&M guides.
 - Schedule
   - WBS milestones and dependencies; see Implementation Schedule artifact.

Compliance Matrix to Annexure N / Annexure P (SDL)
 - Instruction
   - This table traces each requirement to a response and evidence. Definitive SDL (Annexure P) compliance will also be maintained in E2142CXMWPR_SDL_Compliance_v1.0_Alpha_20260313.docx.

| Ref | Requirement (Annexure N/P) | Response Summary | Compliant (Y/N) | Evidence/Section |
| --- | --- | --- | --- | --- |
| N-1 | [Insert scope clause] | [Proposed approach summary] | Y | Architecture Overview |
| N-2 | [Insert performance clause] | [Sizing & tuning summary] | Y | Performance Sizing |
| P-1 | SDL Section [x.y] | [Conform/Alternative/Exception] | Y | SDL Template (Annexure P) |
| P-2 | SDL Section [x.y] | [Conform/Alternative/Exception] | Y/N | Security / HA-DR |

Assumptions & Clarifications
 - Assumptions
   - Scope aligns to Annexure N; deviations to be handled via change control.
   - Station/plant counts and tag estimates per Asset Plant Breakdowns; final licensing to reconcile with Clarification C2.
   - Digital signatures acceptable for forms; fallback to wet-ink + scan if mandated (see C1).
 - Clarifications
   - C1: SHE Acknowledgement signature method — request sent 2026-03-12; assume digital acceptable; fallback to wet-ink + scan.
   - C2: In-scope stations/plants and asset breakdown for licensing counts — pending response.
   - C3: Support hours and SLA targets (24x7?) and maintenance windows — pending response; draft assumes standard 24x7 with agreed windows.

Cross-Checks (TEC and Supplier Evaluation)
 - TEC (Annexure O) Alignment
   - Ensure technical elements and quantities in TEC reflect this architecture and sizing; reconcile any deltas prior to finalization.
 - Supplier Evaluation Pack (Annexure K)
   - Ensure solution narrative and evidence references are consistent with Annexure K responses and scoring drivers.
 - Commercial Consistency
   - Verify Annexure M totals and units correspond to TEC (Annexure O) and scope; update if requirement interpretation changes.

Appendices
 - A: Abbreviations and Glossary.
 - B: Architecture Diagrams (HLD).
 - C: HA/DR Runbooks (summary).
 - D: Backup/Restore Procedures (summary).
 - E: Test Strategy summary (FAT/SAT/UAT).

Packaging & Conversion Notes
 - This markdown file is the working source for content authoring and peer review.
 - On finalization, convert/import into DOCX at:
   submission\technical\E2142CXMWPR_Technical_Proposal_v1.0_Alpha_20260313.docx
 - Produce the submission PDF at:
   submission\technical\E2142CXMWPR_Technical_Proposal_v1.0_Alpha_20260313.pdf
 - Recommended conversion paths:
   - Use Microsoft Word to import this markdown and save as DOCX, then export to PDF.
   - Or use Pandoc locally: pandoc -s -o E2142CXMWPR_Technical_Proposal_v1.0_Alpha_20260313.docx E2142CXMWPR_Technical_Proposal_v1.0_Alpha_20260313.md
     then export to PDF via Word/LibreOffice.

