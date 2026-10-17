from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200


def test_generate_from_parameters():
    response = client.post(
        "/generate/params",
        json={
            "grid_size": 7,
            "symmetry": "mirror",
            "turn_density": 0.5,
            "seed": 12345
        }
    )

    assert response.status_code == 200

    body = response.json()

    assert body["params"]["grid_size"] == 7
    assert body["kolam"]["closed"] is True
    assert body["kolam"]["validated"] is False


def test_invalid_grid_size_is_rejected():
    response = client.post(
        "/generate/params",
        json={
            "grid_size": 100,
            "symmetry": "mirror",
            "turn_density": 0.5,
            "seed": 12345
        }
    )

    assert response.status_code == 422