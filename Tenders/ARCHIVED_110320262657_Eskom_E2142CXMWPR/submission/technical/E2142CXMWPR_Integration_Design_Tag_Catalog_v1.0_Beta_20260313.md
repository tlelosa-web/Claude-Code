# Integration Design and Tag Catalog
**Project:** Eskom GIT Enterprise Historian Licence, Maintenance & Support (ITT E2142CXMWPR)
**Owner:** Beta - OT Integration Specialist
**Date:** 2026-03-13
**Status:** Final Draft

## 1. Integration Design Architecture
### 1.1 Connector Strategy
- **Primary Protocol:** OPC UA for modern control systems / PLCs.
- **Legacy Systems:** OPC DA via dedicated gateway converters to OPC UA, or direct Modbus/TCP depending on plant capability.
- **Telemetry / Remote Sites:** MQTT with Sparkplug B for low-bandwidth environments.

### 1.2 Data Ingestion Pathway
- Assets -> Edge Gateways / Local Historian -> Tier 1 Historian (Plant Level) -> Enterprise Historian (Tier 2).
- Store and Forward functionality enabled on all edge and intermediate nodes to handle network interruptions.

## 2. Tag Strategy and Naming Convention
### 2.1 Standard Tag Naming
Naming convention aligns with Eskom KKS (Kraftwerk Kennzeichen System) standard.
Format: `[PlantID]_[Unit]_[System]_[Equipment]_[MeasurementType]`
Example: `MED01_U1_CWA_PMP01_FLOW` (Medupi, Unit 1, Cooling Water, Pump 1, Flow Rate)

### 2.2 Compression and Retention Policies
- **Exception Tuning:** Deadbanding applied at the edge to reduce noise (e.g., analog tags deadband set to 0.5% full scale).
- **Compression Tuning:** Swinging door algorithm applied at the Tier 1 Historian.
- **Retention:**
  - High-resolution data (1s/raw): 3 years online.
  - Granular/Aggregated (1min/1hr): Online indefinitely.

## 3. Tag Catalog Overview
*Note: This is a representative breakdown based on initial site asset lists. Full inventory to be validated during execution.*

| Plant | System | Estimated Tag Count | Protocol | Update Rate |
|-------|--------|---------------------|----------|-------------|
| Medupi | Boiler | 15,000 | OPC UA | 1 sec |
| Kusile | Turbine | 12,000 | OPC UA | 1 sec |
| Koeberg | BOP | 20,000 | Modbus/TCP | 5 sec |
| Arnot | Gen | 8,000 | OPC DA | 2 sec |
| **Total** | | **~55,000 (Initial Scope)** | | |

## 4. Risks and Fallbacks
- **Protocol Incompatibilities:** Mitigation through deployment of Kepware or equivalent bridging software.
- **Poor Data Quality:** Implement automated validation tags; set points for stale data alarms.
