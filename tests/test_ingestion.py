#!/usr/bin/env python3
"""
Script de test pour l'ingestion de documents.

Usage:
    python scripts/test_ingestion.py <fichier> [--output <fichier_json>]

Exemples:
    python scripts/test_ingestion.py document.txt
    python scripts/test_ingestion.py document.pdf --output resultat.json
    python scripts/test_ingestion.py document.html --chunk-size 50 --overlap 10
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def json_serializer(obj):
    """Convertit les objets non-sérialisables en JSON."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processors.docx_processor import DocxProcessor  # noqa: E402
from src.processors.html_processor import HTMLProcessor  # noqa: E402
from src.processors.ocr_processor import OCRProcessor  # noqa: E402
from src.processors.pdf_processor import PDFProcessor  # noqa: E402
from src.processors.processor_factory import ProcessorFactory  # noqa: E402
from src.processors.txt_processor import TextProcessor  # noqa: E402
from src.schemas.preprocess import CleanOptions  # noqa: E402
from src.services.chunking_service import ChunkingService  # noqa: E402
from src.services.metadata_extractor import MetadataExtractor  # noqa: E402
from src.services.text_cleaning_service import TextCleaningService  # noqa: E402


def process_file(
    file_path: str,
    chunk_size: int = 100,
    overlap: int = 10,
    clean_text: bool = True,
    extract_metadata: bool = True,
) -> dict:
    """Traite un fichier et retourne le document JSON."""

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier non trouvé: {file_path}")

    # Initialisation des services
    processor_factory = ProcessorFactory(
        [
            PDFProcessor(),
            TextProcessor(),
            DocxProcessor(),
            HTMLProcessor(),
            OCRProcessor(),
        ]
    )
    text_cleaning_service = TextCleaningService()
    chunking_service = ChunkingService()
    metadata_extractor = MetadataExtractor()

    # 1. Extraction du texte
    print(f"[1/4] Extraction du texte depuis {path.name}...")
    processor = processor_factory.get_processor(str(path))
    raw_text = processor.extract_text(str(path))
    print(f"      → {len(raw_text)} caractères extraits")

    # 2. Nettoyage du texte
    if clean_text:
        print("[2/4] Nettoyage du texte...")
        clean_options = CleanOptions(
            removeExtraSpaces=True,
            normalizeQuotes=True,
            fixEncoding=True,
            removeHeaders=False,
            removeFooters=False,
        )
        cleaned_text, changes = text_cleaning_service.clean(raw_text, clean_options)
        print(f"      → Transformations appliquées: {changes}")
    else:
        print("[2/4] Nettoyage désactivé")
        cleaned_text = raw_text
        changes = []

    # 3. Extraction des métadonnées
    if extract_metadata:
        print("[3/4] Extraction des métadonnées...")
        metadata = processor.extract_metadata(str(path))
        metadata = metadata_extractor.enrich(metadata, cleaned_text)
        print(f"      → Langue détectée: {metadata.get('language', 'inconnu')}")
        print(f"      → Nombre de mots: {metadata.get('wordCount', 0)}")
    else:
        print("[3/4] Extraction des métadonnées désactivée")
        metadata = {}

    # 4. Découpage en chunks
    print(f"[4/4] Découpage en chunks (taille={chunk_size}, overlap={overlap})...")
    chunks = chunking_service.chunk(cleaned_text, chunk_size, overlap)
    print(f"      → {len(chunks)} chunks créés")

    # Construction du document JSON
    output_document = {
        "fileId": path.stem,
        "fileName": path.name,
        "fileType": path.suffix.lower(),
        "fileSize": path.stat().st_size,
        "processedAt": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "options": {
            "cleanText": clean_text,
            "extractMetadata": extract_metadata,
            "chunkSize": chunk_size,
            "overlap": overlap,
        },
        "metadata": metadata,
        "processing": {
            "cleaningApplied": changes,
            "totalChunks": len(chunks),
            "totalCharacters": len(cleaned_text),
            "rawCharacters": len(raw_text),
        },
        "chunks": [
            {
                "index": i,
                "content": chunk,
                "wordCount": len(chunk.split()),
            }
            for i, chunk in enumerate(chunks)
        ],
    }

    return output_document


def main():
    parser = argparse.ArgumentParser(
        description="Test d'ingestion de documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python scripts/test_ingestion.py mon_document.txt
  python scripts/test_ingestion.py rapport.pdf --output rapport.json
  python scripts/test_ingestion.py page.html --chunk-size 50 --overlap 5
  python scripts/test_ingestion.py fichier.docx --no-clean --no-metadata
        """,
    )
    parser.add_argument("file", help="Chemin vers le fichier à traiter (txt, pdf, docx, html)")
    parser.add_argument(
        "-o", "--output", help="Fichier JSON de sortie (défaut: <nom_fichier>_output.json)"
    )
    parser.add_argument(
        "--chunk-size", type=int, default=100, help="Taille des chunks en mots (défaut: 100)"
    )
    parser.add_argument(
        "--overlap", type=int, default=10, help="Chevauchement entre chunks en mots (défaut: 10)"
    )
    parser.add_argument("--no-clean", action="store_true", help="Désactiver le nettoyage du texte")
    parser.add_argument(
        "--no-metadata", action="store_true", help="Désactiver l'extraction des métadonnées"
    )
    parser.add_argument("--print", action="store_true", help="Afficher le JSON dans le terminal")

    args = parser.parse_args()

    try:
        print(f"\n{'='*60}")
        print(f"INGESTION DE DOCUMENT: {args.file}")
        print(f"{'='*60}\n")

        result = process_file(
            args.file,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
            clean_text=not args.no_clean,
            extract_metadata=not args.no_metadata,
        )

        # Déterminer le fichier de sortie
        if args.output:
            output_path = Path(args.output)
        else:
            input_path = Path(args.file)
            # Sortie dans tests/outputs/ par défaut
            outputs_dir = Path(__file__).parent / "outputs"
            outputs_dir.mkdir(exist_ok=True)
            output_path = outputs_dir / f"{input_path.stem}_output.json"

        # Créer le dossier parent si nécessaire
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Écriture du fichier JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=json_serializer)

        print(f"\n{'='*60}")
        print("RÉSULTAT")
        print(f"{'='*60}")
        print(f"✓ Fichier JSON généré: {output_path}")
        print(f"✓ Chunks créés: {result['processing']['totalChunks']}")
        print(f"✓ Caractères traités: {result['processing']['totalCharacters']}")

        if args.print:
            print(f"\n{'='*60}")
            print("CONTENU JSON:")
            print(f"{'='*60}")
            print(json.dumps(result, ensure_ascii=False, indent=2, default=json_serializer))

        return 0

    except FileNotFoundError as e:
        print(f"❌ Erreur: {e}")
        return 1
    except Exception as e:
        print(f"❌ Erreur lors du traitement: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
