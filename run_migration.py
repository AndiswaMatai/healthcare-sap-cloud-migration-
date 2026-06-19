"""
Healthcare SAP IS-H → Azure Cloud Migration Pipeline (Big Data)

Migrates 1.1M+ rows of SAP IS-H healthcare data (patient cases, billing,
material consumption) to an Azure-ready cloud schema, using the same
three-phase EXTRACT → VALIDATE → TRANSFORM pattern as a real ERP migration,
but built for scale: every phase processes data in chunks so memory stays
flat regardless of hospital group size.

Run:
    python src/generate_sample_data.py
    python src/run_migration.py
"""
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAW    = Path(__file__).resolve().parent.parent / "data" / "raw"
TARGET = Path(__file__).resolve().parent.parent / "data" / "processed"
TARGET.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 50_000

def now(): return datetime.now(timezone.utc).isoformat()

GENDER_MAP = {"1": "male", "2": "female", "9": "unknown"}

def _sap_date(d):
    try: return datetime.strptime(str(d), "%Y%m%d").strftime("%Y-%m-%d")
    except: return None


# ── Phase 1: EXTRACT + VALIDATE (chunked) ────────────────────────────────────
def extract_validate_patients():
    """Patient master is small enough to load whole, but still demonstrates
    the validation pattern used at scale."""
    df = pd.read_csv(RAW / "sap_npat_patients.csv", dtype=str)
    total = len(df)
    valid = df[df["PATNR"].notna() & (df["PATNR"] != "")]
    rejected = total - len(valid)
    valid.to_csv(TARGET / "_staged_patients.csv", index=False)
    return total, len(valid), rejected


def extract_validate_cases():
    """Chunked validation: reject cases with missing facility or discharge
    date earlier than admission date (a classic SAP IS-H data quality issue
    that must be resolved before cloud migration, not after)."""
    total, valid_count, rejected_count = 0, 0, 0
    first_chunk = True
    valid_case_ids = set()
    for chunk in pd.read_csv(RAW / "sap_nfal_cases.csv", dtype=str, chunksize=CHUNK_SIZE):
        before = len(chunk)
        chunk = chunk[chunk["EAUFNR_FACILITY"].notna() & (chunk["EAUFNR_FACILITY"] != "")]
        admit = pd.to_datetime(chunk["AUFNDT"], format="%Y%m%d", errors="coerce")
        discharge = pd.to_datetime(chunk["ENTLDT"], format="%Y%m%d", errors="coerce")
        chunk = chunk[discharge >= admit]
        rejected_count += before - len(chunk)
        valid_case_ids.update(chunk["FALNR"])
        chunk.to_csv(TARGET / "_staged_cases.csv", mode="w" if first_chunk else "a", header=first_chunk, index=False)
        first_chunk = False
        total += before
        valid_count += len(chunk)
    return total, valid_count, rejected_count, valid_case_ids


def extract_validate_billing(valid_case_ids: set):
    """Rejects orphan case references (billing for a case that doesn't exist
    in the validated case set) and zero/negative amounts."""
    total, valid_count, rejected_count = 0, 0, 0
    first_chunk = True
    for chunk in pd.read_csv(RAW / "sap_nbsg_billing.csv", dtype={"DMBTR": float}, chunksize=CHUNK_SIZE):
        before = len(chunk)
        chunk = chunk[chunk["FALNR"].isin(valid_case_ids)]
        chunk = chunk[chunk["DMBTR"] > 0]
        rejected_count += before - len(chunk)
        chunk.to_csv(TARGET / "_staged_billing.csv", mode="w" if first_chunk else "a", header=first_chunk, index=False)
        first_chunk = False
        total += before
        valid_count += len(chunk)
    return total, valid_count, rejected_count


def extract_validate_materials(valid_case_ids: set):
    total, valid_count, rejected_count = 0, 0, 0
    first_chunk = True
    for chunk in pd.read_csv(RAW / "sap_mm_materials.csv", chunksize=CHUNK_SIZE):
        before = len(chunk)
        chunk = chunk[chunk["FALNR"].isin(valid_case_ids)]
        rejected_count += before - len(chunk)
        chunk.to_csv(TARGET / "_staged_materials.csv", mode="w" if first_chunk else "a", header=first_chunk, index=False)
        first_chunk = False
        total += before
        valid_count += len(chunk)
    return total, valid_count, rejected_count


