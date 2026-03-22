# Mini-Task-Board

Built in a pair. A small Trello-style board for practicing pair work and frontend (columns, cards, Flask + SQLite, login/signup).

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 — landing page first, then register/login and the board at `/board`. If you have an old DB and the app crashes on startup, delete `instance/tasks.db` and restart.

```bash
pytest -q
```
