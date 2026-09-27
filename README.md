# ORCA Platform Foundation — Part A

A minimal shared platform foundation for the ORCA emergency-relief platform, demonstrated with
two entities from two different apps: **Case** (Care Companion) and **CountryStats**, an
aggregate open-case count per country (Command View).

For the design reasoning behind these choices, see [ASSIGNMENT_ANSWERS.md](ASSIGNMENT_ANSWERS.md).
For the architecture (file-by-file breakdown, request traces, how to navigate the codebase), see
[HLD.md](HLD.md) and [KNOWLEDGE_GRAPH.md](KNOWLEDGE_GRAPH.md).

## How to run it

**Backend** (Python 3.9+, tested on 3.9.6):
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python seed.py          # populates demo cases across 3 countries + country stats
uvicorn app.main:app --reload --port 8000
```
API docs (auto-generated OpenAPI contract): http://127.0.0.1:8000/docs

**Frontend**:
```bash
cd frontend
npm install
npm run dev             # http://localhost:5173, proxies /api -> localhost:8000
```

**Tests**:
```bash
cd backend && source venv/bin/activate
pytest -v
```

There's no real login — the frontend has a "Viewing as" dropdown that switches which seeded demo
user's id is sent as an `X-User-Id` header. This is a deliberate simplification, not an oversight —
a real auth system would only change `auth/fake_users.py`; RBAC and audit only ever depend on a
user's `.id`/`.role`/`.country`.
