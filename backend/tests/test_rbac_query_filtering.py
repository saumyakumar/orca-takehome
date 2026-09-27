"""Proves RBAC is enforced as a SQL predicate, not a Python-side filter -
the exact distinction the brief calls out, and the anti-pattern Part D's
review target commits.
"""
from app.auth.fake_users import FAKE_USERS
from app.cases.models import Case
from app.core.rbac import scoped_query

from tests.conftest import auth_headers


def _seed_cases(db_session):
    db_session.add_all([
        Case(title="Arnova case 1", country="Arnova", owner_app="care_companion", created_by="lead-arn"),
        Case(title="Arnova case 2", country="Arnova", owner_app="care_companion", created_by="lead-arn"),
        Case(title="Belmara case 1", country="Belmara", owner_app="care_companion", created_by="lead-bel"),
    ])
    db_session.commit()


def test_scoped_query_compiles_country_into_sql_where_clause(db_session):
    _seed_cases(db_session)
    lead = FAKE_USERS["lead-arn"]

    query = scoped_query(db_session, Case, lead)
    compiled_sql = str(query.statement.compile(compile_kwargs={"literal_binds": True}))

    assert "WHERE" in compiled_sql
    assert "country" in compiled_sql
    assert "'Arnova'" in compiled_sql


def test_country_lead_only_sees_own_country_rows(db_session):
    _seed_cases(db_session)
    lead = FAKE_USERS["lead-arn"]

    results = scoped_query(db_session, Case, lead).all()

    assert len(results) == 2
    assert all(c.country == "Arnova" for c in results)


def test_admin_sees_all_countries(db_session):
    _seed_cases(db_session)
    admin = FAKE_USERS["admin-1"]

    results = scoped_query(db_session, Case, admin).all()

    assert len(results) == 3


def test_list_cases_endpoint_enforces_country_scoping(client, db_session):
    _seed_cases(db_session)

    arn_response = client.get("/cases", headers=auth_headers("lead-arn"))
    bel_response = client.get("/cases", headers=auth_headers("lead-bel"))

    assert arn_response.status_code == 200
    assert bel_response.status_code == 200
    assert len(arn_response.json()["items"]) == 2
    assert arn_response.json()["total"] == 2
    assert len(bel_response.json()["items"]) == 1
    assert all(c["country"] == "Arnova" for c in arn_response.json()["items"])
