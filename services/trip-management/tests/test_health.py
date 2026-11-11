from app import app


def test_health_reports_ok():
    response = app.test_client().get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
    assert response.get_json()["service"] == "trip-management"
