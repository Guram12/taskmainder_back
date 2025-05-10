# DOCKER SETUP GUIDE

* This guide explains how to set up and run the Dockerized Django project with Redis, Celery, and Daphne.


## 1. Prerequisites
Before you begin, ensure the following are installed on your system:


* Docker: Install Docker
* Docker Compose: Install Docker Compose

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

## 3. Docker Configuration
The Dockerfile defines how to build the Docker image for the Django application. It:

### 3.1 Dockerfile

* Uses the official Python image.
* Installs dependencies from requirements.txt.
* Runs Daphne to serve the Django application.

### 3.2 docker-compose.yml
The docker-compose.yml file defines the services:

* django: Runs the Django application using Daphne.
* redis: Provides a message broker for Celery and a channel layer for Django Channels.
* celery_worker: Executes background tasks.
* celery_beat: Manages periodic tasks.



## 4. How to Build and Run the Project

### 4.1 Build the Docker Images
Run the following command to build the Docker images:

```
docker-compose build
```

### 4.2 Start the Services

```
docker-compose up
```


### 4.3 Access the Application
Open your browser and go to:

* http://localhost:8000 (if running locally).
* http://<your-ec2-public-ip>:8000 (if running on AWS EC2).


### 4.4 Stop the Services
To stop all running containers:

```
docker-compose down
```

## 5. Common Commands

* View Logs
```
docker-compose logs -f
```


* To view logs for a specific service (e.g., Django):
```
docker-compose logs django
```


* Restart a Specific Service
```
docker-compose restart celery_worker
```


* Check Running Containers

```
docker ps
```

## 6. Troubleshooting

If you see errors like ConnectionError: Error 111 connecting to 127.0.0.1:6379, ensure that:


* The CHANNEL_LAYERS in settings.py is configured to use redis as the hostname:

```
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('redis', 6379)],
        },
    },
}
```

### Permission Denied Errors
If you encounter PermissionError when running Docker commands:

* Add your user to the docker group:
```
sudo usermod -aG docker $USER
```

* Log out and log back in, or run:
```
newgrp docker
```








