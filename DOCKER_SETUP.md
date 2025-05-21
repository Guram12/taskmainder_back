# DOCKER SETUP GUIDE

This guide explains how to set up and run the Dockerized Django project with PostgreSQL, Redis, Celery, and Daphne.

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
│   │   ├── requirements.txt
│   │   ├── DOCKER_SETUP.md
│   │   ├── ...
```

---

## 3. Docker Configuration

### 3.1 Dockerfile
The `Dockerfile` defines how to build the Docker image for the Django application. It:

- Uses the official Python image.
- Installs dependencies from `requirements.txt`.
- Runs Daphne to serve the Django application.

### 3.2 docker-compose.yml
The `docker-compose.yml` file defines the services:

- **django**: Runs the Django application using Daphne.
- **postgres**: Provides the PostgreSQL database.
- **redis**: Provides a message broker for Celery and a channel layer for Django Channels.
- **celery_worker**: Executes background tasks.
- **celery_beat**: Manages periodic tasks.

---

## 4. Adding PostgreSQL to Docker

### 4.1 Update `docker-compose.yml`
Add the PostgreSQL service to your `docker-compose.yml` file:

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

  postgres:
    image: postgres:14
    container_name: postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: taskmainder
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

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

volumes:
  postgres_data:
```

---

### 4.2 Update `settings.py`
Update the `DATABASES` configuration in your Django `settings.py` file to use PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'taskmainder',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'postgres',  # Use the service name defined in docker-compose.yml
        'PORT': '5432',
    }
}
```

---

### 4.3 Install PostgreSQL Dependencies
Ensure that the `psycopg2` library (PostgreSQL adapter for Python) is included in your `requirements.txt` file:

```
psycopg2-binary
```

If it's not already there, add it and rebuild the Docker image:

```bash
docker-compose build
```

---

## 5. How to Build and Run the Project

### 5.1 Build the Docker Images
Run the following command to build the Docker images:

```bash
docker-compose build
```

### 5.2 Start the Services
Start all services (Django, PostgreSQL, Redis, Celery, etc.):

```bash
docker-compose up
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

## 8. Common Commands

### View Logs
```bash
docker-compose logs -f
```

### View Logs for a Specific Service
```bash
docker-compose logs django
```

### Restart a Specific Service
```bash
docker-compose restart django
```

### Check Running Containers
```bash
docker ps
```

---

## 9. Troubleshooting

### PostgreSQL Connection Issues
If you see errors like `connection refused` or `OperationalError`, ensure that:

1. The `postgres` service is running:
   ```bash
   docker ps
   ```

2. The `DATABASES` configuration in `settings.py` uses `postgres` as the `HOST`.

3. The PostgreSQL container is accessible. Check the logs:
   ```bash
   docker logs postgres
   ```

### Permission Denied Errors
If you encounter `PermissionError` when running Docker commands:

1. Add your user to the Docker group:
   ```bash
   sudo usermod -aG docker $USER
   ```

2. Log out and log back in, or run:
   ```bash
   newgrp docker
   ```

---

## 10. Notes on Persistent Data

The `postgres_data` volume ensures that your PostgreSQL data persists even if the container is stopped or removed. If you want to reset the database, remove the volume:

```bash
docker-compose down --volumes
```

---

## 11. Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Documentation](https://docs.docker.com/)