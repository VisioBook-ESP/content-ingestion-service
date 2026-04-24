# Content Ingestion Service

Service de traitement et d'ingestion de documents pour la plateforme ESP (VisioBook). Ce microservice extrait le texte, les métadonnées et découpe les documents en chunks pour l'indexation et la recherche sémantique.

## Table des matières

- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Formats supportés](#formats-supportés)
- [Développement](#développement)
- [Docker](#docker)
- [Documentation API](#documentation-api)
- [Variables d'environnement](#variables-denvironnement)
- [CI/CD](#cicd)

## Fonctionnalités

- **Extraction de texte** : PDF, DOCX, HTML, TXT, images (OCR)
- **OCR** : Reconnaissance optique de caractères avec Tesseract (français/anglais)
- **Nettoyage de texte** : Normalisation, suppression headers/footers, correction encodage
- **Chunking** : Découpage intelligent avec overlap configurable
- **Détection de langue** : FR, EN, ES, DE, IT
- **Extraction de métadonnées** : Titre, auteur, nombre de pages, etc.
- **API REST** : FastAPI avec documentation OpenAPI

## Architecture

```
src/
├── api/v1/routers/       # Endpoints REST
│   ├── ingest.py         # Ingestion asynchrone
│   ├── extract.py        # Extraction de métadonnées
│   ├── preprocess.py     # Nettoyage et chunking
│   ├── validate.py       # Validation de fichiers
│   └── health.py         # Health checks
├── processors/           # Extracteurs par type de fichier
│   ├── pdf_processor.py
│   ├── docx_processor.py
│   ├── html_processor.py
│   ├── txt_processor.py
│   └── ocr_processor.py
├── services/             # Logique métier
│   ├── ingestion_service.py
│   ├── text_cleaning_service.py
│   ├── chunking_service.py
│   ├── metadata_extractor.py
│   └── storage_client.py
├── workers/              # Jobs asynchrones
│   ├── ingestion_worker.py
│   └── job_service.py
├── schemas/              # Modèles Pydantic
├── clients/              # Clients HTTP externes
└── core/                 # Configuration
```

## Installation

### Prérequis

- Python 3.11+
- Tesseract OCR (pour le traitement d'images)

### Installation locale

```bash
# Cloner le repo
git clone https://github.com/VisioBook-ESP/content-ingestion-service.git
cd content-ingestion-service

# Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou .venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Installer Tesseract (Ubuntu/Debian)
sudo apt install tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng
```

### Configuration

Créer un fichier `.env` à la racine :

```env
# Application
APP_NAME=content-ingestion-service
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/content_ingestion

# Redis
REDIS_URL=redis://localhost:6379/0

# External Services
STORAGE_SERVICE_URL=http://localhost:8084
DATABASE_SERVICE_URL=http://localhost:8081

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

## Utilisation

### Démarrage

```bash
# Mode développement (hot-reload)
uvicorn src.main:app --reload --port 8000

# Avec Docker (port externe : 8090)
docker-compose up -d
```

### API Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/v1/ingest/` | Démarrer une ingestion asynchrone |
| `GET` | `/api/v1/ingest/status/{job_id}` | Statut d'un job |
| `POST` | `/api/v1/ingest/cancel/{job_id}` | Annuler un job |
| `POST` | `/api/v1/extract/metadata` | Extraire les métadonnées d'un fichier |
| `POST` | `/api/v1/preprocess/clean` | Nettoyer du texte |
| `POST` | `/api/v1/preprocess/chunk` | Découper en chunks |
| `GET` | `/api/v1/folders/files` | Lister les fichiers d'un dossier (par token) |
| `GET` | `/api/v1/health` | Health check |

### Exemple d'ingestion

```bash
# Démarrer une ingestion
curl -X POST http://localhost:8000/api/v1/ingest/ \
  -H "Content-Type: application/json" \
  -d '{
    "fileId": "file-123",
    "projectId": "project-456",
    "options": {
      "cleanText": true,
      "extractMetadata": true,
      "chunkSize": 1000,
      "overlap": 100
    }
  }'

# Réponse
{
  "jobId": "abc-123-def",
  "status": "queued"
}

# Vérifier le statut
curl http://localhost:8000/api/v1/ingest/status/abc-123-def
```

### Script de test CLI

```bash
# Tester l'ingestion d'un fichier localement
python tests/test_ingestion.py document.pdf --print

# Avec options
python tests/test_ingestion.py image.jpg --chunk-size 50 --overlap 5

# Sortie JSON personnalisée
python tests/test_ingestion.py rapport.docx --output resultat.json
```

## Formats supportés

| Format | Extension | Processeur |
|--------|-----------|------------|
| PDF | `.pdf` | PyMuPDF (fitz) |
| Word | `.docx` | python-docx |
| HTML | `.html`, `.htm` | BeautifulSoup |
| Texte | `.txt` | Built-in |
| Images | `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, `.gif`, `.webp` | Tesseract OCR |

## Développement

### Linting et formatage

```bash
# Formatage
black src/ tests/

# Linting
ruff check src/ tests/
ruff check src/ tests/ --fix  # auto-fix

# Type checking
mypy src/

# Tout en un
black src/ tests/ && ruff check src/ tests/ && mypy src/
```

### Tests

```bash
# Tous les tests
pytest

# Avec couverture
pytest --cov=src --cov-report=html

# Tests unitaires seulement
pytest tests/unit/

# Tests d'intégration
pytest tests/integration/
```

### Structure des tests

```
tests/
├── unit/                    # Tests unitaires
│   ├── test_api_*.py
│   ├── test_services.py
│   └── test_workers.py
├── integration/             # Tests d'intégration
│   └── test_ingestion_pipeline.py
├── samples/                 # Fichiers de test
│   ├── exemple.txt
│   ├── exemple.html
│   ├── test.pdf
│   └── test.docx
└── conftest.py              # Fixtures pytest
```

## Docker

### Build et run

```bash
# Démarrer tous les services
docker-compose up -d

# Logs
docker-compose logs -f content-ingestion-service

# Rebuild après modifications
docker-compose up -d --build
```

### Services inclus

| Service | Description | Port |
|---------|-------------|------|
| `content-ingestion-service` | API principale | `8090` (→ 8000 interne) |
| `db` | PostgreSQL 14 | `5433` |
| `redis` | Redis 7 | `6380` |

## Documentation API

Une fois le service démarré, accéder à :

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

> En Docker, remplacer le port `8000` par `8090`.

## Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `APP_NAME` | Nom de l'application | `content-ingestion-service` |
| `ENVIRONMENT` | Environnement (development/staging/production) | `development` |
| `DEBUG` | Mode debug | `true` |
| `LOG_LEVEL` | Niveau de log | `INFO` |
| `API_PORT` | Port de l'API | `8000` |
| `DATABASE_URL` | URL PostgreSQL | - |
| `REDIS_URL` | URL Redis | - |
| `STORAGE_SERVICE_URL` | URL du service de stockage | - |
| `DATABASE_SERVICE_URL` | URL du service de base de données | - |

## CI/CD

Le projet utilise GitHub Actions pour :

- **Linting** : black, ruff, mypy
- **Tests** : pytest avec couverture
- **Build** : Docker image
- **Deploy** : Kubernetes via Helm

## Licence

Proprietary - VisioBook
