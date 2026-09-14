"""Genera un índice TF-IDF local; no usa claves ni servicios externos."""
from __future__ import annotations

import argparse
from pathlib import Path

from local_retriever import build_local_index, save_local_index
from rag_core import build_chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default="corpus")
    parser.add_argument("--output", default="data/index.pkl")
    args = parser.parse_args()

    records = build_chunks(Path(args.corpus))
    if not records:
        raise SystemExit("El corpus no contiene documentos indexables.")
    save_local_index(build_local_index(records), Path(args.output))
    print(f"Índice local creado: {len(records)} fragmentos en {args.output}")


if __name__ == "__main__":
    main()
