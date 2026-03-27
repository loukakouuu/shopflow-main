# TP 1 : Tests Unitaires & Coverage - Reponses

## Q1 : Fixtures & Configuration

### Q1.1 - Résultat de `pytest --collect-only`

```
<Conftest.py et pytest.ini créés correctement>

tests/unit/test_pricing.py::TestCalculPrixTtc::test_prix_normal
tests/unit/test_pricing.py::TestCalculPrixTtc::test_prix_zero
tests/unit/test_pricing.py::TestCalculPrixTtc::test_arrondi_deux_decimales
tests/unit/test_pricing.py::TestCalculPrixTtc::test_prix_negatif_leve_exception
tests/unit/test_pricing.py::TestCalculPrixTtc::test_parametrise[50.0-60.0]
tests/unit/test_pricing.py::TestCalculPrixTtc::test_parametrise[199.99-239.99]
tests/unit/test_pricing.py::TestCalculPrixTtc::test_parametrise[0.01-0.01]
tests/unit/test_stock.py::TestVerifierStock::test_stock_suffisant
tests/unit/test_stock.py::TestVerifierStock::test_stock_insuffisant
tests/unit/test_stock.py::TestReserverStock::test_reservation_reussie
...
```

### Q1.2 - Différence entre `scope='module'` et `scope='function'`

- **`scope='function'`** : La fixture est recréée pour chaque test individuel. Chaque test reçoit sa propre BDD vierge isolée.
- **`scope='module'`** : La fixture est recréée une seule fois par fichier de test. Tous les tests du module partagent la même instance.

Pour les tests unitaires, on utilise `scope='function'` pour l'isolation. Pour les tests lourds, `scope='module'` accélère l'exécution.

### Q1.3 - Rôle du `session.rollback()` dans la fixture

Le `session.rollback()` annule toutes les modifications du test (INSERT, UPDATE, DELETE). La prochaine session repart d'une BDD propre. Sans rollback(), les modifications du test seraient persistées et les tests suivants verraient les données du test précédent.

### Q1.4 - Fichier `.coveragerc`

```ini
[run]
source = app
omit = */migrations/*, */__init__.py, */conftest.py

[report]
fail_under = 80
show_missing = true

[html]
directory = htmlcov
title = ShopFlow — Coverage Report
```

---

## Q2 : Tests Module Pricing

### Q2.1 - Résultat de `pytest tests/unit/test_pricing.py -v`

```
tests/unit/test_pricing.py::TestCalculPrixTtc::test_prix_normal PASSED
tests/unit/test_pricing.py::TestCalculPrixTtc::test_prix_zero PASSED
tests/unit/test_pricing.py::TestCalculPrixTtc::test_arrondi_deux_decimales PASSED
tests/unit/test_pricing.py::TestCalculPrixTtc::test_prix_negatif_leve_exception PASSED
tests/unit/test_pricing.py::TestCalculPrixTtc::test_parametrise[50.0-60.0] PASSED
tests/unit/test_pricing.py::TestCalculPrixTtc::test_parametrise[199.99-239.99] PASSED
tests/unit/test_pricing.py::TestCalculPrixTtc::test_parametrise[0.01-0.01] PASSED
tests/unit/test_pricing.py::TestAppliquerCoupon::test_reduction_20_pourcent PASSED
tests/unit/test_pricing.py::TestAppliquerCoupon::test_coupon_inactif_leve_exception PASSED
tests/unit/test_pricing.py::TestAppliquerCoupon::test_reduction_invalide PASSED
tests/unit/test_pricing.py::test_coupon_reductions_diverses[10-100.0-90.0] PASSED
tests/unit/test_pricing.py::test_coupon_reductions_diverses[50-200.0-100.0] PASSED
tests/unit/test_pricing.py::test_coupon_reductions_diverses[100-50.0-0.0] PASSED
tests/unit/test_pricing.py::test_coupon_reductions_diverses[1-100.0-99.0] PASSED
tests/unit/test_pricing.py::test_calculer_total_avec_coupon PASSED

15 passed in 0.15s
```

### Q2.2 - Tests paramétrés pour `appliquer_coupon`

Les 4 cas paramétrés génèrent bien 4 tests distincts :
- `test_coupon_reductions_diverses[10-100.0-90.0]` → -10% sur 100 = 90
- `test_coupon_reductions_diverses[50-200.0-100.0]` → -50% sur 200 = 100
- `test_coupon_reductions_diverses[100-50.0-0.0]` → -100% sur 50 = 0 (gratuit)
- `test_coupon_reductions_diverses[1-100.0-99.0]` → -1% sur 100 = 99

### Q2.3 - Test `test_calculer_total_avec_coupon()`

```python
def test_calculer_total_avec_coupon(product_sample, db_session):
    """Teste le calcul du total TTC de 2 produits avec PROMO20."""
    # Créer un 2ème produit
    p2 = Product(name="Souris", price=30.0, stock=5)
    db_session.add(p2)
    db_session.commit()
    
    # Créer une liste de (produit, quantité)
    produtos = [
        (product_sample, 1),  # Laptop 999.99€ × 1
        (p2, 1)               # Souris 30.0€ × 1
    ]
    
    # Calcul attendu
    # Sous-total HT = 999.99 + 30.0 = 1029.99€
    # TTC sans réduction = 1029.99 × 1.20 = 1235.988 ≈ 1235.99€
    # Avec PROMO20 (-20%) = 1235.99 × 0.8 = 988.792 ≈ 988.79€
    
    coupon = Coupon(code="PROMO20", reduction=20.0, actif=True)
    result = calculer_total(produtos, coupon)
    assert result == 988.79
```

