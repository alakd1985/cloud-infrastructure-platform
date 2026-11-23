import pytest
from fastapi.testclient import TestClient

from app.src import main
from app.src.main import app

client = TestClient(app)



@pytest.fixture(autouse=True)
def reset_items():

    main.items.clear()
    main.next_item_id = 1

def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["application"] == "Cloud Infrastructure Platform"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_unknown_endpoint():
    response = client.get("/unknown")

    assert response.status_code == 404


def test_create_item():
    item_data = {
        "name": "AWS Infrastructure",
        "description": "Cloud infrastructure project"
    }

    response = client.post("/items", json=item_data)

    assert response.status_code == 201
    assert response.json()["name"] == "AWS Infrastructure"
    assert response.json()["description"] == "Cloud infrastructure project"
    assert response.json()["id"] == 1


def test_get_all_items():
    item_data = {
        "name": "Kubernetes Platform",
        "description": "Container orchestration platform"
    }

    client.post("/items", json=item_data)

    response = client.get("/items")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Kubernetes Platform"
    assert response.json()[0]["description"] == "Container orchestration platform"

def test_get_item_by_id():
    item_data = {
        "name": "AWS EKS",
        "description": "Managed Kubernetes service"
    }

    create_response = client.post("/items", json=item_data)

    item_id = create_response.json()["id"]

    response = client.get(f"/items/{item_id}")

    assert response.status_code == 200
    assert response.json()["id"] == item_id
    assert response.json()["name"] == "AWS EKS"
    assert response.json()["description"] == "Managed Kubernetes service"

def test_update_item():
    item_data = {
        "name": "AWS Infrastructure",
        "description": "Original description"
    }

    create_response = client.post("/items", json=item_data)
    item_id = create_response.json()["id"]

    updated_data = {
        "name": "AWS EKS Platform",
        "description": "Updated Kubernetes infrastructure"
    }

    response = client.put(f"/items/{item_id}", json=updated_data)

    assert response.status_code == 200
    assert response.json()["id"] == item_id
    assert response.json()["name"] == "AWS EKS Platform"
    assert response.json()["description"] == "Updated Kubernetes infrastructure"

    get_response = client.get(f"/items/{item_id}")

    assert get_response.status_code == 200
    assert get_response.json()["name"] == "AWS EKS Platform"

def test_delete_item():
    item_data = {
        "name": "AWS Infrastructure",
        "description": "Cloud infrastructure project"
    }

    create_response = client.post("/items", json=item_data)
    item_id = create_response.json()["id"]

    response = client.delete(f"/items/{item_id}")

    assert response.status_code == 200
    assert response.json()["message"] == "Item deleted successfully"

    get_response = client.get(f"/items/{item_id}")

    assert get_response.status_code == 404

def test_get_nonexistent_item():
    response = client.get("/items/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"

def test_create_item_with_invalid_data():
    item_data = {
        "name": "AWS Infrastructure"
    }

    response = client.post("/items", json=item_data)

    assert response.status_code == 422

    get_response = client.get("/items")

    assert get_response.status_code == 200
    assert len(get_response.json()) == 0

def test_update_nonexistent_item():
    updated_data = {
        "name": "Updated AWS Infrastructure",
        "description": "Updated description"
    }

    response = client.put("/items/999", json=updated_data)

    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"

def test_delete_nonexistent_item():
    response = client.delete("/items/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"

    list_response = client.get("/items")

    assert list_response.status_code == 200
    assert len(list_response.json()) == 0
    #