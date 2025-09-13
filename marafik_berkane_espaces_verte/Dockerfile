FROM python:3.10-slim

WORKDIR /app

# Installer les dépendances nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les requirements
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copier tout le projet
COPY . /app/

EXPOSE 8081

CMD ["python", "manage.py", "runserver", "0.0.0.0:8081"]
