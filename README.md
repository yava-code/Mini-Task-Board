# Mini-Task-Board

Делали вдвоём. Простенький клон Trello для практики парной работы и фронтенда (колонки, карточки, Flask + SQLite, логин/регистрация).

```bash
pip install -r requirements.txt
python app.py
```

Открой http://127.0.0.1:5000 — сначала визитка, потом регистрация/вход и доска на `/board`. Если база старая и падает при старте, удали `instance/tasks.db` и перезапусти.

```bash
pytest -q
```
