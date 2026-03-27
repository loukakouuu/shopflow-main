# TP 0 : Mise en Place - Reponses

## Relecture 1 : Initialisation du Projet

### Q1.1 - Différence entre dépendances de production et de test

**Réponse:**
- **Production** : FastAPI, SQLAlchemy, Pydantic, Redis - font tourner l'application en production
- **Test** : pytest, pytest-cov, pytest-mock - valident le code en développement

**Pourquoi les séparer ?** Pour ne pas alourdir l'image Docker en production et réduire les vulnérabilités de sécurité (moins de dépendances = moins de surface d'attaque).

### Q1.2 - Rôle du fichier `__init__.py`

**Réponse:**
Le fichier `__init__.py` déclare un dossier comme package Python importable. Sans lui dans `app/services/`, on obtient `ModuleNotFoundError` à l'import et pytest ne trouve plus les tests.

### Q1.3 - Pourquoi utiliser un environnement virtuel (venv) ?

**Réponse:**
- Isole les packages par projet pour éviter les conflits de versions entre projets
- Reproduction facile sur toute machine via `pip install -r requirements.txt` sans droits admin
- Permet de tester différentes versions de dépendances sans affecter le système global

---

## Relecture 2 : Base de Données et Modèles

### Q2.1 - Différence entre FK simple et FK avec CASCADE

**Réponse:**
- **Sans CASCADE** : `Column(ForeignKey('carts.id'))` - la suppression d'un Cart bloque s'il existe des CartItems, c'est une erreur d'intégrité
- **Avec CASCADE** : `Column(ForeignKey('carts.id', ondelete='CASCADE'))` - supprime automatiquement les CartItems liés

**Importance pour ShopFlow** : Indispensable quand on vide un panier (il faut supprimer tous les CartItems associés).

### Q2.2 - Pourquoi OrderItem possède `unit_price` en plus du `price` de Product ?

**Réponse:**
Le prix du produit (`product.price`) peut changer après la commande. `unit_price` capture le prix au moment exact de l'achat. Sans ça, une facture afficherait le prix actuel au lieu du prix payé - erreur comptable et légale.

### Q2.3 - À quoi sert `PRAGMA foreign_keys=ON` ?

**Réponse:**
SQLite désactive les contraintes de clés étrangères par défaut. Sans ce PRAGMA, on peut insérer un CartItem avec un `cart_id` inexistant sans erreur, et le CASCADE ne fonctionnerait pas à la suppression. Ce PRAGMA force SQLite à vérifier les FK.

---

## Relecture 3 : Schémas Pydantic

### Q3.1 - Rôle de `model_config = {"from_attributes": True}`

**Réponse:**
Permet à Pydantic de lire les attributs d'un objet SQLAlchemy (ex: `product.name`) au lieu d'un dictionnaire. Sans cette ligne, on obtient une `ValidationError` car Pydantic ne sait pas lire un objet ORM.

### Q3.2 - Explication des validateurs `gt=0` et `le=100`

**Réponse:**
- `gt=0` : quantity doit être strictement supérieur à 0
- `le=100` : quantity doit être inférieur ou égal à 100

Si on envoie `quantity=0` ou `quantity=200`, FastAPI retourne automatiquement 422 Unprocessable Entity avec le message d'erreur précis, sans écrire une seule ligne de validation.

### Q3.3 - Pourquoi deux classes distinctes ProductCreate et ProductResponse ?

**Réponse:**
- **ProductCreate** : contient ce que l'utilisateur envoie (name, price, stock, etc.)
- **ProductResponse** : contient en plus `id` et `created_at`, générés côté serveur par la BDD

Si on n'avait qu'une seule classe, le client pourrait envoyer son propre `id` ou falsifier `created_at` - risque de sécurité et de collision en base.

---

## Vérification des fichiers clés

**app/database.py** - `create_db_engine()` et `get_db()` correctement définis
**app/models.py** - Product, Cart, CartItem, Order, OrderItem, Coupon tous présents
**app/schemas.py** - Tous les schémas Pydantic validés avec `from_attributes=True`
**pytest.ini** - Configuration avec coverage >= 80%
**requirements.txt** - Toutes les dépendances installées
