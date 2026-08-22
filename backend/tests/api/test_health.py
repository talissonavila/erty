from app.schemas.health_schema import HealthResponse
from app.core.settings import settings


def test_health_endpoint_returns_service_status(client):
    expected_data = HealthResponse(
        status="healthy",
        service="erty-backend",
        version=settings.app_version
    )

    response = client.get("/health")

    assert response.status_code == 200
    items = response.json()
    assert expected_data.model_dump() == items


