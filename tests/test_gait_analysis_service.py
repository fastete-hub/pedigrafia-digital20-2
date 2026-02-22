import csv
import tempfile
import unittest
from pathlib import Path

from services.gait_analysis_service import GaitAnalysisService


class GaitAnalysisServiceTests(unittest.TestCase):
    def test_analizar_csv_step_id(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "gait.csv"
            with p.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["foot", "step_id", "fz"])
                w.writeheader()
                for i in range(2):
                    for v in [10, 80, 140, 100, 20]:
                        w.writerow({"foot": "IZQ", "step_id": str(i), "fz": v})
                for i in range(2):
                    for v in [5, 90, 160, 110, 25]:
                        w.writerow({"foot": "DER", "step_id": str(i), "fz": v})

            res = GaitAnalysisService.analizar_csv(str(p))
            self.assertTrue(res.get("ok"))
            self.assertEqual(res["IZQ"]["n_steps"], 2)
            self.assertEqual(res["DER"]["n_steps"], 2)
            self.assertEqual(len(res["IZQ"]["curve"]), 101)
            self.assertGreater(res["DER"]["peak_n"], 0)

    def test_error_formato(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad.csv"
            with p.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["a", "b"]) 
                w.writeheader()
                w.writerow({"a": 1, "b": 2})
            res = GaitAnalysisService.analizar_csv(str(p))
            self.assertIn("error", res)


if __name__ == "__main__":
    unittest.main()
