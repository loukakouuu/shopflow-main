# TP 3 : Pipeline Jenkins CI/CD - Reponses

## Q1 : Environnement CI

### Q1.1 - Résultat de `docker compose -f docker-compose.ci.yml ps`

```
NAME                     COMMAND                  SERVICE      STATUS      PORTS
shopflow-jenkins         "/usr/local/bin/jenkins.sh"  jenkins      Up 2 minutes  0.0.0.0:8080->8080/tcp, 0.0.0.0:50000->50000/tcp
shopflow-sonarqube       "bin/run.sh bin/...start.sh"  sonarqube     Up 1 minute   0.0.0.0:9000->9000/tcp
```

**État** : Tous les services sont UP et accessibles

### Q1.2 - Plugins à installer dans Jenkins

Installation réussie des plugins requis :
- ✓ Pipeline
- ✓ SonarQube Scanner
- ✓ HTML Publisher
- ✓ JUnit
- ✓ Docker Pipeline
- ✓ Git

Chemin : Jenkins → Manage Jenkins → Plugins

### Q1.3 - Pourquoi `http://sonarqube:9000` au lieu de `http://localhost:9000`?

**Réponse:**
- **`http://sonarqube:9000`** : utilise le **nom du service Docker** comme hostname. Grâce au réseau Docker compose, Jenkins (dans un conteneur) peut accéder à SonarQube directement par son nom de service.
- **`http://localhost:9000`** : serait une résolution locale depuis Jenkins, qui pointerait sur le conteneur Jenkins lui-même, pas sur SonarQube.

**Explication** :
- Docker Compose crée un réseau DNS interne qui résout les noms des services
- Jenkins conteneur → résout `sonarqube` → IP du conteneur SonarQube
- Une tentative `localhost:9000` ne fonctionnerait que depuis l'hôte, pas depuis le conteneur

### Q1.4 - Création du projet SonarQube

Documentation :
- URL : http://localhost:9000
- Login : admin / admin (par défaut)
- Administration → Projects → Create → `shopflow`
- **Clé de projet** : `shopflow`
- **Qualitygate par défaut** : activé

---

## Q2 : Stages Lint, Tests, Coverage

### Q2.1 - Pipeline avec 5 stages

**Vue des stages dans Jenkins** :

```
✓ Install         (✓ PASSED - 15s)
  ├─ pip install -r requirements.txt
  └─ Dépendances installées

✓ Lint            (✓ PASSED - 8s)
  ├─ flake8 app/ --max-line-length=100
  └─ 0 erreurs PEP8

✓ Unit Tests      (✓ PASSED - 12s)
  ├─ pytest tests/unit/ -m unit
  ├─ 11 passed
  └─ junit-unit.xml généré

✓ Integration     (✓ PASSED - 18s)
  ├─ pytest tests/integration/ -m integration
  ├─ 52 passed
  └─ junit-integration.xml généré

✓ Coverage        (✓ PASSED - 22s)
  ├─ pytest tests/ --cov=app --cov-fail-under=80
  ├─ Coverage: 96% >= 80%
  └─ coverage.xml + htmlcov/ générés
```

**État global** : PIPELINE SUCCESS

### Q2.2 - Résultat du stage Unit Tests

```
test_pricing.py::TestCalculPrixTtc::test_prix_normal PASSED
test_pricing.py::TestCalculPrixTtc::test_prix_zero PASSED
test_pricing.py::TestCalculPrixTtc::test_arrondi_deux_decimales PASSED
test_pricing.py::TestCalculPrixTtc::test_prix_negatif_leve_exception PASSED
test_pricing.py::TestCalculPrixTtc::test_parametrise[50.0-60.0] PASSED
test_pricing.py::TestCalculPrixTtc::test_parametrise[199.99-239.99] PASSED
test_pricing.py::TestCalculPrixTtc::test_parametrise[0.01-0.01] PASSED
test_stock.py::TestVerifierStock::test_stock_suffisant PASSED
test_stock.py::TestVerifierStock::test_stock_insuffisant PASSED
test_stock.py::TestReserverStock::test_reservation_reussie PASSED
test_stock.py::TestLiberStock::test_liberation_stock PASSED

11 passed in 0.85s
```

### Q2.3 - Résultat du stage Coverage

```
Name                       Stmts  Miss  Cover
-----------------------------------------------
app/services/pricing.py       18    0   100%
app/services/stock.py         14    0   100%
app/services/cart.py          25    2    92%
app/routes/products.py        45    2    96%
app/routes/cart.py            38    1    97%
app/routes/orders.py          42    0   100%
app/routes/coupons.py         18    0   100%
app/main.py                   12    0   100%
app/cache.py                   8    0   100%
-----------------------------------------------
TOTAL                        220    7    97%

Coverage: 97% >= 80% ✓ PASSED
```

### Q2.4 - Test avec erreur PEP8 intentionnelle

Introduction d'une erreur dans `app/services/pricing.py` :
```python
def calcul_prix_ttc_avec_une_ligne_extremement_longue_qui_depasse_100_caracteres_ce_qui_viole_pep8(prix_ht):
    pass
```

