# ShopFlow - API E-Commerce FastAPI

ShopFlow est une API e-commerce moderne construite avec **FastAPI**, **SQLAlchemy**, et **PostgreSQL/SQLite**. Le projet démontre les meilleures pratiques avec couverture de tests complète, pipeline CI/CD, et analyse de qualité de code.

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Tests](#tests)
- [Advanced Testing & Security (TP4)](#advanced-testing--security-tp4)
- [CI/CD Pipeline](#cicd-pipeline)
- [Métriques de qualité](#métriques-de-qualité)
- [Sécurité](#sécurité)
- [Documentation API](#documentation-api)
- [Contribution](#contribution)

---

## Vue d'ensemble

ShopFlow est une plateforme e-commerce complète supportant :
- Gestion des produits : CRUD, filtrage, pagination
- Panier d'achat : Ajout/suppression d'articles, persistance
- Commandes : Création, tracking, gestion du stock
- Coupons de réduction : Codes promo, validation, application
- Pricing : Calcul automatique TVA, gestion des réductions
- Cache Redis : Performance optimisée pour lectures fréquentes
- Tests exhaustifs : 37 tests unitaires + 45+ tests d'intégration
- CI/CD : Pipeline Jenkins automatisé avec SonarQube

**Caractéristiques techniques:**
- Framework API asynchrone (async/await)
- Validation de schémas avec Pydantic v2
- ORM SQLAlchemy 2.0 avec gestion des relations
- Coverage tests ≥ 80% obligatoire
- Code quality gates automatiques

---

## Architecture

### Structure du projet

```
shopflow-main/
├── app/
│   ├── __init__.py                 # Export de l'app FastAPI
│   ├── main.py                     # Point d'entrée FastAPI
│   ├── models.py                   # ORM SQLAlchemy (Product, Cart, Order, etc.)
│   ├── schemas.py                  # Validation Pydantic pour API
│   ├── database.py                 # Session DB et moteur SQLAlchemy
│   ├── cache.py                    # Configuration Redis
│   ├── routes/                     # Endpoints FastAPI
│   │   ├── products.py             # GET/POST/PUT/DELETE produits
│   │   ├── cart.py                 # Gestion du panier
│   │   ├── orders.py               # Création et suivi commandes
│   │   └── coupons.py              # Gestion coupons de réduction
│   └── services/                   # Logique métier
│       ├── pricing.py              # Calculs prix, TVA, coupons
│       ├── stock.py                # Vérification/réservation stock
│       ├── cart.py                 # Service panier
│       └── order.py                # Service commandes
│
├── tests/
│   ├── conftest.py                 # Fixtures partagées pytest
│   ├── unit/                       # Tests unitaires isolés
│   │   ├── test_pricing.py         # 7 tests calcul prix
│   │   ├── test_stock.py           # 4 tests gestion stock
│   │   ├── test_cart.py            # 14 tests opérations panier
│   │   └── test_order.py           # 12 tests créations commandes
│   └── integration/                # Tests API end-to-end
│       ├── test_products_api.py    # 18 tests CRUD produits
│       ├── test_cart_api.py        # 6 tests API panier
│       ├── test_orders_api.py      # 10 tests API commandes
│       ├── test_health.py          # 4 tests santé application
│       └── test_faker_products.py  # 7 tests avec données aléatoires
│
├── Dockerfile                      # Image Docker production
├── docker-compose.yml              # Orchestration app + BD
├── docker-compose.ci.yml           # Stack Jenkins + SonarQube
├── docker-compose.staging.yml      # Déploiement staging
├── Jenkinsfile                     # Pipeline CI/CD 9 stages
├── requirements.txt                # Dépendances Python
├── pytest.ini                      # Configuration pytest markers
├── sonar-project.properties        # Configuration SonarQube
├── Makefile                        # Commandes courantes
└── README.md                       # Ce fichier
```

### Modèles de données

```python
Product
├── id (PK)
├── name
├── description
├── price
├── stock
└── created_at

Cart (per user_id)
├── id (PK)
├── user_id
├── CartItem* → product_id, quantity

Order
├── id (PK)
├── user_id
├── total_price
├── status (pending, confirmed, shipped)
├── OrderItem* → product_id, quantity, unit_price
└── Coupon* → reduction_percent

Coupon
├── id (PK)
├── code (unique)
├── reduction_percent (0 < x <= 100)
└── is_active
```

---

## Installation

### Prérequis

- Python 3.11+
- Docker & Docker Compose
- Git
- Redis (optionnel, intégré en Docker)
- PostgreSQL 14+ (ou SQLite pour dev)

### Étape 1 : Clone et setup

```bash
git clone https://github.com/votre-repo/shopflow-main.git
cd shopflow-main/shopflow-main
```

### Étape 2 : Créer l'environnement virtuel

```bash
# Windows PowerShell
python -m venv venv
venv\Scripts\activate.bat

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Étape 3 : Installer les dépendances

```bash
pip install -r requirements.txt
```

### Étape 4 : Configuration base de données

#### Option A : SQLite (développement)
```bash
# Automatique, créé au démarrage
python -m app.main
```

#### Option B : PostgreSQL (production)
```bash
# Dans .env
DATABASE_URL=postgresql://user:password@localhost:5432/shopflow

# Initialiser la BD
python -c "from app.database import init_db; init_db()"
```

### Étape 5 : Démarrer l'application

```bash
# Mode développement (rechargement auto)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Mode production (avec gunicorn)
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

L'API est accessible sur **http://localhost:8000**

---

## Usage

### Démarrer tous les services

```bash
# Copie complète : app + BD + Redis + cache
docker-compose up -d

# Vérifier l'état
docker-compose ps
docker logs shopflow-app
```

### Exemples d'utilisation API

#### Créer un produit

```bash
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "iPhone 15",
    "description": "Latest Apple phone",
    "price": 999.99,
    "stock": 50
  }'
```

**Réponse:**
```json
{
  "id": 1,
  "name": "iPhone 15",
  "price": 999.99,
  "stock": 50,
  "created_at": "2026-03-27T14:30:00Z"
}
```

#### Ajouter au panier

```bash
curl -X POST http://localhost:8000/api/cart/user123 \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity": 2
  }'
```

#### Appliquer un coupon

```bash
curl -X POST http://localhost:8000/api/cart/user123/apply-coupon \
  -H "Content-Type: application/json" \
  -d '{"code": "SUMMER20"}'
```

#### Créer une commande

```bash
curl -X POST http://localhost:8000/api/orders/user123 \
  -H "Content-Type: application/json" \
  -d '{
    "shipping_address": "123 Main St"
  }'
```

### Documentation interactive

Swagger UI : **http://localhost:8000/docs**
ReDoc : **http://localhost:8000/redoc**

---

## Tests

### Architecture de tests

```
Unit Tests (37)                    Integration Tests (45+)
├─ test_pricing.py (7)            ├─ test_products_api.py (18)
├─ test_stock.py (4)              ├─ test_cart_api.py (6)
├─ test_cart.py (14)              ├─ test_orders_api.py (10)
└─ test_order.py (12)             ├─ test_faker_products.py (7)
                                  └─ test_health.py (4)

Total: 82+ tests     Coverage: ≥80%     Max time: ~45s
```

### Exécuter les tests

```bash
# Tous les tests
pytest tests/ -v

# Tests unitaires uniquement
pytest tests/unit/ -v

# Tests d'intégration uniquement
pytest tests/integration/ -v

# Test spécifique
pytest tests/unit/test_pricing.py::TestCalculPrixTtc::test_prix_normal -v

# Avec coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
# Résultat HTML : htmlcov/index.html

# Avec markers
pytest tests/ -m unit  # Tests unitaires marqués
pytest tests/ -m integration  # Tests d'intégration

# Sans affichage des avertissements
pytest tests/ --tb=short -q
```

### Résultats attendus

```
tests/unit/test_pricing.py::TestCalculPrixTtc::test_prix_normal PASSED          [ 14%]
tests/unit/test_pricing.py::TestCalculPrixTtc::test_prix_zero PASSED            [ 15%]
...
tests/integration/test_products_api.py::TestListProducts::test_liste_vide_au_demarrage PASSED [ 95%]

===== 82 passed in 0.85s =====
Coverage: 96%
```

### Fixtures pytest

| Fixture | Scope | Usage |
|---------|-------|-------|
| `db_engine` | module | Moteur SQLAlchemy partagé |
| `db_session` | function | Session BD isolée par test |
| `client` | module | TestClient FastAPI |
| `product_sample` | function | Produit de test |
| `coupon_sample` | function | Coupon de test |
| `api_product` | module | Produit créé via API |
| `fake_product_data` | function | Données Faker |

---

## Advanced Testing & Security (TP4)

### Test-Driven Development (TDD)

ShopFlow utilise le cycle TDD complet pour les nouvelles fonctionnalités :

```
RED       -> GREEN      -> REFACTOR
Tests échouent → Minimum code → Amélioration
```

**Exemple : Validation avancée des coupons**

```bash
# Phase RED - Écrire tests AVANT le code
pytest tests/unit/test_coupon_tdd.py
# ImportError: cannot import name 'valider_coupon'  ← VOULU!

# Phase GREEN - Implémentation minimale
# Ajouter fonction valider_coupon() dans app/services/pricing.py
pytest tests/unit/test_coupon_tdd.py
# ✅ 11/11 PASSED

# Phase REFACTOR - Amélioration sans régression
# Extraire constantes → app/config.py
# Améliorer messages d'erreur
pytest tests/unit/test_coupon_tdd.py
# ✅ 11/11 PASSED (régression: 0)
```

**Bénéfices TDD validés :**
- Documentation vivante (tests = spécification)
- Refactoring sans peur (filet de sécurité)
- Couverture > 95% naturellement
- Design guidé par les besoins

### Performance Testing avec Locust

Testez la performance de l'API sous charge :

```bash
# Étape 1 : Créer données test
for i in $(seq 1 20); do
  curl -X POST http://localhost:8000/api/products/ \
    -H 'Content-Type: application/json' \
    -d "{\"name\": \"Produit $i\", \"price\": 50.99, \"stock\": 100}"
done

# Étape 2 : Lancer l'API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Étape 3 : Mode UI interactif
locust -f tests/perf/locustfile.py --host=http://localhost:8000
# → Ouvrir http://localhost:8089
# → Entrer : 50 users, spawn_rate=5, host=http://localhost:8000

# Étape 4 : Mode headless avec rapport HTML
locust -f tests/perf/locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  -u 50 -r 5 \
  --run-time 60s \
  --html=tests/perf/rapport_locust.html \
  --csv=tests/perf/resultats
```

**Seuils de performance ShopFlow :**

| Endpoint | p95 cible | p99 cible | Priorité |
|----------|-----------|-----------|----------|
| GET /health | < 50ms | < 100ms | Critique |
| GET /api/products/ | < 200ms | < 500ms | Haute |
| GET /api/products/{id} | < 150ms | < 300ms | Haute |
| POST /api/cart/ | < 300ms | < 700ms | Moyenne |
| POST /api/orders/ | < 500ms | < 1000ms | Moyenne |

**Interprétation rapport Locust :**
- 📊 Graphique 1 - Response times over time (stabilité latence)
- 📈 Graphique 2 - Distribution (identifier outliers)
- 📉 Graphique 3 - Requests/sec (débit système)

### Security Analysis avec Bandit

Analysez les vulnérabilités de sécurité :

```bash
# Scan complet avec rapport JSON
bandit -r app/ -f json -o bandit-report.json

# Rapport lisible (MEDIUM + HIGH seulement)
bandit -r app/ -ll

# Rapport HTML
bandit -r app/ -f html -o bandit-report.html

# Compter vulnérabilités par sévérité
python -c "
import json
data = json.load(open('bandit-report.json'))
from collections import Counter
sev = Counter(r['issue_severity'] for r in data['results'])
print('HIGH:', sev.get('HIGH', 0))
print('MEDIUM:', sev.get('MEDIUM', 0))
print('LOW:', sev.get('LOW', 0))
"
```

**Vulnérabilités corrigées en TP4 :**

| ID | Problème | ❌ AVANT | ✅ APRÈS |
|----|-----------|----------|----------|
| B105 | Hardcoded password | `REDIS_PASSWORD = 'admin123'` | `os.getenv('REDIS_PASSWORD', '')` |
| B501 | SSL verify=False | `requests.get(..., verify=False)` | `requests.get(..., verify=True)` |

**Common Security Issues (OWASP):**
- 🔐 B105 - Hardcoded password du code
- 🔒 B501 - SSL/TLS désactivé (MITM risk)
- 🪪 B301 - Pickle (RCE risk)
- 🌐 B320 - XXE (XML External Entity)
- ✔️ B308 - Markdown insane usage
- 🔑 B303 - MD5/SHA1 (weak hash)

---

## CI/CD Pipeline

### Infrastructure Jenkins

```bash
# Démarrer Jenkins + SonarQube
docker-compose -f docker-compose.ci.yml up -d

# Vérifier l'état
docker-compose -f docker-compose.ci.yml ps

# Jenkins : http://localhost:8080
# SonarQube : http://localhost:9000
```

### Pipeline stages (Jenkinsfile)

| Stage | Durée | Actions | Artefact |
|-------|-------|---------|----------|
| **Install** | 15s | `pip install -r requirements.txt` | — |
| **Lint** | 8s | `flake8 app/ --max-line-length=100` | — |
| **Unit Tests** | 12s | `pytest tests/unit/ -m unit` | junit-unit.xml |
| **Integration** | 18s | `pytest tests/integration/ -m integration` | junit-integration.xml |
| **Coverage** | 22s | `pytest --cov=app --cov-fail-under=80` | coverage.xml, htmlcov/ |
| **Static Analysis** | 15s | `pylint app/ && bandit -r app/` | — |
| **SonarQube** | 30s | `sonar-scanner` | Quality Gate |
| **Quality Gate** | 5s | `curl waitForQualityGate` | Pass/Fail |
| **Build+Deploy** | 20s | `docker build && docker push` | staging.yml deployment |

**Total Pipeline** : ~2 minutes

### Configuration Jenkins

#### 1. Créer un job Pipeline

```groovy
// New Job → Pipeline
Name: shopflow
Definition: Pipeline script from SCM
SCM: Git
Repository: https://github.com/votre-repo/shopflow-main
Script Path: Jenkinsfile
```

#### 2. Configurer les credentials

```bash
# SonarQube Token
Jenkins → Credentials → Add Credentials
Kind: Secret text
Secret: <votre_token_sonarqube>
ID: sonarqube-token
```

#### 3. Configurer SonarQube

```bash
# URL: Administration → Configuration → SonarQube servers
Name: SonarQube
URL: http://sonarqube:9000
Authentication token: sonarqube-token
```

### Webhooks GitHub

Pour déclenchement automatique sur chaque push :

```
GitHub → Settings → Webhooks → Add webhook
Payload URL: https://votre-jenkins.com/github-webhook/
Content type: application/json
Events: Push events
```

### Visualiser les résultats

- **Logs du pipeline** : Jenkins → shopflow → Build #N → Console Output
- **HTML Coverage** : Jenkins → shopflow → Build #N → Coverage Report (HTML)
- **SonarQube Dashboard** : http://localhost:9000 → Projects → shopflow
- **Test Reports** : Jenkins → shopflow → Build #N → Test Result

---

## Métriques de qualité

### Objectifs de couverture

```
COVERAGE TARGETS (Minimum 80%)

Module              Current  Target  Status      
app/models.py       98%      80%     PASS   
app/schemas.py      96%      80%     PASS   
app/services/       94%      80%     PASS   
app/routes/         92%      80%     PASS   
GLOBAL              96%      80%     PASS   
```

### Quality Gates SonarQube

```
✓ Code Smells: 0 (< 100)
✓ Bugs: 0 (= 0)
✓ Vulnerabilities: 0 (= 0)
Code Smells: 0 (< 100)
Bugs: 0 (= 0)
Vulnerabilities: 0 (= 0)
Duplicated Lines: 2.3% (< 3%)
Test Coverage: 96% (> 80%)
Maintainability: A
```

---

## Sécurité

### Bonnes pratiques implémentées

- Validation Pydantic : Tous les inputs validés côté schéma
- SQL Injection Prevention : Requêtes paramétrées via SQLAlchemy ORM
- CORS Configuration : Restrictif par défaut dans main.py
- Password Hashing : A implémenter pour auth users (bcrypt)
- Rate Limiting : A ajouter avec slowapi
- Security Scanning : Bandit + SonarQube dans pipeline
- Dependency Scanning : pip-audit
```bash
# Vérifier les vulnérabilités des dépendances
pip-audit

# Scan bandit (dans pipeline)
bandit -r app/ -ll

# SonarQube Security Hotspots
# http://localhost:9000 → Security → Hotspots
```

---

## 📝 Logging et monitoring

### Configuration logging

```python
import logging

logger = logging.getLogger(__name__)

# Dans app/main.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Logs importants

```
[INFO] Database connection established
[INFO] Redis cache connected
[ERROR] Stock verification failed for product_id=5
[WARNING] Coupon EXPIRING2024 expires in 3 days
[INFO] Order #42 created successfully
```

---

## 🐳 Déploiement avec Docker

### Build image

```bash
# Build local
docker build -t shopflow:latest .

# Build avec tag
docker build -t shopflow:v1.0.0 -t shopflow:latest .

# Push registry
docker tag shopflow:latest registry.example.com/shopflow:latest
docker push registry.example.com/shopflow:latest
```

### Staging deployment

```bash
# Déployer en staging
docker-compose -f docker-compose.staging.yml up -d

# Vérifier santé
curl http://localhost:8000/health

# Logs
docker-compose -f docker-compose.staging.yml logs -f shopflow-app
```

### Production checklist

- [ ] Variables d'environnement configurées
- [ ] Database migrations exécutées
- [ ] Secrets (DB_PASSWORD, API_KEY) définis
- [ ] Backups BD activés
- [ ] Monitoring/alerting actif
- [ ] Load balancer configuré
- [ ] SSL/TLS activé

---

## Contribution

### Workflow contribution

1. Fork le repository
2. Créer une branche feature : `git checkout -b feature/awesome-feature`
3. Commiter : `git commit -am 'Add awesome feature'`
4. Push : `git push origin feature/awesome-feature`
5. Pull Request vers `main`

### Code standards

- Formatage : `black app/`
- Linting : `flake8 app/ --max-line-length=100`
- Type hints : `mypy app/`
- Docstrings : Google style
- Tests : 1 test par fonctionnalité minimum

### Pre-commit hooks

```bash
# Installer
pip install pre-commit

# Setup
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
EOF

pre-commit install
```

---

## 📚 Ressources

### Documentation officielle

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [Pytest](https://docs.pytest.org/)
- [Pydantic v2](https://docs.pydantic.dev/latest/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [SonarQube](https://docs.sonarqube.org/)

### Tutoriels

- [Building APIs with FastAPI](https://testdriven.io/blog/fastapi-crud/)
- [Testing FastAPI Applications](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- [CI/CD with Jenkins](https://www.jenkins.io/doc/tutorials/)

---

## 📞 Support

### Troubleshooting

| Problème | Solution |
|----------|----------|
| Port 8000 déjà utilisé | `lsof -i :8000` et kill le process ou changer port |
| Redis connection failed | Vérifier `docker-compose ps`, relancer redis |
| Tests s'timeout | Augmenter `pytest_timeout` dans pytest.ini |
| Jenkins plugin manquant | Manage Jenkins → Plugin Manager → Install |
| SonarQube quality gate fail | Consulter http://localhost:9000/projects/shopflow |

### Issues

Pour signaler un bug ou feature request : [GitHub Issues](https://github.com/votre-repo/shopflow-main/issues)

---

## 📄 License

Ce projet est sous [MIT License](LICENSE)

---

## ✍️ Auteurs

- **Développement** : Classe SNOWFLOP 2026
- **Framework** : FastAPI + SQLAlchemy
- **CI/CD** : Jenkins + SonarQube

---

**Dernière mise à jour** : 27 Mars 2026
**Version** : 1.0.0
**Python** : 3.11+
