# tests/perf/locustfile.py
"""Performance tests avec Locust - Simulation charge utilisateurs ShopFlow."""

from locust import HttpUser, task, between
import random

PRODUCT_IDS = list(range(1, 21))  # IDs des 20 produits créés


class ShopFlowUser(HttpUser):
    """Utilisateur virtuel SimShopFlow - Simulate load on e-commerce API."""
    
    wait_time = between(0.5, 2.0)  # Wait 0.5-2s entre chaque l'action
    
    def on_start(self):
        """Initialisation au démarrage du user - Générer ID utilisateur unique."""
        self.user_id = random.randint(10000, 99999)
    
    @task(5)
    def browse_products(self):
        """Scénario le plus fréquent : lister les produits (5x plus que autres)."""
        self.client.get('/api/products/', name='/api/products/ [list]')
    
    @task(3)
    def get_product_detail(self):
        """Consulter un produit au hasard (3x)."""
        pid = random.choice(PRODUCT_IDS)
        self.client.get(f'/api/products/{pid}', name='/api/products/[id] [detail]')
    
    @task(2)
    def add_to_cart(self):
        """Ajouter un produit au panier (2x)."""
        product_id = random.choice(PRODUCT_IDS)
        payload = {
            "product_id": product_id,
            "quantity": random.randint(1, 3)
        }
        self.client.post(
            f'/api/cart/{self.user_id}',
            json=payload,
            name='/api/cart/[add]'
        )
    
    @task(1)
    def place_order(self):
        """Passer une commande : (1) ajouter produit -> (2) créer commande."""
        # Étape 1 : Ajouter un produit au panier
        product_id = random.choice(PRODUCT_IDS)
        payload = {
            "product_id": product_id,
            "quantity": 1
        }
        self.client.post(
            f'/api/cart/{self.user_id}',
            json=payload,
            name='/api/cart/[add]'
        )
        
        # Étape 2 : Créer la commande
        order_payload = {
            "shipping_address": f"Address {random.randint(1, 1000)}"
        }
        response = self.client.post(
            f'/api/orders/{self.user_id}',
            json=order_payload,
            name='/api/orders/[create]'
        )
        
        # Gérer le cas 400 (panier vide) comme succès acceptable
        if response.status_code == 400:
            pass  # Acceptable - panier vide
    
    @task(1)
    def health_check(self):
        """Vérifier la santé de l'API - smoke test."""
        self.client.get('/health', name='/health [smoke]')