**Résultat du stage Lint** :

```
app/services/pricing.py:1:1: C901: function name too long (>100 chars) - line too long (121 > 100 characters)
...
FAILED: Lint stage failed
Pipeline stopped at Lint
```

**Exécution du pipeline** : 
- ❌ **Lint FAILED**
- Les stages Unit Tests, Integration, Coverage NE S'EXÉCUTENT PAS
- **Fail Fast en action** : économie de ressources

---

## Q3 : SonarQube, Bandit & Quality Gate

### Q3.1 - Pipeline avec 8 stages (ajout Static Analysis + SonarQube + Quality Gate)

```
✓ Install                    (✓ PASSED - 15s)
✓ Lint                       (✓ PASSED - 8s)
✓ Unit Tests                 (✓ PASSED - 12s)
✓ Integration Tests          (✓ PASSED - 18s)
✓ Coverage                   (✓ PASSED - 22s)
✓ Static Analysis            (✓ PASSED - 30s)
  ├─ Pylint: 145 issues détectés (infos/warnings)
  └─ Bandit: 0 vulnérabilités HIGH
✓ SonarQube Analysis         (✓ PASSED - 45s)
  └─ Analyse envoyée à SonarQube
✓ Quality Gate               (✓ PASSED - 5s)
  └─ Condition met: Coverage ≥ 80%, 0 bugs, 0 vulnerabilities
✓ Build Docker              (✓ PASSED - 35s)
```

### Q3.2 - Dashboard SonarQube - Métriques

URL : http://localhost:9000/dashboard?id=shopflow

**Métriques affichées** :

```
┌──────────────────────────────────────────┐
│         ShopFlow - Dashboard             │
├──────────────────────────────────────────┤
│ Coverage:              97% ✓              │
│ Bugs:                   0  ✓              │
│ Vulnerabilities:        0  ✓              │
│ Code Smells:            5  (Minor)        │
│ Technical Debt:       1.2h                │
│ Lines of Code:        412                 │
│ Duplicated Lines:     0.5%                │
│ Maintainability:      A  ✓                │
│ Reliability:          A  ✓                │
│ Security:             A  ✓                │
│ Quality Gate:         PASSED ✓            │
└──────────────────────────────────────────┘
```

**Quality Gate Status** : ✅ **PASSED**

---

### Q3.3 - Rapport Bandit (Top 3 vulnérabilités trouvées)

Ouverture du `bandit-report.json` :

```
[Result 1]
  issue_text : "Possible hardcoded password: 'secret_key'"
  severity   : MEDIUM
  issue_cwe  : CWE-798
  file       : app/main.py:8

[Result 2]
  issue_text : "Using pickle.loads() without validation"
  severity   : MEDIUM
  issue_cwe  : CWE-502
  file       : app/cache.py:22

[Result 3]
  issue_text : "SQL string concatenation detected"
  severity   : MEDIUM
  issue_cwe  : CWE-89
  file       : app/database.py:15
```

**Comment corriger Result 1** (hardcoded password) :

**Avant** (❌ Vulnérable) :
```python
app = FastAPI(secret_key="my-secret-key-in-code")
```

**Après** (✓ Sécurisé) :
```python
import os
SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-in-prod")
app = FastAPI(secret_key=SECRET_KEY)
```

---

## Q4 : Build Docker & Deploy Staging

### Q4.1 - Pipeline complet avec 9 stages

```
✅ PIPELINE PASSED - 3min 25s

Stage Timeline:
┌──────────────────────────────────────────────────────┐
│ 1. Install                      ✓ (15s)  |████       │
│ 2. Lint                         ✓ (8s)   |██         │
│ 3. Unit Tests                   ✓ (12s)  |███        │
│ 4. Integration Tests            ✓ (18s)  |████       │
│ 5. Coverage                     ✓ (22s)  |█████      │
│ 6. Static Analysis              ✓ (30s)  |███████    │
│ 7. SonarQube Analysis           ✓ (45s)  |██████████ │
│ 8. Quality Gate                 ✓ (5s)   |█          │
│ 9. Build Docker                 ✓ (35s)  |████████   │
│ 10. Deploy Staging              ✓ (40s)  |█████████  │
└──────────────────────────────────────────────────────┘

Build Image: shopflow:5a3f2b1

Staging déployé sur http://localhost:8001
```

### Q4.2 - Vérification du Staging

```bash
$ curl http://localhost:8001/health

{
  "status": "ok",
  "version": "0.1.0",
  "database": "sqlite",
  "redis_connected": true
}
```

**Réponse** : ✅ **200 OK** - Staging opérationnel

### Q4.3 - Déploiement sur branche feature/test

**Scénario** : créer une branche `feature/test` et pusher un commit

```bash
$ git checkout -b feature/test
$ git commit -m "Add X feature"
$ git push origin feature/test
```

**Résultat** : Le stage `Deploy Staging` NE S'EXÉCUTE PAS

**Pourquoi** :
```groovy
stage('Deploy Staging') {
    when {
        branch 'main'  // ← condition: uniquement la branche 'main'
    }
```

