from app.core.audit import AuditLog

from tests.conftest import auth_headers


def test_create_case_writes_one_audit_row(client, db_session):
    response = client.post(
        "/cases",
        json={"title": "New case"},
        headers=auth_headers("lead-arn"),
    )
    assert response.status_code == 200

    logs = db_session.query(AuditLog).filter_by(action="create").all()
    assert len(logs) == 1
    assert logs[0].actor_id == "lead-arn"
    assert logs[0].entity_type == "Case"
    assert logs[0].entity_id == response.json()["id"]


def test_close_case_writes_close_audit_row(client, db_session):
    create_resp = client.post("/cases", json={"title": "Case to close"}, headers=auth_headers("lead-arn"))
    case_id = create_resp.json()["id"]

    close_resp = client.post(f"/cases/{case_id}/close", headers=auth_headers("lead-arn"))
    assert close_resp.status_code == 200

    logs = db_session.query(AuditLog).filter_by(action="close", entity_id=case_id).all()
    assert len(logs) == 1
    assert logs[0].actor_id == "lead-arn"


def test_list_cases_is_itself_audited(client, db_session):
    client.get("/cases", headers=auth_headers("lead-arn"))

    logs = db_session.query(AuditLog).filter_by(action="list_cases").all()
    assert len(logs) == 1
    assert logs[0].actor_id == "lead-arn"


def test_auditor_can_read_audit_logs_scoped_to_own_country(client):
    client.post("/cases", json={"title": "Arnova case"}, headers=auth_headers("lead-arn"))
    client.post("/cases", json={"title": "Belmara case"}, headers=auth_headers("lead-bel"))

    response = client.get("/audit-logs", headers=auth_headers("audit-arn"))

    assert response.status_code == 200
    countries = {row["country"] for row in response.json() if row["country"]}
    assert countries <= {"Arnova"}


def test_field_worker_cannot_read_audit_logs(client):
    response = client.get("/audit-logs", headers=auth_headers("field-cal"))
    assert response.status_code == 403
