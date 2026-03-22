# Mini-Task-Board

Делали вдвоём. Простенький клон Trello для практики парной работы и фронтенда (колонки, карточки, Flask + MongoDB, логин/регистрация).

Нужен **MongoDB** локально (по умолчанию `mongodb://127.0.0.1:27017`) или задай `MONGO_URI`. Для продакшена выставь `SECRET_KEY`.

```bash
pip install -r requirements.txt
python app.py
```

Открой http://127.0.0.1:5000 — зарегистрируйся или войди, потом доска.

Либо `docker compose up` — поднимет MongoDB и приложение вместе.

Тесты поднимают in-memory Mongo через `mongomock`, отдельный демон не нужен:

```bash
pytest -q
```
