"""A case can only be assigned to staff in its own country - enforced
server-side, not just left to the frontend to not offer a bad option.
"""
from tests.conftest import auth_headers


def test_create_rejects_cross_country_assignee(client):
    response = client.post(
        "/cases",
        json={"title": "Arnova case", "assigned_to": "lead-bel"},
        headers=auth_headers("lead-arn"),
    )
    assert response.status_code == 400


def test_create_accepts_same_country_assignee(client):
    response = client.post(
        "/cases",
        json={"title": "Arnova case", "assigned_to": "lead-arn"},
        headers=auth_headers("lead-arn"),
    )
    assert response.status_code == 200
    assert response.json()["assigned_to"] == "lead-arn"


def test_update_rejects_cross_country_assignee(client):
    case_id = client.post(
        "/cases", json={"title": "Arnova case"}, headers=auth_headers("lead-arn")
    ).json()["id"]

    response = client.patch(
        f"/cases/{case_id}", json={"assigned_to": "field-cal"}, headers=auth_headers("lead-arn")
    )

    assert response.status_code == 400


def test_update_accepts_same_country_assignee(client):
    case_id = client.post(
        "/cases", json={"title": "Arnova case"}, headers=auth_headers("lead-arn")
    ).json()["id"]

    response = client.patch(
        f"/cases/{case_id}", json={"assigned_to": "lead-arn"}, headers=auth_headers("lead-arn")
    )

    assert response.status_code == 200
    assert response.json()["assigned_to"] == "lead-arn"


def test_unassigning_is_always_allowed(client):
    case_id = client.post(
        "/cases",
        json={"title": "Arnova case", "assigned_to": "lead-arn"},
        headers=auth_headers("lead-arn"),
    ).json()["id"]

    response = client.patch(
        f"/cases/{case_id}", json={"assigned_to": None}, headers=auth_headers("lead-arn")
    )

    assert response.status_code == 200
    assert response.json()["assigned_to"] is None
