"""Pagination/search on GET /cases must compose on top of RBAC scoping,
never before it - a search or page slice can never surface a row that
scoped_query() would have hidden.
"""
from tests.conftest import auth_headers


def _create(client, title, user="lead-arn"):
    return client.post("/cases", json={"title": title}, headers=auth_headers(user))


def test_pagination_limits_page_size_and_reports_total(client):
    for i in range(7):
        _create(client, f"Case {i}")

    page1 = client.get("/cases", params={"limit": 5, "offset": 0}, headers=auth_headers("lead-arn"))
    page2 = client.get("/cases", params={"limit": 5, "offset": 5}, headers=auth_headers("lead-arn"))

    assert page1.json()["total"] == 7
    assert len(page1.json()["items"]) == 5
    assert len(page2.json()["items"]) == 2


def test_search_filters_by_title(client):
    _create(client, "Shelter request - Family A")
    _create(client, "Medical supply case")

    response = client.get("/cases", params={"search": "shelter"}, headers=auth_headers("lead-arn"))

    assert response.json()["total"] == 1
    assert "Shelter" in response.json()["items"][0]["title"]


def test_search_and_pagination_stay_scoped_to_country(client):
    _create(client, "Arnova shelter case", user="lead-arn")
    _create(client, "Belmara shelter case", user="lead-bel")

    response = client.get("/cases", params={"search": "shelter"}, headers=auth_headers("lead-arn"))

    assert response.json()["total"] == 1
    assert response.json()["items"][0]["country"] == "Arnova"
