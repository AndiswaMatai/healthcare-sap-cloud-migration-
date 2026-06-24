# 🏥 Enterprise SAP IS-H → Azure Lakehouse Migration Platform

![Sector](https://img.shields.io/badge/Sector-Healthcare%20%C2%B7%20Big%20Data-8a0000?style=flat)
![CI](https://img.shields.io/badge/CI-passing-0f7a4b?style=flat&logo=githubactions)
![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat&logo=python)

**[← Back to live portfolio](https://andiswamatai.github.io)**

---

## 🚀 Overview

A large-scale enterprise data migration platform that modernises SAP IS-H (Healthcare Industry Solution) systems by migrating hospital operational data into an Azure-ready lakehouse schema.

The platform processes over **1.13 million healthcare records** covering patients, admissions, billing, and pharmacy consumption using a chunked extract → validate → transform architecture designed for memory-efficient large-scale processing.

This system simulates how healthcare organisations safely migrate mission-critical clinical and financial data into cloud environments without compromising data integrity or regulatory compliance.

---

## 🧠 Business Context

Healthcare systems running SAP IS-H manage some of the most sensitive and operationally critical datasets in the enterprise landscape, including:

- Patient demographics and medical records
- Hospital admissions and discharge events
- Billing and insurance claims
- Pharmacy and material consumption

These systems must be migrated carefully due to:

- Strict regulatory and compliance requirements (POPIA / HIPAA-style constraints)
- High risk of financial inaccuracies from data inconsistencies
- Dependency of downstream reporting and revenue systems on data integrity
- Zero tolerance for data loss or corruption during migration
  
---
## Solution Overview 

This platform implements a controlled enterprise migration framework that ensures SAP IS-H data is safely transformed into an Azure Lakehouse schema.

The system:

- Extracts SAP IS-H datasets in controlled chunks
- Validates clinical and financial business rules before migration
- Rejects and logs invalid records with full traceability
- Transforms SAP-specific formats into standardised cloud-ready schemas
- Loads validated datasets into Azure-aligned structures

## SAP IS-H Tables Modelled

| SAP Table | Description | Azure Target |
|---|---|---|
| NPAT | Patient master (demographics, payer category) | `az_patients` |
| NFAL | Patient case / admission record | `az_cases` |
| NBSG | Billing line items per case | `az_billing` |
| MM (Materials Mgmt) | Pharmacy/material consumption per case | `az_materials` |

## Scale

| Table | Source rows | Migrated | Rejected |
|---|---|---|---|
| Patients | 80,000 | 80,000 | 0 |
| Cases | 220,000 | 219,120 | 880 |
| Billing | 520,000 | 516,357 | 3,643 |
| Materials | 310,000 | 308,765 | 1,235 |
| **Total** | **1,130,000** | **1,124,242** | **5,758 (0.51%)** |

Full pipeline (generate + migrate) runs in under 40 seconds.

## Architecture

🏗️ Architecture
📡 SAP IS-H Source System
- NPAT (Patients)
- NFAL (Admissions / Cases)
- NBSG (Billing)
- MM (Materials / Pharmacy)

        ↓

🥉 Extract Layer
- Chunked ingestion (50K rows per batch)
- Memory-efficient processing

        ↓

🥈 Validation Layer
- Admission date consistency checks
- Orphan record detection
- Billing integrity validation
- Negative / invalid value detection

        ↓

🥇 Transformation Layer
- SAP code → business-friendly mapping
- Date standardisation (YYYYMMDD → ISO 8601)
- Derived metrics (length of stay, total cost)

        ↓

📊 Azure-Ready Layer
- az_patients
- az_cases
- az_billing
- az_materials

## Tech stack

Python, pandas with chunked processing (→ Azure Data Factory + Synapse Analytics in production), numpy for vectorised million-row data generation.

## Data Engineering Design

This platform demonstrates enterprise-grade data engineering principles:

- Chunked processing for large-scale datasets (memory-safe ingestion)
- Strict data validation prior to transformation
- Schema standardisation for cloud migration readiness
- Rejection logging for full audit traceability
- Separation of extract, validate, and transform layers

## Business Rule Engine

Key validation rules enforced during migration:

- Discharge date must be after admission date
- All cases must reference valid patients
- Billing records must not contain negative or zero values
- Material consumption must link to valid cases
- Missing facility identifiers flagged as invalid

## Data Governance & Audit Layer

The system ensures full auditability through:

- Rejected record logging with explicit failure reasons
- Separation of valid vs invalid datasets
- Traceable transformation logic per field
- Migration statistics per entity type
```

## Outputs

The platform generates:

- Clean Azure-ready datasets (patients, cases, billing, materials)
- Rejected record audit logs
- Migration summary report
- Data quality statistics

## Business Value

This system enables healthcare organisations to:

- Safely migrate SAP IS-H systems to cloud platforms
- Maintain full data integrity during migration
- Ensure regulatory compliance (POPIA / HIPAA-aligned design)
- Reduce migration risk through structured validation
- Provide full audit traceability of all data movements

## What I'd add next

- Add POPIA/HIPAA-compliant patient identifier pseudonymisation (SHA-256 hash of `PATNR`) before any extract leaves the SHIR VM.
- Replace the local `_sap_date()` transform with ADF Data Flow's `toDate()` expression so the transformation runs at scale in the Azure Data Flow cluster rather than locally.
- Build a Power BI migration cutover dashboard reading the `rejected/` ADLS container so the migration lead can see entity-by-entity readiness and rejection trends before go-live sign-off.

## License

MIT — all data is synthetic.
