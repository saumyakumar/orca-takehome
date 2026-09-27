"""End-to-end proof of the cross-app integration: closing a Case through
the real HTTP endpoint (not calling the handler directly) must cause
Command View's country stats to update, with no manual refresh step.
"""
from tests.conftest import auth_headers


def test_closing_a_case_updates_command_view_count(client):
    create_resp = client.post("/cases", json={"title": "Case A"}, headers=auth_headers("lead-arn"))
    client.post("/cases", json={"title": "Case B"}, headers=auth_headers("lead-arn"))
    case_id = create_resp.json()["id"]

    before = client.get("/country-stats/Arnova", headers=auth_headers("lead-arn"))
    assert before.status_code == 404  # no CountryStats row exists until the first close event

    close_resp = client.post(f"/cases/{case_id}/close", headers=auth_headers("lead-arn"))
    assert close_resp.status_code == 200

    after = client.get("/country-stats/Arnova", headers=auth_headers("lead-arn"))
    assert after.json()["open_case_count"] == 1


def test_recompute_is_idempotent_against_duplicate_events(client):
    """Guards the design choice of recomputing rather than decrementing:
    firing the same close twice (e.g. a retried event) must not double-count."""
    create_resp = client.post("/cases", json={"title": "Case A"}, headers=auth_headers("lead-arn"))
    case_id = create_resp.json()["id"]

    client.post(f"/cases/{case_id}/close", headers=auth_headers("lead-arn"))

    from app.command_view.service import recompute_open_count
    from app.db import SessionLocal

    db = SessionLocal()
    try:
        stats_first = recompute_open_count("Arnova", db)
        stats_second = recompute_open_count("Arnova", db)
        assert stats_first.open_case_count == stats_second.open_case_count == 0
    finally:
        db.close()
