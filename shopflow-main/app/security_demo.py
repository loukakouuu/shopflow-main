# app/security_demo.py
"""
Démonstration de vulnérabilités de sécurité pour Bandit.
Ce fichier introduit volontairement des failles pour tester Bandit.
À ne JAMAIS utiliser en production!
"""

import os

# VULNÉRABILITÉ 1 - B105 : Hardcoded password (AVANT CORRECTION)
# REDIS_PASSWORD = 'admin123'  # INSECURE - Jamais coder des mots de passe!

# CORRECTION VULNÉRABILITÉ 1 - Utiliser des variables d'environnement
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')  # ✅ SÉCURISÉ


def call_external_api():
    """
    VULNÉRABILITÉ 2 - B501 : SSL verification disabled (AVANT CORRECTION)
    Ceci a été corrigé pour toujours vérifier les certificats SSL.
    """
    import requests
    
    # CORRECTION VULNÉRABILITÉ 2 - Toujours verify=True
    # Même si insecure=True, on DOIT vérifier les certificats SSL
    response = requests.get(
        'https://api.example.com',
        verify=True,  # ✅ SÉCURISÉ - Vérifier toujours les certificats
        timeout=5.0   # ✅ Bonus: ajouter un timeout pour éviter B113
    )
    return response


class InsecureDatabase:
    """
    VULNÉRABILITÉ 3 - B301 : Pickle usage (RCE risk)
    Cette classe est conservée à titre informatif.
    """
    def load_config(self, data):
        """NE PAS utiliser pickle pour désérialiser des données non fiables."""
        import pickle
        # INSECURE
        config = pickle.loads(data)  # Peut exécuter du code arbitraire!
        return config


def secure_database_load(data):
    """
    ✅ SÉCURISÉ - Utiliser JSON à la place de pickle.
    JSON est beaucoup plus sûr car il ne peut pas exécuter du code.
    """
    import json
    config = json.loads(data)
    return config

