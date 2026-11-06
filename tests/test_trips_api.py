from uuid import uuid4

from tests.conftest import register_and_login, trip_payload


async def test_create_trip_requires_authentication(client):
    response = await client.post("/api/v1/trips/", json=trip_payload())

    assert response.status_code == 401


async def test_create_and_read_trip(client, trip):
    response = await client.get(f"/api/v1/trips/{trip['id']}")

    assert response.status_code == 200
    assert response.json()["destination"] == "Paris, France"


async def test_create_trip_rejects_end_before_start(client, auth_headers):
    payload = trip_payload(end_datetime="2030-05-01T09:00:00Z")

    response = await client.post("/api/v1/trips/", json=payload, headers=auth_headers)

    assert response.status_code == 422


async def test_create_trip_rejects_a_past_start(client, auth_headers):
    payload = trip_payload(
        start_datetime="2020-05-10T09:00:00Z", end_datetime="2020-05-12T09:00:00Z"
    )

    response = await client.post("/api/v1/trips/", json=payload, headers=auth_headers)

    assert response.status_code == 422


async def test_list_trips(client, trip):
    response = await client.get("/api/v1/trips/")

    assert [item["id"] for item in response.json()] == [trip["id"]]


async def test_unknown_trip_is_404(client):
    assert (await client.get(f"/api/v1/trips/{uuid4()}")).status_code == 404


async def test_creator_can_update_trip(client, trip, auth_headers):
    response = await client.put(
        f"/api/v1/trips/{trip['id']}",
        json=trip_payload(title="Paris in May"),
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Paris in May"


async def test_other_users_cannot_update_trip(client, trip):
    intruder = await register_and_login(client, "mallory")

    response = await client.put(
        f"/api/v1/trips/{trip['id']}", json=trip_payload(title="Hijacked"), headers=intruder
    )

    assert response.status_code == 403


async def test_delete_trip(client, trip):
    assert (await client.delete(f"/api/v1/trips/{trip['id']}")).status_code == 204
    assert (await client.get(f"/api/v1/trips/{trip['id']}")).status_code == 404
