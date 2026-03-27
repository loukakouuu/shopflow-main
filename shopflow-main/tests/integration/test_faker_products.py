import pytest


@pytest.mark.integration
class TestProductsAvecFaker:
    def test_creation_donnees_faker(self, client, fake_product_data):
        """Crée un produit avec des données faker et vérifie la réponse."""
        response = client.post('/products/', json=fake_product_data)
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == fake_product_data['name']
        assert data['price'] == fake_product_data['price']

    def test_liste_avec_multiple_produits(self, client, multiple_products):
        """Vérifie que les 5 produits créés apparaissent dans la liste."""
        if not multiple_products:
            pytest.skip("Les produits n'ont pas pu être créés")
        
        response = client.get('/products/')
        assert response.status_code == 200
        ids_liste = [p['id'] for p in response.json()]
        for p in multiple_products:
            assert p['id'] in ids_liste

    @pytest.mark.parametrize('prix,attendu_422', [
        (0.0, True),       # prix = 0 → invalide (gt=0)
        (-1.0, True),      # prix négatif → invalide
        (0.01, False),     # prix minimal valide
        (9999.99, False),  # prix élevé mais valide
    ])
    def test_validation_prix(self, client, prix, attendu_422):
        response = client.post('/products/', json={
            'name': 'Test',
            'price': prix,
            'stock': 1
        })
        if attendu_422:
            assert response.status_code == 422
        else:
            assert response.status_code == 201

    def test_noms_longs(self, client):
        """Un nom de 101 chars dépasse max_length=100 → 422."""
        # 1) créer un produit avec un nom de 101 caractères → doit retourner 422
        response_long = client.post('/products/', json={
            'name': 'A' * 101,
            'price': 10.0,
            'stock': 1
        })
        assert response_long.status_code == 422

        # 2) créer un produit avec un nom de 100 caractères → doit réussir (201)
        response_ok = client.post('/products/', json={
            'name': 'A' * 100,
            'price': 10.0,
            'stock': 1
        })
        assert response_ok.status_code == 201
