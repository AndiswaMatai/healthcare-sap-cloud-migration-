"""
Generates large-scale synthetic data modelled on SAP IS-H (Industry Solution
for Healthcare) extracts — the SAP module hospital groups use for patient
administration, billing, and clinical material consumption — as it would be
extracted ahead of a migration to an Azure cloud data platform.

Tables modelled (SAP IS-H naming):
  NFAL  — patient case/admission records
  NBSG  — billing line items per case
  NPAT  — patient master (demographics)
  MM    — material/pharmacy consumption per case (from SAP Materials Mgmt)

Volumes are large (500K+ billing line items) to exercise chunked big-data
processing patterns. All data is synthetic.
"""
import csv
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

# ── Scale knobs ──────────────────────────────────────────────────────────────
N_PATIENTS       = 80_000
N_CASES          = 220_000     # admissions/encounters — a patient can have several
N_BILLING_ITEMS  = 520_000     # individual billable line items per case
N_MATERIALS      = 310_000     # pharmacy/material consumption records

FACILITIES = ["Chris Hani Baragwanath", "Groote Schuur", "Tygerberg", "Steve Biko Academic",
              "Charlotte Maxeke", "Universitas", "Frere Hospital"]
PAYER_CATEGORIES = ["Medical Aid", "Private/Self-Pay", "State/Uninsured", "Workmans Compensation", "Road Accident Fund"]
CASE_TYPES = ["inpatient", "outpatient", "day_case", "emergency"]
BILLING_CATEGORIES = ["Ward Fee", "Theatre Fee", "Consultation", "Radiology", "Pathology",
                       "Pharmacy", "Physiotherapy", "ICU Fee", "Prosthesis"]
MATERIAL_GROUPS = ["Pharmaceuticals", "Surgical Consumables", "Implants", "Dressings", "IV Fluids"]

start_date = datetime(2023, 1, 1)
today = datetime(2026, 6, 1)


def _random_dates(n, start, end):
    delta_days = (end - start).days
    offsets = rng.integers(0, delta_days, size=n)
    return [start + timedelta(days=int(o)) for o in offsets]


# ── Patient master (NPAT-style) ─────────────────────────────────────────────
print("Generating patient master (NPAT)...")
patient_ids = [f"PAT{str(i).zfill(8)}" for i in range(1, N_PATIENTS + 1)]
patients = pd.DataFrame({
    "PATNR": patient_ids,
    "GESCH": rng.choice(["1", "2", "9"], N_PATIENTS, p=[0.48, 0.48, 0.04]),   # SAP gender codes
    "GBDAT": [d.strftime("%Y%m%d") for d in _random_dates(N_PATIENTS, datetime(1935,1,1), datetime(2024,1,1))],
    "PAYER_CATEGORY": rng.choice(PAYER_CATEGORIES, N_PATIENTS, p=[0.35, 0.10, 0.40, 0.08, 0.07]),
    "PROVINCE": rng.choice(["Gauteng", "Western Cape", "KwaZulu-Natal", "Eastern Cape", "Free State"], N_PATIENTS),
})
patients.to_csv(RAW / "sap_npat_patients.csv", index=False)

# ── Patient cases / admissions (NFAL-style) ─────────────────────────────────
print(f"Generating {N_CASES:,} patient cases (NFAL)...")
case_patient_idx = rng.integers(0, N_PATIENTS, N_CASES)
case_patients = np.array(patient_ids)[case_patient_idx]
admit_dates = _random_dates(N_CASES, start_date, today - timedelta(days=1))
case_type = rng.choice(CASE_TYPES, N_CASES, p=[0.30, 0.45, 0.15, 0.10])
los_days = np.where(case_type == "inpatient", rng.integers(1, 21, N_CASES),
            np.where(case_type == "day_case", 0, rng.integers(0, 1, N_CASES)))
discharge_dates = [a + timedelta(days=int(l)) for a, l in zip(admit_dates, los_days)]

