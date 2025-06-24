FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Crear directorios necesarios
RUN mkdir -p ./data/raw ./data/processed

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]