# ── Phase 2: TRANSFORM (SAP field names -> Azure-friendly cloud schema) ─────
def transform_and_load():
    ts = now()

    patients = pd.read_csv(TARGET / "_staged_patients.csv", dtype=str)
    patients_az = pd.DataFrame({
        "patient_id": patients["PATNR"],
        "gender": patients["GESCH"].map(GENDER_MAP).fillna("unknown"),
        "date_of_birth": patients["GBDAT"].apply(_sap_date),
        "payer_category": patients["PAYER_CATEGORY"],
        "province": patients["PROVINCE"],
        "_migrated_ts": ts,
    })
    patients_az.to_csv(TARGET / "az_patients.csv", index=False)

    cases = pd.read_csv(TARGET / "_staged_cases.csv", dtype=str)
    cases_az = pd.DataFrame({
        "case_id": cases["FALNR"],
        "patient_id": cases["PATNR"],
        "facility": cases["EAUFNR_FACILITY"],
        "case_type": cases["CASE_TYPE"],
        "admission_date": cases["AUFNDT"].apply(_sap_date),
        "discharge_date": cases["ENTLDT"].apply(_sap_date),
        "length_of_stay_days": cases["LOS_DAYS"].astype(int),
        "_migrated_ts": ts,
    })
    cases_az.to_csv(TARGET / "az_cases.csv", index=False)

    # Billing: chunked transform since this is the largest table
    first_chunk = True
    total_billing_value = 0.0
    for chunk in pd.read_csv(TARGET / "_staged_billing.csv", chunksize=CHUNK_SIZE):
        out = pd.DataFrame({
            "billing_id": chunk["BELNR"],
            "case_id": chunk["FALNR"],
            "billing_category": chunk["BILLING_CATEGORY"],
            "billing_date": chunk["BUDAT"].apply(_sap_date),
            "amount": chunk["DMBTR"],
            "status": chunk["STATUS"],
            "_migrated_ts": ts,
        })
        total_billing_value += out["amount"].sum()
        out.to_csv(TARGET / "az_billing.csv", mode="w" if first_chunk else "a", header=first_chunk, index=False)
        first_chunk = False

    materials = pd.read_csv(TARGET / "_staged_materials.csv")
    materials_az = pd.DataFrame({
        "material_record_id": materials["MATBELNR"],
        "case_id": materials["FALNR"],
        "material_group": materials["MATERIAL_GROUP"],
        "consumption_date": materials["BUDAT"].apply(_sap_date),
        "quantity": materials["MENGE"],
        "unit_cost": materials["UNIT_COST"],
        "total_cost": (materials["MENGE"] * materials["UNIT_COST"]).round(2),
        "_migrated_ts": ts,
    })
    materials_az.to_csv(TARGET / "az_materials.csv", index=False)

    return len(patients_az), len(cases_az), total_billing_value, len(materials_az)


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("HEALTHCARE SAP IS-H → AZURE CLOUD MIGRATION (BIG DATA)")
    print("=" * 65)

    print(f"\n{'Entity':<20} {'Source':>9} {'Valid':>9} {'Rejected':>9}")
    print("-" * 65)

    p_total, p_valid, p_rejected = extract_validate_patients()
    print(f"{'Patients (NPAT)':<20} {p_total:>9,} {p_valid:>9,} {p_rejected:>9,}")

    c_total, c_valid, c_rejected, valid_case_ids = extract_validate_cases()
    print(f"{'Cases (NFAL)':<20} {c_total:>9,} {c_valid:>9,} {c_rejected:>9,}")

    b_total, b_valid, b_rejected = extract_validate_billing(valid_case_ids)
    print(f"{'Billing (NBSG)':<20} {b_total:>9,} {b_valid:>9,} {b_rejected:>9,}")

    m_total, m_valid, m_rejected = extract_validate_materials(valid_case_ids)
    print(f"{'Materials (MM)':<20} {m_total:>9,} {m_valid:>9,} {m_rejected:>9,}")

    print("\n[Transform] SAP field names -> Azure cloud schema...")
    n_pat, n_cases, billing_value, n_mat = transform_and_load()
    print(f"   Patients migrated: {n_pat:,}")
    print(f"   Cases migrated: {n_cases:,}")
    print(f"   Billing migrated, total value: R{billing_value:,.2f}")
    print(f"   Material records migrated: {n_mat:,}")

    total_source = p_total + c_total + b_total + m_total
    total_rejected = p_rejected + c_rejected + b_rejected + m_rejected
    print("\n" + "=" * 65)
    print("MIGRATION SUMMARY")
    print("=" * 65)
    print(f"Total source rows:    {total_source:,}")
    print(f"Total rejected:       {total_rejected:,} ({total_rejected/total_source:.2%})")
    print(f"Total migrated:       {total_source - total_rejected:,}")

    # Clean up staging files
    for f in TARGET.glob("_staged_*.csv"):
        f.unlink()


if __name__ == "__main__":
    main()
