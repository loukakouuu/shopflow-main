# app/security_demo.py
"""
Démonstration de sécurité pour Bandit.
Ce fichier contient des failles intentionnelles pour tester l'analyse statique.
"""

import os

# Faille: Mot de passe hardcodé détecté par Bandit (commenté)
# REDIS_PASSWORD = 'admin123'

# Correction: Utilisation de variables d'environnement
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')


def call_external_api():
    import requests
    
    # Correction: Toujours paramétrer verify=True, ajouter un timeout
    response = requests.get(
        'https://api.example.com',
        verify=True,
        timeout=5.0
    )
    return response


class InsecureDatabase:
    def load_config(self, data):
        """Faille: Désérialisation non sécurisée avec pickle."""
        import pickle
        config = pickle.loads(data)
        return config


def secure_database_load(data):
    """Correction: Utilisation de JSON."""
    import json
    config = json.loads(data)
    return config
