# Analyse de sentiments — commentaires Reddit et YouTube

## Présentation

Ce projet entraîne et met à disposition un modèle de classification de sentiments. Le modèle et les données fournis portent sur des commentaires en anglais. Chaque texte est classé dans l'une de ces catégories :

| Étiquette | Sentiment |
|---:|---|
| `-1` | négatif |
| `0` | neutre |
| `1` | positif |

Le dépôt comprend le pipeline de préparation des données et d'entraînement, une API HTTP pour les prédictions, ainsi qu'une extension Chrome qui extrait les commentaires visibles d'une vidéo YouTube et affiche leur répartition par sentiment.

Le modèle fourni est déjà entraîné. Sur le jeu de test du projet, les métriques enregistrées sont une accuracy de **0,893**, un F1 macro de **0,883** et un temps d'inférence mesuré d'environ **1 ms pour 50 textes**. Ces résultats dépendent du jeu de données et de l'environnement d'exécution.

## Architecture

```text
data/raw/reddit.csv
       │
       ├── src/data/eda.py                 Analyse exploratoire
       └── src/data/make_dataset.py        Nettoyage et séparation train/test
                    │
                    └── data/processed/
                              │
                              └── src/models/train.py
                                    ├── models/tfidf_vectorizer.joblib
                                    ├── models/sentiment_model.joblib
                                    └── reports/ (métriques et graphiques)

chrome-extension/ ── POST /predict_batch ──> app_api.py
                                               │
                                               └── src/api/
                                                    ├── main.py
                                                    ├── model_service.py
                                                    └── schemas.py
```

- **Données et entraînement** : le dataset Reddit est nettoyé, dédupliqué et séparé en ensembles d'entraînement et de test de façon stratifiée. Le prétraitement partagé entre entraînement et prédiction normalise le texte et retire notamment les URL, mentions, hashtags et caractères spéciaux. L'entraînement compare plusieurs algorithmes, puis optimise une régression logistique avec TF-IDF et validation croisée.
- **API** : FastAPI charge le vectoriseur et le modèle au démarrage, puis expose les prédictions par lot, la santé du service et la documentation OpenAPI.
- **Extension Chrome** : l'extension extrait les commentaires d'une page vidéo YouTube, les envoie à l'API par lots et présente les statistiques, les prédictions et leur confiance. Elle permet de filtrer les résultats et de les copier ou exporter en CSV.
- **Déploiement** : le `Dockerfile` construit une image de production basée sur Python 3.10, qui expose l'API sur le port `7860`.

## Prérequis

- Python 3.10 ou version compatible avec les dépendances épinglées.
- `pip`.
- Chrome ou un navigateur Chromium pour utiliser l'extension.
- Docker, uniquement pour le lancement conteneurisé.

## Installation et lancement de l'API

Depuis la racine du dépôt :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

L'environnement de développement inclut les dépendances d'entraînement et de test. Pour une installation limitée à l'exécution de l'API :

```powershell
python -m pip install -r requirements-prod.txt
```

Démarrez ensuite le serveur local :

```powershell
python -m uvicorn app_api:app --host 0.0.0.0 --port 8000
```

L'API est accessible sur `http://localhost:8000`. Consultez `http://localhost:8000/docs` pour l'interface interactive, ou `http://localhost:8000/health` pour vérifier que le modèle est chargé. Si vous déplacez les fichiers du modèle, définissez la variable d'environnement `MODEL_DIR` vers leur dossier.

### Exemple de prédiction

Envoyez un tableau contenant entre 1 et 1 000 commentaires à `POST /predict_batch` :

```powershell
curl.exe -X POST http://localhost:8000/predict_batch `
  -H "Content-Type: application/json" `
  -d '{"comments":["I love this video!","This was disappointing."]}'
```

Chaque commentaire est limité à 5 000 caractères. La réponse contient une prédiction par texte (`label`, `sentiment` et `confidence`), les statistiques du lot et le temps de traitement. Les valeurs de `sentiment` sont `negative`, `neutral` et `positive`.

Exemple de structure de réponse :

```json
{
  "predictions": [
    {
      "index": 0,
      "text": "I love this video!",
      "label": 1,
      "sentiment": "positive",
      "confidence": 0.91
    }
  ],
  "statistics": {
    "total": 1,
    "counts": {"negative": 0, "neutral": 0, "positive": 1},
    "percentages": {"negative": 0.0, "neutral": 0.0, "positive": 100.0},
    "average_confidence": 0.91
  },
  "processing_ms": 1.0
}
```

Les scores et temps de cet exemple sont illustratifs.

## Utiliser l'extension Chrome

1. Démarrez l'API locale, ou configurez une API déployée.
2. Dans `chrome-extension/config.js`, vérifiez les URL `API_TARGETS`. La cible `local` est initialement `http://localhost:8000` ; la cible `cloud` doit correspondre à l'adresse de votre déploiement.
3. Ouvrez `chrome://extensions`, activez le **mode développeur**, choisissez **Charger l'extension non empaquetée** et sélectionnez le dossier `chrome-extension`.
4. Ouvrez une vidéo YouTube, cliquez sur l'extension puis sur **Analyser cette vidéo**. Choisissez la cible d'API et le nombre de commentaires, et activez si besoin l'inclusion des réponses visibles.

L'extension propose la répartition des sentiments, les filtres par classe, l'affichage progressif des commentaires, la copie du rapport et l'export CSV. Pour une API servie sur un port autre que `8000`, adaptez aussi la configuration d'accès réseau déclarée dans `chrome-extension/manifest.json`.

## Préparer les données et réentraîner

Les scripts s'exécutent depuis la racine du dépôt. Le téléchargement est facultatif si `data/raw/reddit.csv` est déjà présent :

```powershell
python -m src.data.download
python -m src.data.make_dataset
python -m src.data.eda
python -m src.models.train
```

La préparation crée `data/processed/clean.csv`, `train.csv` et `test.csv`. L'entraînement compare la régression logistique, LinearSVC et Random Forest, puis optimise la régression logistique par validation croisée. Il enregistre les deux artefacts chargés par l'API dans `models/` et les métriques ainsi que la matrice de confusion dans `reports/`.

## Lancement avec Docker

Construisez l'image puis démarrez le conteneur :

```powershell
docker build -t sentiment-mlops .
docker run --rm -p 7860:7860 sentiment-mlops
```

L'API est alors accessible sur `http://localhost:7860`. Pour que l'extension puisse utiliser ce conteneur, adaptez la cible `local` dans `chrome-extension/config.js` et autorisez le port correspondant dans `chrome-extension/manifest.json`.

## Tests

Avec les dépendances de développement installées :

```powershell
python -m pytest
```

Les tests couvrent le nettoyage des textes, les performances du modèle, les cas limites de prédiction, les routes de l'API et la latence d'inférence.

## Principaux dossiers

```text
app_api.py                 Point d'entrée Uvicorn
src/data/                  Téléchargement, préparation et analyse des données
src/models/train.py        Entraînement et évaluation
src/api/                   API, schémas et service de prédiction
src/utils/                 Nettoyage des textes et journalisation
data/                      Données brutes et préparées
models/                    Modèle et vectoriseur pré-entraînés
reports/                   Métriques et graphiques
chrome-extension/          Extension Chrome
tests/                     Tests automatisés
```