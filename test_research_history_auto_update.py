import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_research_history_auto_updates_on_stock_analysis():
    # 1. Register and login test user
    client.post("/register", json={"email": "history_test@example.com", "password": "Password123!"})
    login_res = client.post("/login", json={"email": "history_test@example.com", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Clear initial history for clean state
    client.delete("/research-history", headers=headers)
    initial_res = client.get("/research-history", headers=headers)
    assert len(initial_res.json()) == 0

    # 3. Analyze stock (INFY)
    stock_res = client.get("/stocks/INFY?period=3mo", headers=headers)
    assert stock_res.status_code == 200

    # 4. Verify research history automatically updated
    history_res = client.get("/research-history", headers=headers)
    assert history_res.status_code == 200
    items = history_res.json()
    assert len(items) >= 1
    assert items[0]["stock_symbol"] == "INFY"
    entry_id = items[0]["id"]

    # 5. Analyze another stock (TCS.NS)
    client.get("/stocks/TCS.NS?period=1mo", headers=headers)
    updated_hist = client.get("/research-history", headers=headers).json()
    symbols = [item["stock_symbol"] for item in updated_hist]
    assert "TCS.NS" in symbols
    assert "INFY" in symbols

    # 6. Delete specific history entry
    del_res = client.delete(f"/research-history/{entry_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify INFY entry removed
    after_del = client.get("/research-history", headers=headers).json()
    remaining_ids = [item["id"] for item in after_del]
    assert entry_id not in remaining_ids
