"""Carga, fragmentación y recuperación para el MVP perioperatorio."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

PHASE_BY_PREFIX = {"PRE": "Preoperatorio", "AN": "Intraoperatorio", "POST": "Recuperación", "LOCAL": "Gobernanza local"}
EMERGENCY_PATTERNS = (
    r"dificultad para respirar|falta (de |el )?aire|dolor (en )?el pecho|desmay|inconsciente|"
    r"sangrado (importante|abundante)|sangrando (mucho|abundantemente)|debilidad súbita|confu|convuls",
)
MEDICATION_RISK_PATTERNS = (
    r"(suspend|dejar|parar|reinici|cambi|subir|bajar|duplicar|omitir|salt).*(insulina|anticoagul|"
    r"antiagreg|warfarina|apixab|rivaroxab|clopidogrel|aspirina|semaglutida|tirzepatida|GLP-?1)|"
    r"(insulina|anticoagul|antiagreg|warfarina|apixab|rivaroxab|clopidogrel|aspirina|semaglutida|"
    r"tirzepatida|GLP-?1).*(suspend|dejar|parar|reinici|cambi|dosis|omitir|salt)",
)
PREOPERATIVE_SYMPTOM_PATTERNS = (
    r"\btos\b|congest|fiebre|gripa|resfriad|dolor de garganta|moco|síntoma respiratorio|"
    r"síntomas respiratorios|infección respiratoria",
)
OUT_OF_SCOPE_PATTERNS = (
    r"antibi[oó]tico|migraña|dieta.*bajar|cu[aá]nto cuesta|partido de f[uú]tbol|biopsia|"
    r"diagnosticar|dosis de ibuprofeno|invierto|electrocardiograma",
)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    _, raw_meta, body = text.split("---", 2)
    metadata: dict[str, Any] = {}
    for line in raw_meta.strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata, body.strip()


def category_from_filename(path: Path) -> str:
    return re.sub(r"^\d+_", "", path.stem).replace("_", " ").capitalize()


def chunk_text(text: str, max_chars: int = 850, overlap: int = 140) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, current = [], ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip()
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        carry = current[-overlap:] if current else ""
        current = f"{carry}\n\n{paragraph}".strip()
        while len(current) > max_chars:
            chunks.append(current[:max_chars])
            current = current[max_chars - overlap :]
    if current:
        chunks.append(current)
    return chunks


def build_chunks(corpus_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(corpus_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        source = metadata.get("fuente_principal", "Fuente no especificada")
        for index, chunk in enumerate(chunk_text(body)):
            prefix = str(metadata.get("id", "LOCAL")).split("-")[0]
            records.append({
                "chunk_id": f"{metadata.get('id', path.stem)}-{index + 1}",
                "text": chunk,
                "fase": PHASE_BY_PREFIX.get(prefix, "General"),
                "categoría": category_from_filename(path),
                "riesgo": metadata.get("nivel_riesgo", "moderado"),
                "fuente": source,
                "url_fuente": metadata.get("url_fuente", ""),
                "fecha": metadata.get("fecha_revisión", ""),
                "versión": metadata.get("versión", ""),
                "responsable_clínico": metadata.get("responsable_clínico", ""),
                "estado": metadata.get("estado", ""),
            })
    return records


def cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


def search(index: dict[str, Any], query_embedding: list[float], limit: int = 3) -> list[dict[str, Any]]:
    scored = []
    for item in index["chunks"]:
        score = cosine_similarity(query_embedding, item["embedding"])
        scored.append({**item, "score": score})
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]


def assess_risk(question: str) -> str:
    """Clasifica únicamente para decidir la ruta de escalamiento, no para diagnosticar."""
    if re.search("|".join(EMERGENCY_PATTERNS), question, flags=re.IGNORECASE):
        return "emergencia"
    if re.search("|".join(MEDICATION_RISK_PATTERNS), question, flags=re.IGNORECASE):
        return "medicación_alto_riesgo"
    if re.search("|".join(PREOPERATIVE_SYMPTOM_PATTERNS), question, flags=re.IGNORECASE):
        return "síntomas_preoperatorios"
    if re.search("|".join(OUT_OF_SCOPE_PATTERNS), question, flags=re.IGNORECASE):
        return "fuera_de_alcance"
    return "general"


def corpus_route(index: dict[str, Any], prefix: str) -> dict[str, Any] | None:
    """Recupera una ruta prevalidada del corpus para alto riesgo."""
    return next((item for item in index["chunks"] if item["chunk_id"].startswith(prefix)), None)


def save_index(index: dict[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")


def load_index(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
