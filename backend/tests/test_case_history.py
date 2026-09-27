"""GET /cases/{id}/history: any role that can see the case can see its
own history (unlike the platform-wide /audit-logs, which is Admin/Auditor
only) - deliberately different, owner-of-the-record visibility.
"""
from tests.conftest import auth_headers


def test_history_lists_this_cases_audit_rows_only(client):
    case_id = client.post(
        "/cases", json={"title": "Shelter case"}, headers=auth_headers("lead-arn")
    ).json()["id"]
    other_id = client.post(
        "/cases", json={"title": "Other case"}, headers=auth_headers("lead-arn")
    ).json()["id"]
    client.post(f"/cases/{case_id}/close", headers=auth_headers("lead-arn"))

    response = client.get(f"/cases/{case_id}/history", headers=auth_headers("lead-arn"))

    assert response.status_code == 200
    actions = [row["action"] for row in response.json()]
    assert actions == ["close", "create"]
    assert all(row["entity_id"] == case_id for row in response.json())
    assert other_id not in [row["entity_id"] for row in response.json()]


def test_field_worker_can_read_history_of_a_case_they_can_see(client):
    """Field workers are barred from /audit-logs entirely, but they can
    still see the history of a case in their own country - a case's
    history is part of viewing the case, not a separate audit permission."""
    case_id = client.post(
        "/cases", json={"title": "Field case"}, headers=auth_headers("field-cal")
    ).json()["id"]

    response = client.get(f"/cases/{case_id}/history", headers=auth_headers("field-cal"))

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_history_404s_for_a_case_outside_the_users_country(client):
    case_id = client.post(
        "/cases", json={"title": "Belmara case"}, headers=auth_headers("lead-bel")
    ).json()["id"]

    response = client.get(f"/cases/{case_id}/history", headers=auth_headers("lead-arn"))

    assert response.status_code == 404
