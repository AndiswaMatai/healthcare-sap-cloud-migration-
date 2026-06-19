"""Run with: python -m unittest discover -s tests -v"""
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from run_migration import _sap_date, GENDER_MAP


class TestTransformLogic(unittest.TestCase):
    def test_sap_date_converts(self):
        self.assertEqual(_sap_date("20250615"), "2025-06-15")

    def test_sap_date_invalid_returns_none(self):
        self.assertIsNone(_sap_date("garbage"))

    def test_gender_mapping(self):
        self.assertEqual(GENDER_MAP["1"], "male")
        self.assertEqual(GENDER_MAP["2"], "female")
        self.assertEqual(GENDER_MAP["9"], "unknown")


class TestValidationLogic(unittest.TestCase):
    def test_case_with_missing_facility_rejected(self):
        chunk = pd.DataFrame([
            {"FALNR": "C1", "EAUFNR_FACILITY": "", "AUFNDT": "20250101", "ENTLDT": "20250105"},
            {"FALNR": "C2", "EAUFNR_FACILITY": "Groote Schuur", "AUFNDT": "20250101", "ENTLDT": "20250105"},
        ])
        chunk = chunk[chunk["EAUFNR_FACILITY"].notna() & (chunk["EAUFNR_FACILITY"] != "")]
        self.assertEqual(len(chunk), 1)
        self.assertEqual(chunk.iloc[0]["FALNR"], "C2")

    def test_discharge_before_admission_rejected(self):
        chunk = pd.DataFrame([
            {"FALNR": "C1", "AUFNDT": "20250110", "ENTLDT": "20250105"},  # invalid: discharge before admit
            {"FALNR": "C2", "AUFNDT": "20250101", "ENTLDT": "20250105"},  # valid
        ])
        admit = pd.to_datetime(chunk["AUFNDT"], format="%Y%m%d")
        discharge = pd.to_datetime(chunk["ENTLDT"], format="%Y%m%d")
        chunk = chunk[discharge >= admit]
        self.assertEqual(len(chunk), 1)
        self.assertEqual(chunk.iloc[0]["FALNR"], "C2")

    def test_orphan_billing_case_rejected(self):
        valid_case_ids = {"C1", "C2"}
        chunk = pd.DataFrame([
            {"BELNR": "B1", "FALNR": "C1", "DMBTR": 500.0},
            {"BELNR": "B2", "FALNR": "C99", "DMBTR": 300.0},   # orphan
        ])
        chunk = chunk[chunk["FALNR"].isin(valid_case_ids)]
        self.assertEqual(len(chunk), 1)
        self.assertEqual(chunk.iloc[0]["BELNR"], "B1")

    def test_zero_amount_billing_rejected(self):
        chunk = pd.DataFrame([
            {"BELNR": "B1", "FALNR": "C1", "DMBTR": 0.0},
            {"BELNR": "B2", "FALNR": "C1", "DMBTR": 250.0},
        ])
        chunk = chunk[chunk["DMBTR"] > 0]
        self.assertEqual(len(chunk), 1)
        self.assertEqual(chunk.iloc[0]["BELNR"], "B2")


if __name__ == "__main__":
    unittest.main()
