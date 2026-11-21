import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.app.db.session import Base, get_db

# Create an in-memory SQLite database specifically for test isolation
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in the isolated in-memory test database
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override FastAPI get_db dependency
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_user_registration_and_validation():
    # 1. Successful registration
    reg_payload = {
        "email": "test_investor@example.com",
        "password": "Password123!",
        "preferences": {"preferred_market": "NSE", "analysis_period": "1Y"}
    }
    response = client.post("/register", json=reg_payload)
    assert response.status_code == 201
    data = response.json()
    assert "user_id" in data
    assert data["email"] == "test_investor@example.com"
    assert data["message"] == "Registration successful!"

    # 2. Duplicate registration attempt should return 400
    dup_res = client.post("/register", json=reg_payload)
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 3. Invalid email format should return 422
    invalid_email_res = client.post("/register", json={"email": "not-an-email", "password": "Password123!"})
    assert invalid_email_res.status_code == 422

    # 4. Short password (< 6 chars) should return 422
    short_pw_res = client.post("/register", json={"email": "valid@example.com", "password": "123"})
    assert short_pw_res.status_code == 422

def test_login_and_jwt_authentication():
    # 1. Invalid credentials
    bad_login = client.post("/login", json={"email": "test_investor@example.com", "password": "WrongPassword"})
    assert bad_login.status_code == 401
    assert "Invalid email or password" in bad_login.json()["detail"]

    # 2. Valid credentials
    good_login = client.post("/login", json={"email": "test_investor@example.com", "password": "Password123!"})
    assert good_login.status_code == 200
    token_data = good_login.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # 3. Access protected /me route
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/me", headers=headers)
    assert me_res.status_code == 200
    user_info = me_res.json()
    assert user_info["email"] == "test_investor@example.com"

    # 4. Access protected route without token should fail with 401
    unauth_res = client.get("/me")
    assert unauth_res.status_code == 401

def test_user_preferences():
    # Log in
    login_res = client.post("/login", json={"email": "test_investor@example.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Read default preferences
    get_res = client.get("/preferences", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["market"] == "NSE"

    # 2. Update preferences
    update_res = client.put("/preferences", json={"market": "BSE", "period": "6 months"}, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["market"] == "BSE"
    assert update_res.json()["period"] == "6 months"

    # 3. Confirm persistence
    verify_res = client.get("/preferences", headers=headers)
    assert verify_res.json()["market"] == "BSE"
    assert verify_res.json()["period"] == "6 months"

def test_watchlist_operations():
    # Log in
    login_res = client.post("/login", json={"email": "test_investor@example.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Add stock to watchlist
    add_res = client.post("/watchlist", json={"symbol": "RELIANCE.NS", "company_name": "Reliance Industries"}, headers=headers)
    assert add_res.status_code == 201
    item = add_res.json()
    assert item["symbol"] == "RELIANCE.NS"
    item_id = item["id"]

    # 2. View watchlist
    list_res = client.get("/watchlist", headers=headers)
    assert list_res.status_code == 200
    symbols = [s["symbol"] for s in list_res.json()]
    assert "RELIANCE.NS" in symbols

    # 3. Duplicate addition should return 400
    dup_res = client.post("/watchlist", json={"symbol": "RELIANCE.NS"}, headers=headers)
    assert dup_res.status_code == 400

    # 4. Remove stock from watchlist
    del_res = client.delete(f"/watchlist/{item_id}", headers=headers)
    assert del_res.status_code == 200

    # Confirm removed
    after_del = client.get("/watchlist", headers=headers)
    symbols_after = [s["symbol"] for s in after_del.json()]
    assert "RELIANCE.NS" not in symbols_after

def test_research_history():
    # Log in
    login_res = client.post("/login", json={"email": "test_investor@example.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Record a research task
    rec_res = client.post(
        "/research-history",
        json={
            "stock_symbol": "TATAMOTORS.NS",
            "company_name": "Tata Motors Ltd",
            "analysis_period": "1Y",
            "research_summary": {"sentiment": "Bullish", "target_price": 1050}
        },
        headers=headers
    )
    assert rec_res.status_code == 201
    assert rec_res.json()["stock_symbol"] == "TATAMOTORS.NS"

    # 2. Retrieve research history
    hist_res = client.get("/research-history", headers=headers)
    assert hist_res.status_code == 200
    items = hist_res.json()
    assert len(items) >= 1
    assert items[0]["stock_symbol"] == "TATAMOTORS.NS"
    assert items[0]["company_name"] == "Tata Motors Ltd"

def test_workspace_isolation_between_users():
    # Register User Alpha
    client.post("/register", json={"email": "alpha@example.com", "password": "AlphaPassword123!"})
    alpha_token = client.post("/login", json={"email": "alpha@example.com", "password": "AlphaPassword123!"}).json()["access_token"]
    alpha_hdr = {"Authorization": f"Bearer {alpha_token}"}

    # Register User Beta
    client.post("/register", json={"email": "beta@example.com", "password": "BetaPassword123!"})
    beta_token = client.post("/login", json={"email": "beta@example.com", "password": "BetaPassword123!"}).json()["access_token"]
    beta_hdr = {"Authorization": f"Bearer {beta_token}"}

    # Alpha adds HDFC and researches HDFC
    client.post("/watchlist", json={"symbol": "HDFCBANK.NS", "company_name": "HDFC Bank"}, headers=alpha_hdr)
    client.post("/research-history", json={"stock_symbol": "HDFCBANK.NS", "company_name": "HDFC Bank"}, headers=alpha_hdr)

    # Beta adds INFY and researches INFY
    client.post("/watchlist", json={"symbol": "INFY.NS", "company_name": "Infosys"}, headers=beta_hdr)
    client.post("/research-history", json={"stock_symbol": "INFY.NS", "company_name": "Infosys"}, headers=beta_hdr)

    # Verify Alpha cannot see Beta's data
    alpha_wl = [s["symbol"] for s in client.get("/watchlist", headers=alpha_hdr).json()]
    alpha_rh = [s["stock_symbol"] for s in client.get("/research-history", headers=alpha_hdr).json()]
    assert "HDFCBANK.NS" in alpha_wl
    assert "INFY.NS" not in alpha_wl
    assert "HDFCBANK.NS" in alpha_rh
    assert "INFY.NS" not in alpha_rh

    # Verify Beta cannot see Alpha's data
    beta_wl = [s["symbol"] for s in client.get("/watchlist", headers=beta_hdr).json()]
    beta_rh = [s["stock_symbol"] for s in client.get("/research-history", headers=beta_hdr).json()]
    assert "INFY.NS" in beta_wl
    assert "HDFCBANK.NS" not in beta_wl
    assert "INFY.NS" in beta_rh
    assert "HDFCBANK.NS" not in beta_rh
