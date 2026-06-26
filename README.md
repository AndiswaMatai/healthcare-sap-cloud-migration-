# 🏥 Enterprise SAP IS-H → Azure Lakehouse Migration Platform

![SAP](https://img.shields.io/badge/ERP-SAP-blue?logo=sap)
![Azure](https://img.shields.io/badge/Cloud-Azure-blue?logo=microsoftazure)
![Python](https://img.shields.io/badge/Language-Python-yellow?logo=python)
![Pandas](https://img.shields.io/badge/Library-Pandas-green?logo=pandas)
![Compliance](https://img.shields.io/badge/Domain-Healthcare%20Compliance-red)

---

## 🚀 Overview
A large-scale enterprise migration platform modernising **SAP IS-H (Healthcare Industry Solution)** systems by migrating hospital operational data into an **Azure-ready lakehouse schema**.  
Processes **1.13M+ healthcare records** (patients, admissions, billing, pharmacy) using a **chunked extract → validate → transform** architecture for memory-efficient large-scale processing.

---

## 🧠 Business Context
Healthcare systems must migrate mission-critical datasets under strict compliance (POPIA / HIPAA). Risks include:
- Financial inaccuracies from inconsistent data  
- Dependency of downstream reporting on integrity  
- Zero tolerance for data loss or corruption  

---

## 🎯 Solution Overview
- Controlled chunked extraction of SAP IS-H datasets  
- Validation of clinical + financial business rules  
- Logging of rejected records with full traceability  
- Transformation into standardised cloud-ready schemas  
- Loading into Azure-aligned structures  

---

## 🏗️ Architecture
📡 **SAP IS-H Source** → 🥉 Extract Layer → 🥈 Validation Layer → 🥇 Transformation Layer → 📊 Azure-Ready Layer  

- Extract: Chunked ingestion (50K rows/batch)  
- Validation: Admission consistency, orphan detection, billing integrity  
- Transformation: SAP code mapping, ISO date standardisation, derived metrics  
- Azure Layer: `az_patients`, `az_cases`, `az_billing`, `az_materials`  

---

## 📊 Scale
| Table     | Source Rows | Migrated | Rejected |
|-----------|-------------|----------|----------|
| Patients  | 80,000      | 80,000   | 0        |
| Cases     | 220,000     | 219,120  | 880      |
| Billing   | 520,000     | 516,357  | 3,643    |
| Materials | 310,000     | 308,765  | 1,235    |
| **Total** | **1,130,000** | **1,124,242** | **5,758 (0.51%)** |

⚡ Full pipeline runs in **<40 seconds**.

---

## 🛠️ Tech Stack
Python · Pandas · NumPy · Azure Data Factory · Synapse Analytics · Terraform · GitHub Actions  

---

## 📂 Project Structure
healthcare-sap-cloud-migration/
├── .github/workflows/      # CI/CD: Automated testing & DAB deployment
├── audit/                  # Rejected records & migration stats
├── config/                 # SAP mappings, validation rules, env vars
├── data/                   # Synthetic datasets & migration outputs
├── infrastructure/         # Databricks Asset Bundle (DAB) & IaC
├── reports/                # Migration summaries & Power BI assets
├── scripts/                # Orchestration & utility scripts
├── src/                    # Core PySpark modules
│   ├── __init__.py
│   ├── main.py             # Pipeline orchestrator
│   ├── transformations/    # Silver -> Gold logic
│   ├── utils/              # Spark helpers & logging
│   └── validation/         # Quality rule engine
├── tests/                  # Pytest unit & integration tests
├── Dockerfile              # Containerisation definition
└── README.md               # Project documentation


---

## 💡 Business Impact
- **Data Integrity:** Achieved 99.5% successful migration with <1% rejection rate.  
- **Compliance:** POPIA/HIPAA-aligned validation ensures regulatory readiness.  
- **Auditability:** Full rejection logs + traceable transformations for audit sign-off.  
- **Performance:** Migrated 1.13M records in under 40 seconds, demonstrating scalability.  
- **Risk Reduction:** Structured validation reduced migration risk and ensured downstream reliability.  

---

## 📜 License
MIT — all data is synthetico

 

