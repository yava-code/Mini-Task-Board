# Mini-Task-Board

Built in a pair. A small Trello-style board for practicing pair work and frontend (columns, cards, Flask + MongoDB, login/signup).

Run **MongoDB** locally (default `mongodb://127.0.0.1:27017`) or set `MONGO_URI`. Set `SECRET_KEY` in production.

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 — landing page, then register/login and the board at `/board`.

**API:** human-readable list at `/docs`, OpenAPI spec at `/openapi.json`, interactive **Swagger UI** at `/swagger` (log in in another tab first so requests include your session cookie).

Or `docker compose up` to run MongoDB and the app together.

Tests use **mongomock** (no Mongo daemon needed):

```bash
pytest -q
```
