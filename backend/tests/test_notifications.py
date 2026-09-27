"""Notifications are owner-scoped (recipient_id == current user), a
deliberately different access rule from country-based scoped_query() -
see core/notifications.py. Assignees must be same-country as the case
(see test_assignee_country_validation.py), so these tests use Admin as
the actor when a distinct creator/assignee pair is needed - Admin-created
cases default to Arnova, and lead-arn is Arnova's only assignable staff.
"""
from tests.conftest import auth_headers


def test_assigning_a_case_on_create_notifies_the_assignee(client):
    client.post(
        "/cases",
        json={"title": "Shelter case", "assigned_to": "lead-arn"},
        headers=auth_headers("admin-1"),
    )

    response = client.get("/notifications", headers=auth_headers("lead-arn"))

    assert response.status_code == 200
    messages = [n["message"] for n in response.json()]
    assert any("Shelter case" in m for m in messages)


def test_assigning_a_case_on_update_notifies_the_assignee(client):
    case_id = client.post(
        "/cases", json={"title": "Medical case"}, headers=auth_headers("lead-arn")
    ).json()["id"]

    client.patch(
        f"/cases/{case_id}",
        json={"assigned_to": "lead-arn"},
        headers=auth_headers("lead-arn"),
    )

    response = client.get("/notifications", headers=auth_headers("lead-arn"))
    assert any("Medical case" in n["message"] for n in response.json())


def test_unassigned_case_notifies_the_countrys_country_lead(client):
    client.post("/cases", json={"title": "Unassigned case"}, headers=auth_headers("lead-arn"))

    response = client.get("/notifications", headers=auth_headers("lead-arn"))

    assert any("needs attention" in n["message"] for n in response.json())


def test_a_user_only_sees_their_own_notifications(client):
    client.post(
        "/cases",
        json={"title": "Private to Amara", "assigned_to": "lead-arn"},
        headers=auth_headers("admin-1"),
    )

    response = client.get("/notifications", headers=auth_headers("field-cal"))

    assert response.json() == []


def test_marking_a_notification_read(client):
    client.post(
        "/cases",
        json={"title": "Case for Amara", "assigned_to": "lead-arn"},
        headers=auth_headers("admin-1"),
    )
    notification_id = client.get("/notifications", headers=auth_headers("lead-arn")).json()[0]["id"]

    response = client.post(f"/notifications/{notification_id}/read", headers=auth_headers("lead-arn"))
    assert response.json()["is_read"] is True

    # Can't mark someone else's notification as read.
    other_attempt = client.post(f"/notifications/{notification_id}/read", headers=auth_headers("lead-bel"))
    assert other_attempt.status_code == 404
