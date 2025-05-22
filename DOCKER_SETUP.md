# DOCKER SETUP GUIDE

This guide explains how to set up and run the Dockerized Django project with PostgreSQL, Redis, Celery, and Daphne. It also explains how to configure the project to use either an **external database** (e.g., AWS RDS) or a **local PostgreSQL database** inside a Docker container.

---

## 1. Prerequisites
Before you begin, ensure the following are installed on your system:

- **Docker**: Install Docker
- **Docker Compose**: Install Docker Compose

---

## 2. Project Structure
Your project should have the following structure:

```
task_management_app/
├── task_back/
│   ├── taskmainder/
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   ├── docker_conf_for_local.yml
│   │   ├── requirements.txt
│   │   ├── DOCKER_SETUP.md
│   │   ├── ...
```

---

## 3. Docker Configuration

### 3.1 Using an External Database (e.g., AWS RDS)
If you are using an external database like AWS RDS, you **do not need the PostgreSQL container**. Instead, you should define the database credentials in the `environment` section of the `django` service in your `docker-compose.yml` file.

#### Example `docker-compose.yml` for External Database:
```yaml
version: '3.8'

services:
  django:
    build:
      context: .
    container_name: django_app
    command: daphne -b 0.0.0.0 -p 8000 taskmainder.asgi:application
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - DB_NAME=your_database_name
      - DB_USER=your_database_user
      - DB_PASSWORD=your_database_password
      - DB_HOST=your-rds-endpoint.amazonaws.com
      - DB_PORT=5432

  redis:
    image: redis:6.2
    container_name: redis
    ports:
      - "6379:6379"

  celery_worker:
    build:
      context: .
    container_name: celery_worker
    command: celery -A taskmainder worker --loglevel=info
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0

  celery_beat:
    build:
      context: .
    container_name: celery_beat
    command: celery -A taskmainder beat --loglevel=info
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
```

#### Update `settings.py` for External Database:
In your `settings.py`, configure the `DATABASES` setting to use environment variables:
```python
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', ''),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

---

### 3.2 Using a Local PostgreSQL Database Inside Docker
If you are running the database locally inside a Docker container, you should use the `docker_conf_for_local.yml` file. This file includes a `postgres` service to run PostgreSQL inside Docker.

#### Example `docker_conf_for_local.yml`:
```yaml
version: '3.8'

services:
  django:
    build:
      context: .
    container_name: django_app
    command: daphne -b 0.0.0.0 -p 8000 taskmainder.asgi:application
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - postgres
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - DB_NAME=taskmainder
      - DB_USER=postgres
      - DB_PASSWORD=postgres
      - DB_HOST=postgres
      - DB_PORT=5432

  redis:
    image: redis:6.2
    container_name: redis
    ports:
      - "6379:6379"

  celery_worker:
    build:
      context: .
    container_name: celery_worker
    command: celery -A taskmainder worker --loglevel=info
    depends_on:
      - redis
      - postgres
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0

  celery_beat:
    build:
      context: .
    container_name: celery_beat
    command: celery -A taskmainder beat --loglevel=info
    depends_on:
      - redis
      - postgres
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0

  postgres:
    image: postgres:14
    container_name: postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: taskmainder
    ports:
      - "5433:5432" 
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

#### Update `settings.py` for Local Database:
In your `settings.py`, configure the `DATABASES` setting to use the local PostgreSQL container:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'taskmainder',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'postgres',  # Service name in docker-compose
        'PORT': '5432',
    }
}
```

---

## 4. How to Switch Between External and Local Database

- **For External Database (e.g., AWS RDS)**:
  - Use the `docker-compose.yml` file.
  - Remove the `postgres` service and define the database credentials in the `environment` section of the `django` service.

- **For Local Database**:
  - Use the `docker_conf_for_local.yml` file.
  - Ensure the `postgres` service is included and the `DB_HOST` is set to `postgres`.

---

## 5. Running the Project

### 5.1 Build the Docker Images
Run the following command to build the Docker images:

```bash
docker-compose -f <compose-file>.yml build
```

Replace `<compose-file>` with either `docker-compose.yml` (for external database) or `docker_conf_for_local.yml` (for local database).

### 5.2 Start the Services
Start all services:

```bash
docker-compose -f <compose-file>.yml up
```

---

## 6. Running Migrations

After starting the containers, apply the migrations to set up the database schema:

```bash
docker exec -it django_app python manage.py migrate
```

---

## 7. Access the Application

- Open your browser and go to:
  - `http://localhost:8000` (if running locally).
  - `http://<your-ec2-public-ip>:8000` (if running on AWS EC2).

---

## 8. Notes on Persistent Data

- For the local PostgreSQL database, the `postgres_data` volume ensures that your data persists even if the container is stopped or removed.
- For the external database, data persistence is managed by the database provider (e.g., AWS RDS).

---

Let me know if you need further clarification!