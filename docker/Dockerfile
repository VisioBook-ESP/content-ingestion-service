# image
FROM python:3.12-slim

# répertoire de travail
WORKDIR /app

# fichiers de dépendances
COPY requirements.txt .

# installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# installer ping et curl
RUN apt-get update && apt-get install -y iputils-ping curl && rm -rf /var/lib/apt/lists/*

# copier le reste du code
COPY ./src .

# port
EXPOSE 8080

# lancer le serveur FastAPI avec Uvicorn
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8080"]