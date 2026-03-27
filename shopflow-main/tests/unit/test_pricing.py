import pytest
from app.services.pricing import calcul_prix_ttc, appliquer_coupon, calculer_total
from app.models import Coupon

# TESTS calcul_prix_ttc
@pytest.mark.unit
class TestCalculPrixTtc:
    def test_prix_normal(self):
        """Prix HT 100 -> TTC 120€ avec TVA 20%"""
        assert calcul_prix_ttc(100.0) == 120.0

    def test_prix_zero(self):
        assert calcul_prix_ttc(0.0) == 0.0

    def test_arrondi_deux_decimales(self):
        assert calcul_prix_ttc(10.0) == 12.0

    def test_prix_negatif_leve_exception(self):
        with pytest.raises(ValueError, match='invalide'):
            calcul_prix_ttc(-5.0)

    @pytest.mark.parametrize('ht,ttc', [
        (50.0, 60.0),
        (199.99, 239.99),
        (0.01, 0.01),
    ])
    def test_parametrise(self, ht, ttc):
        assert calcul_prix_ttc(ht) == ttc


# TESTS appliquer_coupon
class TestAppliquerCoupon:
    def test_reduction_20_pourcent(self, coupon_sample):
        result = appliquer_coupon(100.0, coupon_sample)
        assert result == 80.0

    def test_coupon_inactif_leve_exception(self, db_session):
        coupon_inactif = Coupon(code='OLD', reduction=10.0, actif=False)
        with pytest.raises(ValueError, match='inactif'):
            appliquer_coupon(100.0, coupon_inactif)

    def test_reduction_invalide(self, coupon_sample):
        coupon_invalide = Coupon(code='BAD', reduction=150.0, actif=True)
        with pytest.raises(ValueError):
            appliquer_coupon(100.0, coupon_invalide)

# Tests paramétrés pour appliquer_coupon
@pytest.mark.parametrize('reduction,prix_initial,prix_attendu', [
    (10, 100.0, 90.0),   # -10%
    (50, 200.0, 100.0),  # -50%
    (100, 50.0, 0.0),    # -100% (gratuit)
    (1, 100.0, 99.0),    # -1% (minimal)
])
def test_coupon_reductions_diverses(reduction, prix_initial, prix_attendu, db_session):
    coupon = Coupon(code=f'TEST{reduction}', reduction=float(reduction), actif=True)
    assert appliquer_coupon(prix_initial, coupon) == prix_attendu

def test_calculer_total_avec_coupon(coupon_sample):
    """
    Test du calcul total TTC avec 2 produits et une réduction de 20%.
    - Produit 1 : 50€ HT, quantité 1
    - Produit 2 : 30€ HT, quantité 2
    Total HT = 50 + (30 * 2) = 110€ HT
    Total TTC = 110 * 1.20 = 132€ TTC
    Avec coupon 20% = 132 * 0.80 = 105.60€ TTC
    """
    from app.models import Product
    
    # On crée nos faux produits (pas besoin de les sauvegarder en BDD pour ce test)
    produit_1 = Product(name="Casque", price=50.0)
    produit_2 = Product(name="Souris", price=30.0)
    
    # La liste attendue par calculer_total est une liste de tuples (Produit, quantité)
    liste_produits = [
        (produit_1, 1),
        (produit_2, 2)
    ]
    
    # On appelle la fonction
    resultat = calculer_total(liste_produits, coupon_sample)
    
    # On vérifie que le résultat final correspond au calcul manuel
    assert resultat == 105.60