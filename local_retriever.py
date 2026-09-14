"""Recuperación local TF-IDF sin API externa."""
from __future__ import annotations

import pickle
from datetime import date
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROUTE_PATTERNS = (
    ("PRE-GLP", r"semaglutida|tirzepatida|ozempic|wegovy|mounjaro|inyecci[oó]n.*adelgaz"),
    ("PRE-DM", r"diabetes|insulina|az[uú]car"),
    ("PRE-ANTICOAG", r"anticoagul|antiagreg|warfarina|apixab|rivaroxab|clopidogrel|aspirina|pastilla.*sangre"),
    ("PRE-MED", r"medicamento|medicinas|pastilla|vape|tabaco|alergia|suplement|valoraci[oó]n preanest[eé]sica|cpap"),
    ("PRE-SINTOMAS", r"tos|congest|fiebre|gripa|resfriad|garganta|respir"),
    ("PRE-ANSIEDAD", r"miedo|temor|ansiedad|angust|despert.*cirug|conscien|intub|no.*mover"),
    ("POST-REC", r"recuper|despiert|despert|n[aá]usea|fr[ií]o|casa|conducir|dolor.*despu[eé]s"),
    ("AN-INFO", r"anestesia|anestesi[oó]logo|regional|sedaci[oó]n|dormir|peligros"),
    ("PRE-AYUNO", r"ayuno|agua|comer|beber|alimento"),
    ("LOCAL-CONTACTO", r"no entend[ií].*instruccion|dudas? sobre.*instruccion"),
)


def build_local_index(records: list[dict[str, Any]]) -> dict[str, Any]:
    vectorizer = TfidfVectorizer(lowercase=True, strip_accents="unicode", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform([record["text"] for record in records])
    return {
        "created_at": str(date.today()),
        "retriever": "TF-IDF local",
        "vectorizer": vectorizer,
        "matrix": matrix,
        "chunks": records,
    }


def save_local_index(index: dict[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as file:
        pickle.dump(index, file)


def load_local_index(path: Path) -> dict[str, Any]:
    with path.open("rb") as file:
        return pickle.load(file)


def local_search(index: dict[str, Any], question: str, limit: int = 3) -> list[dict[str, Any]]:
    query = index["vectorizer"].transform([question])
    scores = cosine_similarity(query, index["matrix"]).ravel()
    ranked = sorted(enumerate(scores), key=lambda pair: pair[1], reverse=True)[:limit]
    return [{**index["chunks"][position], "score": float(score)} for position, score in ranked]


def hybrid_search(index: dict[str, Any], question: str, limit: int = 3) -> list[dict[str, Any]]:
    """Prioriza rutas documentales explícitas y usa TF-IDF para el resto.

    No genera texto: siempre devuelve fragmentos existentes del corpus.
    """
    import re

    for prefix, pattern in ROUTE_PATTERNS:
        if re.search(pattern, question, flags=re.IGNORECASE):
            item = next((chunk for chunk in index["chunks"] if chunk["chunk_id"].startswith(prefix)), None)
            return [{**item, "score": 1.0}] if item else []
    return local_search(index, question, limit=limit)
