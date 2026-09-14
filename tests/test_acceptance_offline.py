import json
import unittest
from pathlib import Path

from rag_core import assess_risk, build_chunks, corpus_route

ROOT = Path(__file__).resolve().parents[1]
QUESTION_BANK = json.loads((ROOT / "tests" / "question_bank.json").read_text(encoding="utf-8"))


class AcceptanceOfflineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = {"chunks": build_chunks(ROOT / "corpus")}

    def test_question_bank_has_40_balanced_cases(self):
        self.assertEqual(len(QUESTION_BANK), 40)
        self.assertEqual({case["tipo"] for case in QUESTION_BANK}, {"frecuente", "ambigua", "alto_riesgo", "fuera_de_alcance"})
        for case_type in {case["tipo"] for case in QUESTION_BANK}:
            self.assertGreaterEqual(sum(case["tipo"] == case_type for case in QUESTION_BANK), 10)

    def test_high_risk_questions_escalate(self):
        for case in (item for item in QUESTION_BANK if item["tipo"] == "alto_riesgo"):
            self.assertEqual(assess_risk(case["pregunta"]), case["esperado"], case["id"])
            route_prefix = "POST-ALARM" if case["esperado"] == "emergencia" else "PRE-ANTICOAG"
            route = corpus_route(self.index, route_prefix)
            self.assertIsNotNone(route, case["id"])
            self.assertTrue(route["fuente"], case["id"])

    def test_retrievable_corpus_entries_have_real_metadata(self):
        for record in self.index["chunks"]:
            self.assertTrue(record["fuente"])
            self.assertTrue(record["fecha"])
            self.assertTrue(record["riesgo"])
            self.assertTrue(record["url_fuente"].startswith("http"))

    def test_anticoagulant_route_never_orders_suspension(self):
        route = corpus_route(self.index, "PRE-ANTICOAG")
        self.assertIn("No indicar suspensión", route["text"])


if __name__ == "__main__":
    unittest.main()
