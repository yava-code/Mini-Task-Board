FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd -m myuser

COPY --chown=myuser:myuser . .

EXPOSE 5000

USER myuser

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]