import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from faker import Faker
from app.database import Base, get_db
from app.models import Product, Cart, CartItem, Order, Coupon
from app.main import app

fake = Faker('fr_FR')


@pytest.fixture(autouse=True)
def mock_cache(mocker):
    """Mock cache functions to avoid testing cache logic in integration tests."""
    mocker.patch("app.routes.products.get_cached", return_value=None)
    mocker.patch("app.routes.products.set_cached")
    mocker.patch("app.routes.products.delete_cached")



# FIXTURES BASE DE DONNÉES
@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

# FIXTURES DE DONNÉES
@pytest.fixture
def product_sample(db_session):
    p = Product(
        name="Laptop Pro",
        price=999.99,
        stock=10
    )
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p

@pytest.fixture
def coupon_sample(db_session):
    import uuid
    c = Coupon(
        code=f"PROMO20_{uuid.uuid4().hex[:8]}",
        reduction=20.0,
        actif=True
    )
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


# ───── FIXTURES TESTCLIENT & INTÉGRATION ─────

@pytest.fixture(scope="module")
def client(db_engine):
    """TestClient FastAPI avec BDD SQLite isolée par module de test."""
    SessionTest = sessionmaker(bind=db_engine)
    
    def override_get_db():
        session = SessionTest()
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def api_product(client):
    """Crée un produit via POST /products/ et le retourne."""
    response = client.post('/products/', json={
        'name': 'Clavier Mécanique',
        'price': 89.99,
        'stock': 25,
        'category': 'peripheriques',
    })
    assert response.status_code == 201
    yield response.json()


@pytest.fixture
def api_coupon(client):
    """Crée un coupon TEST10 (-10%) via POST /coupons/."""
    response = client.post('/coupons/', json={
        'code': 'TEST10', 'reduction': 10.0, 'actif': True
    })
    assert response.status_code == 201
    yield response.json()


# ───── FIXTURES FAKER ─────

@pytest.fixture
def fake_product_data():
    """Génère un payload produit réaliste et aléatoire."""
    return {
        'name': fake.catch_phrase()[:50],
        'price': round(fake.pyfloat(min_value=1, max_value=2000, right_digits=2), 2),
        'stock': fake.random_int(min=0, max=500),
        'category': fake.random_element(['informatique', 'peripheriques', 'audio', 'gaming']),
    }


@pytest.fixture
def multiple_products(client):
    """Crée 5 produits avec faker pour tester la liste et les filtres."""
    faker_inst = Faker()
    products = []
    for i in range(5):
        r = client.post('/products/', json={
            'name': faker_inst.word().capitalize() + f' {i}',
            'price': round(10.0 + i * 20, 2),
            'stock': 10,
        })
        if r.status_code == 201:
            products.append(r.json())
    yield products