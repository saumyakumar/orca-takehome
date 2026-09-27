"""Country/assigned_to/status filters on GET /cases compose on top of RBAC
scoping, never before it - same principle as search/pagination.
"""
from tests.conftest import auth_headers


def _create(client, title, user="lead-arn", assigned_to=None):
    payload = {"title": title}
    if assigned_to is not None:
        payload["assigned_to"] = assigned_to
    return client.post("/cases", json=payload, headers=auth_headers(user))


def test_status_filter(client):
    open_id = _create(client, "Open case").json()["id"]
    closed_id = _create(client, "Case to close").json()["id"]
    client.post(f"/cases/{closed_id}/close", headers=auth_headers("lead-arn"))

    response = client.get("/cases", params={"status": "open"}, headers=auth_headers("lead-arn"))

    ids = [c["id"] for c in response.json()["items"]]
    assert open_id in ids
    assert closed_id not in ids


def test_assigned_to_filter_matches_specific_user(client):
    _create(client, "Assigned to Amara", assigned_to="lead-arn")
    _create(client, "Unassigned case")

    response = client.get(
        "/cases", params={"assigned_to": "lead-arn"}, headers=auth_headers("lead-arn")
    )

    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Assigned to Amara"


def test_assigned_to_unassigned_sentinel_matches_null(client):
    _create(client, "Assigned to Boris", assigned_to="lead-bel")
    _create(client, "Unassigned case")

    response = client.get(
        "/cases", params={"assigned_to": "unassigned"}, headers=auth_headers("lead-arn")
    )

    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Unassigned case"


def test_country_filter_outside_own_scope_returns_empty_not_a_bypass(client):
    _create(client, "Arnova case", user="lead-arn")

    response = client.get(
        "/cases", params={"country": "Belmara"}, headers=auth_headers("lead-arn")
    )

    assert response.json()["items"] == []
    assert response.json()["total"] == 0


def test_admin_can_filter_by_any_country(client):
    _create(client, "Arnova case", user="lead-arn")
    _create(client, "Belmara case", user="lead-bel")

    response = client.get(
        "/cases", params={"country": "Belmara"}, headers=auth_headers("admin-1")
    )

    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["country"] == "Belmara"


def test_filters_combine(client):
    _create(client, "Match", assigned_to="lead-arn")
    close_id = _create(client, "Wrong status", assigned_to="lead-arn").json()["id"]
    client.post(f"/cases/{close_id}/close", headers=auth_headers("lead-arn"))
    _create(client, "Wrong assignee")

    response = client.get(
        "/cases",
        params={"status": "open", "assigned_to": "lead-arn"},
        headers=auth_headers("lead-arn"),
    )

    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Match"
