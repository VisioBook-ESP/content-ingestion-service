# Kanban complet — content-ingestion-service
> Depuis le premier commit · 21 juillet 2025 → aujourd'hui

---

## Phase 0 — Initialisation du repo
**juillet 2025**

| Statut | Tâche | Commits |
|--------|-------|---------|
| ✅ Done | Structure initiale du projet | 1 |

---

## Phase 1 — Bootstrap FastAPI + CI/CD
**janvier 2026**

| Statut | Tâche | Commits |
|--------|-------|---------|
| ✅ Done | Structure FastAPI + modèles + routes | 4 |
| ✅ Done | Ajout requirements.txt | 1 |
| ✅ Done | Configuration linters (black, ruff, mypy) | 2 |
| ✅ Done | Setup pipeline CI/CD + fix workflow | 4 |
| ✅ Done | Suppression Redis | 1 |

---

## Phase 2 — Stabilisation CI (no-debug + unit tests)
**janvier 2026**

| Statut | Tâche | Commits |
|--------|-------|---------|
| ✅ Done | Fix `no-debug-leftovers` (gate CI) | 10 |
| ✅ Done | Fix type-check + unit tests | 3 |
| ✅ Done | Ajout structlog + aiosqlite | 2 |
| ✅ Done | Passage unit tests CI | 3 |


---

## Phase 3 — Service d'ingestion + OCR
**février 2026**

| Statut | Tâche | Commits |
|--------|-------|---------|
| ✅ Done | Add Ingestion Service (core) | 1 |
| ✅ Done | Tests ingestion + samples | 2 |
| ✅ Done | README complet + support OCR dans tests | 3 |
| ✅ Done | Fix linting black/ruff/mypy | 3 |
| ✅ Done | Nettoyage .venv + .gitignore | 5 |
| ✅ Done | Fix CI post-merge | 3 |
| ✅ Merged | **PR #4** — feature/ingestion-service → dev | — |

---

## Phase 4 — Helm chart + déploiement K8s initial
**février 2026**

| Statut | Tâche | Commits |
|--------|-------|---------|
| ✅ Done | Add Helm chart (initial) | 2 |
| ✅ Done | Processeur PDF (PyMuPDF — texte + métadonnées) | 1 |
| ✅ Done | Endpoint validation fichier (format/taille/lisibilité) | 1 |
| ✅ Done | Stockage PostgreSQL local (JSON output) | 1 |
| ✅ Done | Clean commit + fix Helm values | 3 |
| ✅ Done | Add sync wave ArgoCD | 1 |
| ✅ Merged | **PR #9** — 5-modify-helm-chart → dev | — |
| ✅ Done | Fix values Helm chart | 1 |
| ✅ Merged | **PR #12** — 11-fix-values-in-chart → dev | — |

---

## Phase 5 — MinIO + mise à jour Helm chart
**février 2026**

| Statut | Tâche |Commits |
|--------|-------|---------|
| ✅ Done | Mise à jour chart (secrets MinIO) | 1 |
| ✅ Merged | **PR #14 + #16** — 13-mise-a-jour-helm-chart → dev | — |
| ✅ Done | Add MinIO storage + endpoint upload | 2 |
| ✅ Done | Entrypoint script | 1 |
| ✅ Done | Test scripts API | 1 |
| ✅ Done | Tests MinIO (itératifs) | 4 |
| ✅ Merged | **PR #18** — 17-update-charts-with-minio-secrets → dev | — |

---

## Phase 6 — CI robuste + DB scripts Helm
**mars 2026**

| Statut | Tâche | Commits |
|--------|-------|---------|
| ✅ Done | Fix docker-compose + prod | 1 |
| ✅ Done | Fix MinIO/Worker init (defer à l'import) | 2 + 6 reverts |
| ✅ Done | Fix entrypoint.sh dans CI | 1 |
| ✅ Done | Fix CORS_ORIGINS (pydantic-settings) | 1 |
| ✅ Done | CI : unit tests + alembic dans image prod | 1 |
| ✅ Done | Fix DATABASE_URL + image tag sha | 4 |
| ✅ Merged | **PR #15, #19, #20, #21, #22** → dev | — |
| ✅ Done | SQL migration scripts pour Helm job | 1 |
| ✅ Done | Fix Helm (env dupliqués, ArgoCD sync fail) | 2 |
| ✅ Done | Fix MinIO hostname cluster + endpoint/port | 1 |
| ✅ Done | Revert/restore alembic dans entrypoint | 1 |


---

## Phase 7 — Folders API
**mars 2026**

| Statut | Tâche | Commits |
|--------|-------|---------|
| ✅ Done | `POST /api/v1/folders/` (génération folderId) | 7 |
| ✅ Done | `GET /api/v1/folders/files` (listing par token) | 4 |
| ✅ Done | Fix résolution folderId via `/users/resolve-folder` | 1 |
| ✅ Done | Résolution folderId depuis DB locale par userId | 1 |
| 🔄 In Progress | Fix résolution userId via `/users/me` (uuid) | 1 |

---

## Synthèse

| Métrique | Valeur |
|----------|--------|
| **Premier commit** | 21 juillet 2025 |
| **Durée totale** | ~9 mois (actif depuis jan. 2026) |
| **Commits totaux** | ~130 |
| **PRs mergées** | 9 (#4, #9, #12, #14, #15, #16, #18, #19–#22) |
| **Phases complètes** | 6 / 7 |
| **Phase en cours** | Folders API (phase 7) |

### Patterns notables

- **CI friction élevée** : les phases 2 et 6 ont chacune nécessité 6–10 commits pour passer un seul gate
- **Commits répétés** : `POST /api/v1/folders/` a 7 commits identiques le 13 mars — push/test itératifs sans squash
- **Pause de 6 mois** : entre le commit initial (juil. 2025) et le vrai démarrage (jan. 2026)
- **Accélération** : le rythme de livraison s'est densifié depuis fév. 2026
