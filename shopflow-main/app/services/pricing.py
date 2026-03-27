# app/services/pricing.py
from typing import Optional, List, Tuple
from app.models import Product, Coupon
from app.config import TVA_RATE, MONTANT_MINIMUM_COUPON, MONTANT_MINIMUM_GRATUIT


def calcul_prix_ttc(prix_ht: float) -> float:
    if prix_ht < 0:
        raise ValueError(f"Prix HT invalide : {prix_ht}.")
    return round(prix_ht * (1 + TVA_RATE), 2)


def appliquer_coupon(prix: float, coupon: Coupon) -> float:
    if not coupon.actif:
        raise ValueError(f"Coupon inactif : {coupon.code}")
    if not 0 < coupon.reduction <= 100:
        raise ValueError(f"Réduction invalide : {coupon.reduction}.")
    return round(prix * (1 - coupon.reduction / 100), 2)


def calculer_total(
    produits: List[Tuple[Product, int]],
    coupon: Optional[Coupon] = None
) -> float:
    if not produits:
        return 0.0
    total_ht = sum(p.price * q for p, q in produits)
    total_ttc = calcul_prix_ttc(total_ht)
    if coupon:
        total_ttc = appliquer_coupon(total_ttc, coupon)
    return total_ttc


def calculer_remise(prix_original: float, prix_final: float) -> float:
    if prix_original <= 0:
        raise ValueError(f"Prix original invalide : {prix_original}")
    return round((1 - prix_final / prix_original) * 100, 2)


def valider_coupon(coupon: Coupon, panier_total: float) -> bool:
    """
    Valide qu'un coupon peut être appliqué sur un panier.
    
    Vérifie les règles métier pour l'application d'un coupon :
    1. Le coupon doit être actif (coupon.actif == True)
    2. La réduction doit être dans l'intervalle ]0, 100] (0 < réduction <= 100)
    3. Le panier doit atteindre le montant minimum (>= 10€)
    4. Un coupon gratuit (réduction=100) nécessite panier >= 50€
    
    Args:
        coupon (Coupon): L'objet Coupon à valider contenant code, reduction, actif
        panier_total (float): Le montant total du panier en euros
        
    Returns:
        bool: True si toutes les conditions sont respectées
        
    Raises:
        ValueError: Si une règle est violée avec message explicite incluant :
                   - Le type de violation (inactif, réduction invalide, etc.)
                   - Les montants requis et actuels si applicable
                   
    Examples:
        >>> coupon = Coupon(code='PROMO20', reduction=20.0, actif=True)
        >>> valider_coupon(coupon, 50.0)
        True
        >>> coupon_gratuit = Coupon(code='FREE', reduction=100.0, actif=True)
        >>> valider_coupon(coupon_gratuit, 30.0)  # Panier insuffisant pour FREE
        Traceback (most recent call last):
            ...
        ValueError: Coupon 100% gratuit - montant minimum requis : 50.0€, panier actuel : 30.0€
    """
    # Règle 1 : Coupon actif
    if not coupon.actif:
        raise ValueError(
            f"Coupon '{coupon.code}' inactif - impossible à appliquer"
        )
    
    # Règle 2 : Réduction valide (0 < réduction <= 100)
    if not (0 < coupon.reduction <= 100):
        raise ValueError(
            f"Coupon '{coupon.code}' - Réduction invalide ({coupon.reduction}%). "
            f"Doit être entre 0 (exclus) et 100 (inclus)."
        )
    
    # Règle 3 : Montant minimum du panier (10€)
    if panier_total < MONTANT_MINIMUM_COUPON:
        raise ValueError(
            f"Coupon '{coupon.code}' - Montant minimum requis : {MONTANT_MINIMUM_COUPON}€, "
            f"panier actuel : {panier_total}€"
        )
    
    # Règle 4 : Coupon gratuit (réduction=100) nécessite panier >= 50€
    if coupon.reduction == 100 and panier_total < MONTANT_MINIMUM_GRATUIT:
        raise ValueError(
            f"Coupon '{coupon.code}' 100% gratuit - montant minimum requis : {MONTANT_MINIMUM_GRATUIT}€, "
            f"panier actuel : {panier_total}€"
        )
    
    return True