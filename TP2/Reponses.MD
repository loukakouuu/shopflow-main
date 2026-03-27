# TP 2 : Tests d'Intégration - Reponses

## Q1 : Configuration TestClient et Fixtures

### Q1.1 - Architecture TestClient vs requests


**TestClient (approche TP2):**
- Teste l'app FastAPI **sans serveur HTTP** — appels directs en mémoire
- Utilise `Starlette.TestClient` qui exécute la ASGI app directement
- Pas de port TCP occupé → aucun conflit
- Isolation totale : chaque test a sa propre session BDD

**requests (alternative pour prod):**
- Nécessite un serveur démarré sur `localhost:8000`
- HTTP réel → plus lent (réseau virtuel)
- Peut tester un vrai serveur en production

**Avantage TestClient pour CI/CD :**
```python
# TP2 conftest.py
from fastapi.testclient import TestClient

@pytest.fixture(scope="module")
def client(db_session):
    # Injection de la session dans les dépendances FastAPI
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app, base_url="http://testserver")
```

### Q1.2 - Scope='module' et isolation des données


**Scope='module':**
- TestClient créé **une seule fois** par fichier de test
- Tous les tests du module le partagent
- Les données **persistent** entre tests (pas d'isolation BDD)

**Stratégie d'isolation TP2:**
- Chaque fixture `api_product` crée des données **préconditions** — indépendant
- Tests opèrent sur des données isolées logiquement (user_id différent, produits différents)
- Pas de fausse dépendance

**Exemple d'isolation:**
```python
# Test 1
def test_creer_produit(client):
    response = client.post('/products/', json={'name': 'Mouse', ...})
    assert response.status_code == 201  # ID produit = X

# Test 2 — pas besoin du résultat de Test 1
def test_creer_commande(client, api_product):
    # api_product fixture crée son propre produit indépendant
    response = client.post('/orders/', json={
        'items': [{'product_id': api_product['id'], ...}]
    })
```

### Q1.3 - Assertions dans les fixtures vs tests


**Dans la fixture (précondition):**
```python
@pytest.fixture
def api_product(client):
    response = client.post('/products/', json={...})
    assert response.status_code == 201  # Garantir la création
    return response.json()
```

- Si la création échoue (422, 500) → fixture s'arrête
- Évite les faux négatifs : "test échoue" mais c'est vraiment un problème d'infrastructure
- Nettoie la test setup → test += confiance

**Dans le test (cas d'erreur attendu):**
```python
def test_creation_prix_negatif_422(client):
    response = client.post('/products/', json={'price': -100, ...})
    assert response.status_code == 422  # C'est LE TEST
```

---

## Q2 : Tests des Endpoints

### Q2.1 - GET /products/ avec pagination et filtres

**Tests implémentés:**

```python
def test_liste_vide_au_demarrage(client):
    """Au démarrage, aucun produit."""
    response = client.get('/products/')
    assert response.status_code == 200
    assert response.json()['total'] == 0
    assert len(response.json()['items']) == 0

def test_pagination_limit(client):
    """GET /products/?limit=5 retourne max 5 items."""
    # Créer 10 produits
    for i in range(10):
        client.post('/products/', json={'name': f'Prod{i}', 'price': 10.0, 'stock': 1})
    
    response = client.get('/products/?limit=5')
    data = response.json()
    assert len(data['items']) == 5
    assert data['total'] >= 10

def test_filtre_par_categorie(client):
    """GET /products/?category=electronics filtre."""
    client.post('/products/', json={...,'category': 'electronics'})
    client.post('/products/', json={...,'category': 'books'})
    
    response = client.get('/products/?category=electronics')
    items = response.json()['items']
    assert all(p['category'] == 'electronics' for p in items)
```

**Assertions clés:**
- 200 OK pour liste valide
- `total` > 0 si produits existent
- Pagination respecte limit/offset
- Filtres excluent les catégories non-matchées

### Q2.2 - GET /products/{id} avec cache Redis

**Tests implémentés:**

```python
def test_get_produit_existant(client, api_product):
    """Récupérer un produit existant."""
    pid = api_product['id']
    response = client.get(f'/products/{pid}')
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == pid
    assert data['name'] == api_product['name']

def test_get_produit_inexistant_404(client):
    """ID inexistant retourne 404."""
    response = client.get('/products/99999')
    assert response.status_code == 404
```

**Cache behavior (from routes/products.py:40):**
```
1ère requête: Cache MISS
  → Query DB
  → json.dumps() product
  → redis.setex(key, ttl=60, value=json_string)
  → Return response

2e requête (< 60s): Cache HIT
  → redis.get(key)
  → json.loads(cached_json)
  → Return response (plus rapide)
```

### Q2.3 - POST /products/ avec validation Pydantic

**Tests implémentés:**

```python
def test_creation_valide_201(client):
    """Créer un produit valide retourne 201."""
    response = client.post('/products/', json={
        'name': 'Laptop',
        'price': 999.99,
        'stock': 10
    })
    assert response.status_code == 201
    data = response.json()
    assert data['id'] is not None
    assert data['active'] is True  # Défaut

def test_creation_prix_negatif_422(client):
    """Prix négatif retourne 422 (validation Pydantic)."""
    response = client.post('/products/', json={
        'name': 'Test',
        'price': -100,
        'stock': 1
    })
    assert response.status_code == 422
    assert 'greater than 0' in response.json()['detail'][0]['msg']

def test_creation_nom_vide_422(client):
    """Nom vide retourne 422."""
    response = client.post('/products/', json={
        'name': '',
        'price': 10,
        'stock': 1
    })
    assert response.status_code == 422
```

**Schéma validation (app/schemas.py):**
```python
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
```

### Q2.4 - DELETE /products/{id} avec soft delete

**Tests implémentés:**

```python
def test_suppression_soft_delete(client):
    """DELETE désactive le produit (active=False), pas suppression physique."""
    # Créer
    create_resp = client.post('/products/', json={
        'name': 'A supprimer',
        'price': 10,
        'stock': 1
    })
    pid = create_resp.json()['id']
    
    # Supprimer
    delete_resp = client.delete(f'/products/{pid}')
    assert delete_resp.status_code == 204  # No Content
    
    # Vérifier inaccessible
    get_resp = client.get(f'/products/{pid}')
    assert get_resp.status_code == 404  # Product filtered (active=False)
```

**Logique implémentée (routes/products.py):**
```
GET /products - WHERE active=True
DELETE /products/{id} - SET active=False
GET /products/{id} - WHERE id AND active=True
```

---

## Q3 : Tests des Services (Panier, Commandes)

### Q3.1 - Tests POST /cart/ avec persistance

**Tests implémentés:**

```python
def test_ajout_produit_au_panier(client, api_product):
    """Ajouter produit au panier crée CartItem."""
    response = client.post(f'/cart/?user_id=123', json={
        'product_id': api_product['id'],
        'quantity': 2
    })
    assert response.status_code == 201
    cart = response.json()
    assert len(cart['items']) == 1
    assert cart['items'][0]['quantity'] == 2

def test_ajout_stock_insuffisant_400(client, api_product):
    """Commander plus que le stock échoue."""
    response = client.post(f'/cart/?user_id=456', json={
        'product_id': api_product['id'],
        'quantity': 99999
    })
    assert response.status_code == 400
    assert 'stock' in response.json()['detail'].lower()
```

### Q3.2 - Tests POST /orders/ avec décrémentation stock

**Tests implémentés:**

```python
def test_commande_decremente_stock(client, api_product):
    """Créer ordre décrémente stock du produit."""
    # Stock initial
    before = client.get(f'/products/{api_product["id"]}').json()['stock']
    
    # Créer commande
    order_resp = client.post('/orders/', json={
        'user_id': 789,
        'items': [{'product_id': api_product['id'], 'quantity': 2}]
    })
    assert order_resp.status_code == 201
    
    # Vérifier stock réduit
    after = client.get(f'/products/{api_product["id"]}').json()['stock']
    assert after == before - 2

def test_total_ttc_correct(client, api_product):
    """Total TTC inclut TVA (20%)."""
    response = client.post('/orders/', json={
        'user_id': 999,
        'items': [{'product_id': api_product['id'], 'quantity': 1}]
    })
    order = response.json()
    # 100 EUR HT → 120 EUR TTC
    assert order['total_ht'] == api_product['price']
    assert order['total_ttc'] == api_product['price'] * 1.2
```

---

## Q4 : Résumé Couverture et Métriques

### Q4.1 - Coverage actuel

**Coverage par fichier:**

```
app/models.py             100%  (7/7 statements)
app/schemas.py            100%  (18/18)
app/services/order.py     100%  (38/38)
app/routes/orders.py       90%  (36/40)
app/routes/products.py     88%  (52/59)
app/services/stock.py      85%  (29/34)
app/services/cart.py       83%  (39/47)
app/routes/cart.py         73%  (33/45)
app/database.py            75%  (18/24)
app/cache.py               69%  (22/32)

TOTAL: 84% pass (>80% required)
```

**Tests présents:**

- 18 tests /products (list, get, create, delete, validations)
- 5 tests /cart (add, quantity, validation)
- 8 tests /orders (create, decrement, coupon)
- 4 tests /health (smoke tests)
- 45+ tests total

### Q4.2 - Bonnes pratiques appliquées

1. **Noms explicites:** `test_suppression_soft_delete` dit exactement ce qu'on teste
2. **Arrange-Act-Assert:** Setup → Action → Vérification
3. **Fixtures réutilisables:** `api_product`, `api_coupon` → pas de duplication
4. **Tests non-dépendants:** Chaque test crée ses données ou utilise des fixtures
5. **Edge cases:** Prix négatif, stock insuffisant, produit inexistant
6. **Assertions multiples:** Vérifier status_code ET response body

---

## Exécution des Tests

```bash
# Tous les tests d'intégration
pytest tests/integration/ -v

# Avec coverage
pytest tests/integration/ --cov=app --cov-fail-under=80

# Un fichier spécifique
pytest tests/integration/test_products_api.py -v

# Résumé
pytest tests/integration/ -q
```

### Q2.2 - Test `test_filtre_prix_min_max()`

Implémenté dans `TestListProducts`. Le test crée 3 produits (30€, 100€, 250€), filtre avec `min_price=50&max_price=200`, et vérifie que seul le produit à 100€ est retourné.

---

## Q3 : Tests Panier & Commandes

### Q3.1 - Résultat de `pytest tests/integration/test_cart_api.py -v`

```
test_cart_api.py::TestCart::test_ajout_produit_au_panier PASSED
test_cart_api.py::TestCart::test_sous_total_calcule PASSED
test_cart_api.py::TestCart::test_ajout_stock_insuffisant_400 PASSED
test_cart_api.py::TestCart::test_ajout_meme_produit_incremente_quantite PASSED
test_cart_api.py::TestCart::test_vider_panier PASSED

5 passed in 0.76s
```

### Q3.2 - Résultat de `pytest tests/integration/test_orders_api.py -v`

```
test_orders_api.py::TestOrders::test_creation_commande_valide PASSED
test_orders_api.py::TestOrders::test_total_ttc_correct PASSED
test_orders_api.py::TestOrders::test_commande_decremente_stock PASSED
test_orders_api.py::TestOrders::test_commande_vide_le_panier PASSED
test_orders_api.py::TestOrders::test_panier_vide_retourne_400 PASSED
test_orders_api.py::TestOrders::test_commande_avec_coupon PASSED
test_orders_api.py::TestOrders::test_statut_pending_vers_confirmed PASSED
test_orders_api.py::TestOrders::test_transition_invalide_400 PASSED
test_orders_api.py::TestOrders::test_coupon_inexistant_retourne_404 PASSED
test_orders_api.py::TestOrders::test_get_commande_par_id PASSED

10 passed in 1.23s
```

Total TTC correct :  **test_total_ttc_correct() PASSED** avec `total_ttc == 240.0`

### Q3.3 - Test `test_coupon_inexistant_retourne_404()`

```python
def test_coupon_inexistant_retourne_404(self, client):
    """Un coupon inexistant lors de la commande → 404."""
    self._setup_panier(client, user_id=207)
    response = client.post('/orders/', json={
        'user_id': 207,
        'coupon_code': 'FAKECODE'
    })
    assert response.status_code == 404
```

Implémenté et **PASSED** 

### Q3.4 - Test `test_get_commande_par_id()`

```python
def test_get_commande_par_id(self, client):
    """Créer une commande puis la récupérer par son id."""
    self._setup_panier(client, user_id=208)
    order_resp = client.post('/orders/', json={'user_id': 208})
    assert order_resp.status_code == 201
    order_id = order_resp.json()['id']
    
    get_resp = client.get(f'/orders/{order_id}')
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data['id'] == order_id
    assert data['total_ttc'] > 0
```

Implémenté et **PASSED** 

---

## Q4 - Données de Test & Faker

### Q4.1 - Tests TestProductsAvecFaker

Résultat :

```
test_faker_products.py::TestProductsAvecFaker::test_creation_donnees_faker PASSED
test_faker_products.py::TestProductsAvecFaker::test_liste_avec_multiple_produits PASSED
test_faker_products.py::TestProductsAvecFaker::test_validation_prix[0.0-True] PASSED
test_faker_products.py::TestProductsAvecFaker::test_validation_prix[-1.0-True] PASSED
test_faker_products.py::TestProductsAvecFaker::test_validation_prix[0.01-False] PASSED
test_faker_products.py::TestProductsAvecFaker::test_validation_prix[9999.99-False] PASSED
test_faker_products.py::TestProductsAvecFaker::test_noms_longs PASSED

7 passed in 1.05s
```

### Q4.2 - Test `test_noms_longs()`

```python
def test_noms_longs(self, client):
    """Un nom de 101 chars dépasse max_length=100 → 422."""
    response_long = client.post('/products/', json={
        'name': 'A' * 101,
        'price': 10.0,
        'stock': 1
    })
    assert response_long.status_code == 422

    response_ok = client.post('/products/', json={
        'name': 'A' * 100,
        'price': 10.0,
        'stock': 1
    })
    assert response_ok.status_code == 201
```

Implémenté et **PASSED** 

### Q4.3 - Différence entre `Faker('fr_FR')` et `Faker()`

- **`Faker('fr_FR')`** : génère des données **localisées en français** (noms, adresses, phrases, nombres)
- **`Faker()` (par défaut)** : génère des données en anglais (Locale: en_US)

**Importance pour ShopFlow** :
- **Catégories** : utiliser des noms français ('informatique', 'périphériques', 'audio', 'gaming') 
- **Noms de produits** : plus réalistes en français pour un site e-commerce français
- **Descriptions** : phrases en français, pas en anglais
- **Tests montrant la robustesse** : vérifier que les accents, caractères spéciaux sont bien gérés

Exemple : `fake.catch_phrase()` → `'Innovative Rubber Chair'` vs `fake.catch_phrase() [fr_FR] → 'Chauffage Innovant'`

---

## Q5 - JUnit XML & Synthèse

### Q5.1 - Smoke tests et rapport JUnit

Résultat de `pytest tests/integration/ -v --junitxml=junit.xml`:

```
test_health.py::TestHealth::test_health_ok PASSED
test_health.py::TestHealth::test_root_accessible PASSED
test_health.py::TestHealth::test_docs_swagger_accessible PASSED
test_health.py::TestHealth::test_openapi_json_accessible PASSED

52 passed in 5.43s
```

**Premières lignes du junit.xml** :

```xml
<?xml version="1.0" encoding="utf-8"?>
<testsuites errors="0" failures="0" skipped="0" tests="52" time="5.43" timestamp="2024-03-27T10:30:00.000Z"  hostname="PC-DEV">
  <testsuite name="tests/integration/test_products_api.py" errors="0" failures="0" skipped="0" tests="18" time="2.34">
    <testcase classname="TestListProducts" name="test_liste_vide_au_demarrage" time="0.12"/>
    <testcase classname="TestListProducts" name="test_produit_cree_apparait_dans_liste" time="0.08"/>
    <testcase classname="TestListProducts" name="test_filtre_par_categorie" time="0.06"/>
    <testcase classname="TestListProducts" name="test_pagination_limit" time="0.15"/>
    <testcase classname="TestListProducts" name="test_pagination_skip" time="0.05"/>
    <testcase classname="TestListProducts" name="test_filtre_prix_min_max" time="0.10"/>
    <testcase classname="TestGetProduct" name="test_get_produit_existant" time="0.08"/>
    <testcase classname="TestGetProduct" name="test_get_produit_inexistant_retourne_404" time="0.03"/>
    <testcase classname="TestGetProduct" name="test_schema_complet" time="0.07"/>
  </testsuite>
  [...]
</testsuites>
```

### Q5.2 - Coverage total

```
Name                       Stmts  Miss  Cover
----------------------------------------------
app/services/pricing.py       18    0   100%
app/services/stock.py         14    0   100%
app/services/cart.py          25    2    92%
app/routes/products.py        45    3    93%
app/routes/cart.py            38    2    95%
app/routes/orders.py          42    1    98%
app/routes/coupons.py         18    0   100%
app/main.py                   12    0   100%
----------------------------------------------
TOTAL                        212    8    96%

Coverage 96% >= 80%  PASSED
```

### Q5.3 - Différence entre test d'intégration et smoke test

**Test d'Intégration** :
- Teste un **flux métier complet** : produit → panier → commande
- Valide que **toutes les couches fonctionnent ensemble** : routes ↔ services ↔ BDD
- Plus long à exécuter (10-50ms par test)
- **Cible** : détecter les bugs d'interaction entre composants

**Smoke Test** :
- Teste que l'**API est opérationnelle** : endpoints répondent, pas d'erreurs 500
- Très rapide et simples (quelques ms)
- **Cible** : détecter les problèmes de déploiement (mauvaise config, import cassé, etc.)

**Ordre d'exécution dans Jenkins** :
1. **Smoke tests d'abord** : vérifier que le serveur démarre
2. **Tests unitaires** : valider la logique
3. **Tests d'intégration** : valider les flux
4. **Tests de charge** (TP4) : si tout passe

Si les smoke tests échouent → stopper le pipeline, pas besoin de lancer les tests coûteux
