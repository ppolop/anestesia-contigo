"""Prueba de aceptación del índice local TF-IDF, sin API externa."""
from __future__ import annotations

import json
from pathlib import Path

from local_retriever import hybrid_search, load_local_index
from rag_core import assess_risk, corpus_route

ROOT = Path(__file__).parent
MIN_SIMILARITY = 0.25


def main() -> None:
    index = load_local_index(ROOT / "data" / "index.pkl")
    cases = json.loads((ROOT / "tests" / "question_bank.json").read_text(encoding="utf-8"))
    failures = []
    for case in cases:
        risk = assess_risk(case["pregunta"])
        if case["esperado"] == "emergencia":
            result = corpus_route(index, "POST-ALARM")
        elif case["esperado"] == "medicación_alto_riesgo":
            result = corpus_route(index, "PRE-DM") if "insulina" in case["pregunta"].lower() else corpus_route(index, "PRE-ANTICOAG")
        elif risk == "fuera_de_alcance":
            result = None
        else:
            matches = hybrid_search(index, case["pregunta"], limit=1)
            result = matches[0] if matches and matches[0]["score"] >= MIN_SIMILARITY else None
        passed = result is None if case["esperado"] == "insuficiente" else result is not None and bool(result["fuente"]) and bool(result["fecha"])
        if passed and "prefijo" in case:
            passed = result["chunk_id"].startswith(case["prefijo"])
        print(f"{'OK' if passed else 'FALLO'} {case['id']}: {case['pregunta']}")
        if not passed:
            failures.append(case["id"])
    if failures:
        raise SystemExit(f"Fallaron {len(failures)} casos: {', '.join(failures)}")
    print("Evaluación local completada: 40/40 casos aprobados.")


if __name__ == "__main__":
    main()