cases = pd.DataFrame({
    "FALNR": [f"CASE{str(i).zfill(9)}" for i in range(1, N_CASES + 1)],
    "PATNR": case_patients,
    "EAUFNR_FACILITY": rng.choice(FACILITIES, N_CASES),
    "CASE_TYPE": case_type,
    "AUFNDT": [d.strftime("%Y%m%d") for d in admit_dates],
    "ENTLDT": [d.strftime("%Y%m%d") for d in discharge_dates],
    "LOS_DAYS": los_days,
})
# Inject ~0.4% data quality issues: missing facility, discharge before admission
n_dirty = int(N_CASES * 0.004)
dirty_idx = rng.choice(N_CASES, n_dirty, replace=False)
cases.loc[dirty_idx[: n_dirty // 2], "EAUFNR_FACILITY"] = ""
bad_dates_idx = dirty_idx[n_dirty // 2:]
cases.loc[bad_dates_idx, "ENTLDT"] = cases.loc[bad_dates_idx, "AUFNDT"].apply(
    lambda d: (datetime.strptime(d, "%Y%m%d") - timedelta(days=5)).strftime("%Y%m%d"))
cases.to_csv(RAW / "sap_nfal_cases.csv", index=False)

# ── Billing line items (NBSG-style) — the big table ─────────────────────────
print(f"Generating {N_BILLING_ITEMS:,} billing line items (NBSG)...")
bill_case_idx = rng.integers(0, N_CASES, N_BILLING_ITEMS)
bill_cases = np.array(cases["FALNR"])[bill_case_idx]
bill_dates = _random_dates(N_BILLING_ITEMS, start_date, today)
bill_category = rng.choice(BILLING_CATEGORIES, N_BILLING_ITEMS)
bill_amount = np.round(rng.gamma(shape=2.0, scale=850, size=N_BILLING_ITEMS) + 50, 2)
bill_status = rng.choice(["billed", "paid", "rejected", "pending"], N_BILLING_ITEMS, p=[0.30, 0.45, 0.10, 0.15])

billing = pd.DataFrame({
    "BELNR": [f"BILL{str(i).zfill(9)}" for i in range(1, N_BILLING_ITEMS + 1)],
    "FALNR": bill_cases,
    "BILLING_CATEGORY": bill_category,
    "BUDAT": [d.strftime("%Y%m%d") for d in bill_dates],
    "DMBTR": bill_amount,
    "STATUS": bill_status,
})
# Inject ~0.3% orphan case references and zero amounts
n_bill_dirty = int(N_BILLING_ITEMS * 0.003)
orphan_idx = rng.choice(N_BILLING_ITEMS, n_bill_dirty // 2, replace=False)
billing.loc[orphan_idx, "FALNR"] = [f"CASE{str(i).zfill(9)}" for i in range(900_000_000, 900_000_000 + len(orphan_idx))]
zero_idx = rng.choice(N_BILLING_ITEMS, n_bill_dirty // 2, replace=False)
billing.loc[zero_idx, "DMBTR"] = 0
billing.to_csv(RAW / "sap_nbsg_billing.csv", index=False)

# ── Material/pharmacy consumption (MM-style) ────────────────────────────────
print(f"Generating {N_MATERIALS:,} material consumption records (MM)...")
mat_case_idx = rng.integers(0, N_CASES, N_MATERIALS)
mat_cases = np.array(cases["FALNR"])[mat_case_idx]
mat_dates = _random_dates(N_MATERIALS, start_date, today)
mat_group = rng.choice(MATERIAL_GROUPS, N_MATERIALS)
mat_qty = rng.integers(1, 20, N_MATERIALS)
mat_unit_cost = np.round(rng.gamma(shape=1.5, scale=120, size=N_MATERIALS) + 10, 2)

materials = pd.DataFrame({
    "MATBELNR": [f"MAT{str(i).zfill(9)}" for i in range(1, N_MATERIALS + 1)],
    "FALNR": mat_cases,
    "MATERIAL_GROUP": mat_group,
    "BUDAT": [d.strftime("%Y%m%d") for d in mat_dates],
    "MENGE": mat_qty,
    "UNIT_COST": mat_unit_cost,
})
materials.to_csv(RAW / "sap_mm_materials.csv", index=False)

total_rows = len(patients) + len(cases) + len(billing) + len(materials)
print(f"\nDone. Total rows generated: {total_rows:,}")
print(f"  patients (NPAT): {len(patients):,}")
print(f"  cases (NFAL): {len(cases):,}")
print(f"  billing items (NBSG): {len(billing):,}")
print(f"  materials (MM): {len(materials):,}")
