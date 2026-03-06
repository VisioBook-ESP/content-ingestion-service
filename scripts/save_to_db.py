#!/usr/bin/env python3
"""
Sauvegarde des fichiers JSON d'output en base PostgreSQL locale.

Usage:
    python scripts/save_to_db.py tests/outputs/*.json
    python scripts/save_to_db.py tests/outputs/document_output.json
    python scripts/save_to_db.py file1.json file2.json --dry-run
"""

import argparse
import asyncio
import glob
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.dialects.postgresql import insert  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: E402

from src.database.connection import engine  # noqa: E402
from src.models.document import Base, Document  # noqa: E402

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sauvegarde les fichiers JSON d'ingestion en base PostgreSQL locale",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python scripts/save_to_db.py tests/outputs/*.json
  python scripts/save_to_db.py tests/outputs/mon_doc_output.json
  python scripts/save_to_db.py fichier1.json fichier2.json
  python scripts/save_to_db.py tests/outputs/*.json --dry-run
        """,
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Chemins vers les fichiers JSON (supporte les glob patterns)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valider les fichiers sans ecrire en base",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Activer les logs detailles",
    )
    return parser.parse_args()


def resolve_file_paths(patterns: list[str]) -> list[Path]:
    """Resout les glob patterns en chemins de fichiers."""
    paths = []
    for pattern in patterns:
        expanded = glob.glob(pattern, recursive=True)
        if not expanded:
            print(f"  Attention: aucun fichier ne correspond au pattern '{pattern}'")
        for file_path in expanded:
            p = Path(file_path)
            if p.is_file() and p.suffix == ".json":
                paths.append(p)
            else:
                print(f"  Attention: fichier non-JSON ignore '{file_path}'")
    return paths


def load_json_document(file_path: Path) -> dict:
    """Charge et valide un fichier JSON."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "fileId" not in data:
        raise ValueError(f"Champ requis 'fileId' manquant dans {file_path}")

    return data


def extract_columns(data: dict) -> dict:
    """Extrait les colonnes indexees depuis le JSON."""
    processed_at = None
    if data.get("processedAt"):
        try:
            processed_at = datetime.fromisoformat(data["processedAt"])
        except (ValueError, TypeError):
            pass

    return {
        "file_id": data["fileId"],
        "project_id": data.get("projectId"),
        "file_name": data.get("fileName"),
        "file_type": data.get("fileType"),
        "status": data.get("status"),
        "processed_at": processed_at,
        "data": data,
    }


async def create_tables():
    """Cree les tables si elles n'existent pas."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def upsert_document(session: AsyncSession, values: dict) -> str:
    """Insert ou update un document. Retourne 'inserted' ou 'updated'."""
    # Check existence first to report action
    existing = await session.execute(
        select(Document.id).where(Document.file_id == values["file_id"])
    )
    action = "updated" if existing.scalar_one_or_none() else "inserted"

    stmt = insert(Document).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["file_id"],
        set_={
            "project_id": stmt.excluded.project_id,
            "file_name": stmt.excluded.file_name,
            "file_type": stmt.excluded.file_type,
            "status": stmt.excluded.status,
            "processed_at": stmt.excluded.processed_at,
            "data": stmt.excluded.data,
            "updated_at": func.now(),
        },
    )
    await session.execute(stmt)
    return action


async def main_async(file_paths: list[Path], dry_run: bool = False):
    """Logique principale async."""
    print(f"\n{'=' * 60}")
    print(f"SAUVEGARDE EN BASE: {len(file_paths)} fichier(s)")
    print(f"{'=' * 60}\n")

    if not dry_run:
        try:
            print("Creation des tables si necessaire...")
            await create_tables()
            print("Tables pretes.\n")
        except Exception as e:
            print(f"Erreur de connexion a la base: {e}")
            print("PostgreSQL est-il en cours d'execution ?")
            print("  → docker-compose up -d db")
            await engine.dispose()
            sys.exit(1)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    inserted = 0
    updated = 0
    failed = 0

    for i, file_path in enumerate(file_paths, 1):
        try:
            print(f"[{i}/{len(file_paths)}] Traitement de {file_path.name}...")
            data = load_json_document(file_path)
            values = extract_columns(data)

            if dry_run:
                chunks = len(data.get("chunks", []))
                print(
                    f"         Dry run - fileId={values['file_id']}, "
                    f"status={values['status']}, chunks={chunks}"
                )
                inserted += 1
                continue

            async with session_factory() as session:
                async with session.begin():
                    action = await upsert_document(session, values)

            if action == "inserted":
                inserted += 1
                print(f"         Insere: fileId={values['file_id']}")
            else:
                updated += 1
                print(f"         Mis a jour: fileId={values['file_id']}")

        except Exception as e:
            failed += 1
            print(f"         ECHEC: {e}")

    print(f"\n{'=' * 60}")
    print("RESULTATS")
    print(f"{'=' * 60}")
    print(f"  Inseres:     {inserted}")
    print(f"  Mis a jour:  {updated}")
    print(f"  Echoues:     {failed}")
    print(f"  Total:       {len(file_paths)}")

    if dry_run:
        print("\n  (Dry run - aucune modification en base)")

    await engine.dispose()


def main():
    args = parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    file_paths = resolve_file_paths(args.files)

    if not file_paths:
        print("Aucun fichier JSON trouve. Rien a faire.")
        sys.exit(0)

    asyncio.run(main_async(file_paths, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