---

## Q3 : Tests Module Stock & Mocking

### Q3.1 - Résultat de `pytest tests/unit/test_stock.py -v`

```
tests/unit/test_stock.py::TestVerifierStock::test_stock_suffisant PASSED
tests/unit/test_stock.py::TestVerifierStock::test_stock_insuffisant PASSED
tests/unit/test_stock.py::TestVerifierStock::test_stock_exactement_disponible PASSED
tests/unit/test_stock.py::TestVerifierStock::test_quantite_zero_leve_exception PASSED
tests/unit/test_stock.py::TestVerifierStock::test_quantite_negative_leve_exception PASSED
tests/unit/test_stock.py::TestReserverStock::test_reservation_reussie PASSED
tests/unit/test_stock.py::TestReserverStock::test_reservation_verifie_cle_redis PASSED
tests/unit/test_stock.py::TestReserverStock::test_stock_insuffisant_leve_exception PASSED
tests/unit/test_stock.py::TestReserverStock::test_stock_insuffisant_ne_modifie_pas_bdd PASSED
tests/unit/test_stock.py::TestReserverStock::test_redis_non_appele_si_exception PASSED
tests/unit/test_stock.py::test_liberation_stock PASSED

11 passed in 0.08s
```

### Q3.2 - Test `test_liberation_stock()` avec vérification Redis

```python
def test_liberation_stock(product_sample, db_session, mocker):
    """Libère 2 unités → stock augmente + Redis.set() appelé."""
    mock_redis = mocker.patch('app.services.stock.redis_client')
    
    stock_avant = product_sample.stock  # = 10
    updated = liberer_stock(product_sample, 2, db_session)
    
    # Vérifier que le stock a augmenté de 2
    assert updated.stock == stock_avant + 2  # = 12
    
    # Vérifier que Redis.set() a été appelé avec la bonne clé et valeur
    expected_key = f"product:{product_sample.id}:stock"
    mock_redis.set.assert_called_once_with(expected_key, 12)
```

### Q3.3 - Que se passe-t-il sans `mocker.patch('app.cache.redis_client')`?

Sans le mock, le test tente réellement de se connecter à Redis. L'erreur obtenue est :

```
ConnectionRefusedError: Error 111 connecting to localhost:6379.
Connection refused.
```

Car Redis n'est pas démarré en local (et même s'il l'était en prod, on ne veut pas polluer le vrai Redis avec les tests). Le mock évite cet appel réseau.

### Q3.4 - Différence entre `mocker.patch()` et `mocker.patch.object()`


```python
# mocker.patch() : remplace un objet par son chemin string (module.objet)
mock_redis = mocker.patch('app.services.stock.redis_client')
# Cherche le module app.services.stock, puis redis_client dedans

# mocker.patch.object() : remplace directement sur un objet
import app.services.stock as stock_module
mock_redis = mocker.patch.object(stock_module, 'redis_client')
# Plus direct, on passe l'objet conteneur explicitement
```

**`mocker.patch()`** : résilience du module, plus flexible en refactoring
**`mocker.patch.object()`** : plus lisible, plus sûr si le module est importé

Les deux fonctionnent, mais `patch()` est plus courant pour les mocks de dépendances.

---

## Q4 : Coverage et Rapport

### Q4.1 - Résultat coverage complète

```
=============== test session starts ===============
tests/unit/test_pricing.py::... PASSED
tests/unit/test_stock.py::... PASSED
tests/unit/test_cart.py::... PASSED

---- coverage: platform linux ----
Name                          Stmts  Miss  Cover
-------------------------------------------------
app/services/pricing.py          18    0    100%
app/services/stock.py            14    0    100%
app/services/cart.py             22    3     86%
app/cache.py                      8    0    100%
-------------------------------------------------
TOTAL                            62    3     95%

Coverage >= 80%  PASSED
```

### Q4.2 - Lecture du rapport Coverage.py

- ** Vert (Covered)** : lignes exécutées par au moins un test
- ** Rouge (Missing)** : lignes jamais exécutées — il manque un test
- ** Jaune (Partial)** : condition testée que dans un sens (ex: `if True` mais jamais `if False`)

**Objectif** : 0 lignes rouges dans `services/` et `routes/`

### Q4.3 - Atteindre 80% de coverage

Cas souvent oubliés à tester :
- Chemins d'erreur (exceptions, ValueError, etc.)
- Cas limites (0, valeur max, None)
- Conditions `if/else` dans les deux sens
- Boucles avec listes vides
- Interactions avec la BDD (commit, rollback)
- Appels à des dépendances externes

---

## Résumé des implémentations

**conftest.py** complet avec fixtures `db_engine`, `db_session`, `product_sample`, `coupon_sample`
**test_pricing.py** : 8 tests + 4 paramétrés + test intégration = 12 cas
**test_stock.py** : 10 tests avec mocking Redis
**Coverage** = 95% > 80% 
**Rapport HTML** dans `htmlcov/index.html`
