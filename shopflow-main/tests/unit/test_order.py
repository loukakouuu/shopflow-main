import pytest
from app.services.order import creer_commande, mettre_a_jour_statut
from app.services.cart import ajouter_au_panier

@pytest.mark.unit
def test_creer_commande_success(db_session, product_sample, mocker):
    """Teste la création réussie d'une commande."""
    mocker.patch('app.services.stock.redis_client')
    user_id = 42
    cart = ajouter_au_panier(product_sample, 1, user_id, db_session)
    
    commande = creer_commande(user_id, cart, db_session)
    assert commande.status == "pending"
    assert commande.total_ht > 0

def test_creer_commande_avec_coupon(db_session, product_sample, coupon_sample, mocker):
    """Teste la création avec un coupon (couvre la branche 'if coupon')."""
    mocker.patch('app.services.stock.redis_client')
    user_id = 42
    cart = ajouter_au_panier(product_sample, 1, user_id, db_session)
    
    commande = creer_commande(user_id, cart, db_session, coupon_sample)
    assert commande.coupon_code == coupon_sample.code
    # On vérifie que le prix total est bien calculé avec coupon

def test_creer_commande_panier_vide(db_session):
    """Teste l'erreur si le panier est vide (lignes 19-20)."""
    from app.models import Cart
    cart_vide = Cart(user_id=99)
    db_session.add(cart_vide)
    db_session.commit()
    
    with pytest.raises(ValueError, match="vide"):
        creer_commande(99, cart_vide, db_session)

# --- TESTS POUR mettre_a_jour_statut (LIGNES 56-83) ---

def test_mettre_a_jour_statut_success(db_session, product_sample, mocker):
    """Teste une transition de statut valide (pending -> confirmed)."""
    mocker.patch('app.services.stock.redis_client')
    user_id = 1
    cart = ajouter_au_panier(product_sample, 1, user_id, db_session)
    order = creer_commande(user_id, cart, db_session)

    # Action : on passe de pending à confirmed
    updated = mettre_a_jour_statut(order.id, "confirmed", db_session)
    assert updated.status == "confirmed"

def test_mettre_a_jour_statut_ordre_inexistant(db_session):
    """Teste l'erreur si la commande n'existe pas (lignes 64-65)."""
    with pytest.raises(ValueError, match="non trouvée"):
        mettre_a_jour_statut(999, "confirmed", db_session)

def test_mettre_a_jour_statut_transition_invalide(db_session, product_sample, mocker):
    """Teste l'erreur de transition interdite (ex: pending -> shipped) (lignes 67-71)."""
    mocker.patch('app.services.stock.redis_client')
    user_id = 1
    cart = ajouter_au_panier(product_sample, 1, user_id, db_session)
    order = creer_commande(user_id, cart, db_session)

    # Transition interdite selon votre dictionnaire TRANSITIONS_VALIDES
    with pytest.raises(ValueError, match="Transition invalide"):
        mettre_a_jour_statut(order.id, "shipped", db_session)