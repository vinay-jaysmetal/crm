# Jays Metal Backend - Overview

This is the backend for the Jays Metal webapplication, which is built with Django rest framework

This is a dockerized application

DockerFile
```
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

docker-compose.yml
```
version: '3.9'
services:
  web:
    build: .
    environment:
      - GUNICORN_WORKERS=3  # Optional: Use Gunicorn for production
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db

  db:
    image: postgres:15.12
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./deployment/nginx/nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - web

  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

.env
```
# DJANGO SETTINGS
SECRET_KEY='SECRETKEYHERE'
DEBUG=True
# DATA BASE SETTINGS
POSTGRES_DB=jaysmetal_db
POSTGRES_USER=postgres_user_here
POSTGRES_PASSWORD=PASSWORD_HERE
POSTGRES_HOST=db
```


Clerk – Initial data entry, job assignment, or documentation handling.

Shop – Internal shop work; possibly planning, material preparation, or initial job routing.

Cut – Raw material cutting (steel, metal sheets, etc.).

Fab (Fabrication) – Shaping metal sheets into the desired shape and size.

Delivery – Logistics team ships the fabricated items to the site.

Received – Client or site team confirms receipt of materials.

Erect – Final erection/installation of the delivered components at the construction site.