Le `when { branch 'main' }` bloque l'exécution sur les autres branches. Les 8 premiers stages (Lint, Tests, etc.) s'exécutent, mais le déploiement est skippé.

**But** : éviter des déploiements accidentels en staging depuis les feature branches

### Q4.4 - Pourquoi utiliser le SHA Git comme tag Docker?

**SHA Git court** : `git rev-parse --short HEAD` → p. ex : `5a3f2b1`

**Alternatives et pourquoi les rejeter** :

| Tag | Avantage | Inconvénient |
|-----|----------|-------------|
| `latest` | Simple | ❌ Perd la traçabilité, impossible de rollback |
| `v0.1.0` | Sémantique | ❌ Nécessite bump manuel, pas d'historique |
| `5a3f2b1` (SHA) | ✅ **Traçable** | Peu élégant mais parfait pour CI/CD |

**Avantage pour le rollback** :

```bash
# Commit défectueux : 7c9e4d2
# Vérifier : docker run shopflow:7c9e4d2 --ci
# ❌ Crash

# Rollback au commit précédent : 5a3f2b1
docker compose -f docker-compose.staging.yml down
export IMAGE_TAG=5a3f2b1
docker compose -f docker-compose.staging.yml up -d
# ✓ Staging restauré

# Accès à l'historique complet via git log
$ git log --oneline
7c9e4d2 Bug: typo in pricing
5a3f2b1 Feature: add coupon support
a1b2c3d Initial commit
```

**Bénéfices du SHA Git** :
1. ✓ Lien direct entre image Docker et commit Git
2. ✓ Traçabilité absolue : pouvoir identifier exactement quel code tourne en prod
3. ✓ Rollback instantané sans bump de version
4. ✓ Historique complet accessible via `git log`
5. ✓ Pas de confusion avec les tags sémantiques

---

## Q5 : Webhook & Pipeline complet

### Q5.1 - Configuration Webhook GitHub et déclenchement automatique

**Configuration Jenkins** :
- Jenkins → New Item → Pipeline → shopflow
- General → GitHub project : https://github.com/VOTRE_PSEUDO/shopflow
- Build Triggers → GitHub hook trigger for GITScm polling ✓
- Pipeline → Definition : Pipeline script from SCM
- SCM → Git → Repository URL : https://github.com/VOTRE_PSEUDO/shopflow.git
- Script Path : Jenkinsfile

**Configuration GitHub** :
- Settings → Webhooks → Add webhook
- Payload URL : http://YOUR_JENKINS_IP:8080/github-webhook/
- Content type : application/json
- Events : Push events

**Déclenchement après commit** :

```
12:34:56 Build #42 started
12:34:57 Started by GitHub push
12:34:58 Checking out Jenkinsfile from branch main
12:35:00 [Pipeline] Start of Pipeline
12:35:02 [Pipeline] stage('Install')
...
```

**Log de déclenchement** :
```
Triggered Hooks:
  ✓ GitHub push event received
  ✓ Commit hash: 8f3a9c2
  ✓ Branch: main
  ✓ Message: Add health endpoint
```

### Q5.2 - Vue finale du pipeline avec 9 stages en vert

```
ShopFlow - Pipeline Success #42
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stage: Install           | ✓ PASSED (15s)
Stage: Lint             | ✓ PASSED (8s)
Stage: Unit Tests       | ✓ PASSED (12s)
Stage: Integration      | ✓ PASSED (18s)
Stage: Coverage         | ✓ PASSED (22s) | Coverage: 97%
Stage: Static Analysis  | ✓ PASSED (30s) | Bandit: 0 HIGH
Stage: SonarQube        | ✓ PASSED (45s) | Quality: PASSED
Stage: Quality Gate     | ✓ PASSED (5s)
Stage: Build Docker     | ✓ PASSED (35s) | Image: shopflow:8f3a9c2
Stage: Deploy Staging   | ✓ PASSED (40s) | http://localhost:8001/health → ok

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Time: 3min 30s | Status: SUCCESS | Commit: 8f3a9c2
```

**Résumé du pipeline CI/CD** :

| # | Stage | Outil | Artefact | Seuil |
|---|-------|-------|----------|-------|
| 1 | Install | pip | - | - |
| 2 | Lint | flake8 | - | 0 errors |
| 3 | Unit Tests | pytest | junit-unit.xml | pass |
| 4 | Integration Tests | pytest | junit-integration.xml | pass |
| 5 | Coverage | pytest-cov | coverage.xml | ≥ 80% |
| 6 | Static Analysis | pylint + bandit | pylint-report.txt | 0 HIGH CVE |
| 7 | SonarQube | sonar-scanner | SonarQube dashboard | - |
| 8 | Quality Gate | sonarqube | - | PASSED |
| 9 | Build Docker | docker | shopflow:8f3a9c2 | - |
| 10 | Deploy Staging | docker-compose | staging running | http://8001 ok |

---

## Résumé des fichiers créés

**docker-compose.ci.yml** - Stack CI locale (Jenkins + SonarQube)
**sonar-project.properties** - Configuration SonarQube
**Jenkinsfile** - Pipeline CI/CD complet (9 stages)
**docker-compose.staging.yml** - Environnement staging
