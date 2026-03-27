import pytest
from app.services.cart import ajouter_au_panier, vider_panier, calculer_sous_total
from app.models import Cart

@pytest.mark.unit
def test_ajouter_nouveau_produit(db_session, product_sample):
    user_id = 42
    cart = ajouter_au_panier(product_sample, 1, user_id, db_session)
    assert len(cart.items) == 1

def test_ajouter_produit_existant_augmente_quantite(db_session, product_sample):
    user_id = 42
    ajouter_au_panier(product_sample, 1, user_id, db_session)
    # On rajoute 2 unités du même produit
    cart = ajouter_au_panier(product_sample, 2, user_id, db_session)
    db_session.refresh(cart, ['items'])
    assert cart.items[0].quantity == 3

def test_ajouter_produit_stock_insuffisant(db_session, product_sample):
    with pytest.raises(ValueError, match="insuffisant"):
        ajouter_au_panier(product_sample, 999, 42, db_session)

def test_calculer_total_panier_vide():
    assert abs(calculer_sous_total(Cart(items=[])) - 0.0) < 0.01

def test_vider_panier_complet(db_session, product_sample):
    user_id = 42
    cart = ajouter_au_panier(product_sample, 1, user_id, db_session)
    vider_panier(cart, db_session)
    db_session.refresh(cart)
    assert len(cart.items) == 0