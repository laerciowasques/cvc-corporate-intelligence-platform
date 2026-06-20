"""CLI de indexação da base de conhecimento."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.pipeline import IngestionPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexa a base de conhecimento CVC")
    parser.add_argument("--source", default="cvc-ri-portal", help="ID da base")
    args = parser.parse_args()

    print(f"Indexando base: {args.source}")
    pipeline = IngestionPipeline(source_id=args.source)
    manifest = pipeline.run()
    print("Indexação concluída:")
    for k, v in manifest.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
