import tempfile
import unittest
from pathlib import Path

from rag_core import assess_risk, build_chunks, chunk_text


class RAGCoreTests(unittest.TestCase):
    def test_chunk_text_keeps_content(self):
        text = "Primer párrafo con información.\n\nSegundo párrafo con más información."
        self.assertIn("Primer", " ".join(chunk_text(text, max_chars=30, overlap=5)))

    def test_build_chunks_extracts_required_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp)
            (corpus / "01_prueba.md").write_text(
                "---\nid: PRE-TEST-01\nnivel_riesgo: alto\nfuente_principal: Fuente demo\nfecha_revisión: 2026-09-14\n---\n\n# Prueba\n\nTexto de prueba.",
                encoding="utf-8",
            )
            record = build_chunks(corpus)[0]
            self.assertEqual(record["fase"], "Preoperatorio")
            self.assertEqual(record["riesgo"], "alto")
            self.assertEqual(record["fuente"], "Fuente demo")

    def test_assess_risk_detects_emergency_and_medication_requests(self):
        self.assertEqual(assess_risk("Tengo dolor en el pecho después de la cirugía"), "emergencia")
        self.assertEqual(assess_risk("¿Debo suspender mi apixabán?"), "medicación_alto_riesgo")
        self.assertEqual(assess_risk("¿Qué es anestesia regional?"), "general")

    def test_symptoms_before_procedure_escalate_to_preanesthetic_route(self):
        self.assertEqual(assess_risk("Tengo tos y congestión antes de la cirugía"), "síntomas_preoperatorios")


if __name__ == "__main__":
    unittest.main()
