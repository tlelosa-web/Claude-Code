# Test Procedures and Results (FAT/SAT/UAT)
**Project:** Eskom GIT Enterprise Historian Licence, Maintenance & Support (ITT E2142CXMWPR)
**Owner:** Beta - OT Integration Specialist
**Date:** 2026-03-13
**Status:** Final Draft

## 1. Introduction
This document outlines the testing framework for the Enterprise Historian integration covering Factory Acceptance Testing (FAT), Site Acceptance Testing (SAT), and User Acceptance Testing (UAT).

## 2. Factory Acceptance Testing (FAT)
### 2.1 Objective
Validate system build, connector configurations, and data ingestion logic in a controlled lab environment prior to site deployment.

### 2.2 Procedures
- **TC-FAT-01: Connector Initialization:** Verify all OPC UA/DA, MQTT, and Modbus/TCP driver services start correctly up to a simulated controller.
- **TC-FAT-02: Tag Simulation & Ingestion:** Inject simulated data mimicking Eskom KKS structures. Verify data appears in the Historian without errors.
- **TC-FAT-03: Store and Forward:** Disrupt network connection to historian; verify edge buffering. Restore connection and verify backfill.

## 3. Site Acceptance Testing (SAT)
### 3.1 Objective
Validate system integration with live plant networks, confirming end-to-end data flow under actual operational conditions.

### 3.2 Procedures
- **TC-SAT-01: Network Connectivity:** Verify bi-directional (or appropriate uni-directional) network flow from plant edge devices to Tier 1 Historian through the DMZ.
- **TC-SAT-02: Live Data Validation:** Map 5% of production tags. Validate 1-to-1 match between HMI values and Historian trend displays.
- **TC-SAT-03: Performance Benchmarking:** Measure system resource utilization (CPU, RAM, Disk I/O) on Data Collectors to ensure it remains below 50% under load.

## 4. User Acceptance Testing (UAT)
### 4.1 Objective
Formal sign-off by Eskom business users ensuring the system meets functional requirements (reporting, dashboarding, query performance).

### 4.2 Procedures
- **TC-UAT-01: Client Access:** Verify Eskom users can authenticate via Active Directory and access Historian client tools.
- **TC-UAT-02: Query Performance:** Execute 30-day tag trend query for 100 tags. Expectation: Returns in < 5 seconds.
- **TC-UAT-03: Data Quality:** Verify exception and compression rules are yielding expected data footprint while retaining operational fidelity.

## 5. Traceability and Sign-off
All test cases must be mapped to Annexure N specifications. Test results will be appended to the Quality Control Plan (QCP) Evidence Pack managed by the Quality Manager (Golf).
