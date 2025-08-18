# Dailydoer - Task Management Application

A full-featured task management application built with Django, featuring real-time collaboration, email, discord and push notifications.

## Features

### Authentication & User Management
- **User Registration & Login** - Email-based authentication with JWT tokens
- **Google OAuth Integration** - Sign in with Google account
- **GitHub OAuth Integration** - Sign in with GitHub account
- **Email Verification** - Mandatory email confirmation for new accounts
- **Password Management** - Password reset, change, and recovery
- **Profile Management** - Profile pictures, timezone settings, username/phone updates
- **Account Deletion** - Complete account removal with data cleanup

### Board & Task Management
- **Board Creation** - Create boards with custom names and background images
- **Template-based Board Creation** - Create boards from predefined templates
- **Real-time Collaboration** - WebSocket-based live updates using Django Channels
- **Task Organization** - Lists and tasks with drag-and-drop functionality
- **Task Assignment** - Assign tasks to multiple users
- **Task Priorities** - Color-coded priority system (green, orange, red)
- **Due Dates** - Set due dates with timezone support
- **Task Completion** - Mark tasks as completed

### Collaboration Features
- **Board Invitations** - Invite users via email with secure tokens
- **Role-based Access** - Owner, Admin, and Member roles
- **Real-time Updates** - Live synchronization of board changes
- **User Management** - Add/remove users from boards
- **Push Notifications** - Browser notifications for board activities

### Notification System
- **Email Notifications** - Task due date reminders, board invitations
- **Push Notifications** - Real-time browser notifications
- **Discord Notifications** - Task reminders sent to Discord channels via webhooks
- **In-app Notifications** - Notification center with read/unread status
- **Notification Management** - Mark as read, delete individual or all notifications
- **Notification Preferences** - Choose between email, Discord, or both notification types

## Tech Stack

### Backend
- **Django 4.2** - Web framework
- **Django REST Framework** - API development
- **Django Channels** - WebSocket support for real-time features
- **PostgreSQL** - Database (AWS RDS or local)
- **Redis** - Channel layer and Celery broker
- **Celery** - Background task processing with Celery Beat
- **JWT Authentication** - Token-based authentication
- **Daphne** - ASGI server for WebSocket support

### Cloud Services
- **AWS S3** - File storage for profile pictures and board backgrounds
- **AWS RDS** - PostgreSQL database hosting (production)
- **Brevo (SendinBlue)** - Email service provider

### Third-party Integrations
- **Google OAuth** - Social authentication
- **GitHub OAuth** - Social authentication with GitHub
- **Web Push API** - Browser push notifications
- **Discord Webhooks** - Send notifications to Discord channels
- **Timezone Support** - pytz for timezone handling

## Installation & Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.10+ (for local development)
- PostgreSQL (for local development)
- Redis (for local development)

### Docker Setup (Recommended)

1. **Clone the repository**
```bash
git clone <repository-url>
cd taskmainder
```

2. **Create Environment File**
Create a `.env` file in the project root with the following variables:
```env
# Database Configuration
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
AWS_S3_REGION_NAME=your_region

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Email Configuration (Brevo)
BREVO_EMAIL_HOST_USER=your_brevo_email
BREVO_EMAIL_HOST_PASSWORD=your_brevo_password
BREVO_API_KEY=your_brevo_api_key

# Push Notifications
VAPID_PRIVATE_KEY=your_vapid_private_key

# Django Settings
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,your_domain.com

# Frontend/Backend URLs
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
```

3. **Build and Run with Docker Compose**
```bash
docker-compose up --build
```

This will start:
- **Django Application** (port 8000) - Main web server with Daphne
- **Redis** (port 6379) - Message broker and channel layer
- **Celery Worker** - Background task processing
- **Celery Beat** - Scheduled task management

4. **Run Database Migrations**
```bash
docker-compose exec django python manage.py makemigrations
docker-compose exec django python manage.py migrate
```

5. **Create Superuser**
```bash
docker-compose exec django python manage.py createsuperuser
```

6. **Access the Application**
- API: http://localhost:8000
- Admin: http://localhost:8000/admin
- WebSocket: ws://localhost:8000/ws/board/{board_id}/

### Local Development Setup (Alternative)

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Start Redis**
```bash
redis-server
```

4. **Update settings for local development**
In `settings.py`, update the Redis and database configurations:
```python
# For local Redis
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('localhost', 6379)],
        },
    },
}

CELERY_BROKER_URL = 'redis://localhost:6379/0'
```

5. **Run the application**
```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Celery worker
celery -A taskmainder worker --loglevel=info

# Terminal 3: Celery beat
celery -A taskmainder beat --loglevel=info
```

## API Endpoints

### Authentication
- `POST /acc/register/` - User registration
- `POST /acc/login/` - User login
- `POST /acc/token/refresh/` - Token refresh
- `GET /acc/profile/` - User profile
- `PATCH /acc/profile/` - Update profile
- `POST /acc/social/login/token/` - Google OAuth login
- `POST /acc/social/github/login/` - GitHub OAuth login
- `POST /acc/password-reset/` - Password reset request
- `POST /acc/password-reset-confirm/<uidb64>/<token>/` - Password reset confirmation
- `PUT /acc/notification-preference/` - Update notification preferences
- `PUT /acc/discord-webhook-url/` - Update Discord webhook URL

### Boards
- `GET /api/boards/` - List user boards
- `POST /api/boards/` - Create board
- `GET /api/boards/{id}/` - Get board details
- `PUT /api/boards/{id}/` - Update board
- `DELETE /api/boards/{id}/` - Delete board
- `POST /api/boards/{id}/add_users/` - Add users to board
- `POST /api/boards/create-from-template/` - Create board from template

### Tasks & Lists
- `GET /api/tasks/` - List tasks
- `POST /api/tasks/` - Create task
- `PUT /api/tasks/{id}/` - Update task
- `DELETE /api/tasks/{id}/` - Delete task
- `GET /api/lists/` - List board lists
- `POST /api/lists/` - Create list

### Notifications
- `GET /api/notifications/` - Get user notifications
- `PATCH /api/notifications/mark-all-read/` - Mark all as read
- `DELETE /api/notifications/{id}/` - Delete notification
- `POST /api/save-subscription/` - Save push notification subscription

### WebSocket Endpoints
- `ws://localhost:8000/ws/board/{board_id}/` - Board real-time updates

## Docker Services

### Django Application
- **Image**: Python 3.10-slim based
- **Server**: Daphne ASGI server
- **Port**: 8000
- **Features**: REST API, WebSocket support, static/media file serving

### Redis
- **Image**: Redis 6.2
- **Port**: 6379
- **Purpose**: Message broker for Celery and channel layer for Django Channels

### Celery Worker
- **Purpose**: Background task processing
- **Tasks**: Email sending, file processing, notifications

### Celery Beat
- **Purpose**: Scheduled task management
- **Features**: Cron-like job scheduling, database backup scheduling

## Real-time Features

The application uses WebSocket connections for real-time collaboration:

### Supported Actions
- `move_task` - Move task between lists
- `add_task` - Add new task
- `update_task` - Update task details
- `delete_task` - Delete task
- `add_list` - Add new list
- `delete_list` - Delete list
- `reorder_lists` - Reorder lists
- `add_user` - Add user to board
- `delete_user` - Remove user from board
- `update_board_name` - Update board name

## Background Tasks

Celery handles background processing:
- **Email Notifications** - Task due date reminders
- **Discord Notifications** - Task reminders sent to Discord channels
- **Board Invitations** - Send invitation emails
- **Password Reset** - Send password reset emails
- **Push Notifications** - Browser notifications

### Discord Integration

The application supports Discord notifications for task reminders through webhooks:

#### Setting up Discord Webhooks
1. **Create a Discord Server** - Or use an existing server where you have admin permissions
2. **Create a Webhook**:
   - Go to Server Settings → Integrations → Webhooks
   - Click "New Webhook"
   - Choose the channel where notifications should be sent
   - Copy the webhook URL
3. **Configure in Application**:
   - Use the `/acc/discord-webhook-url/` endpoint to save your webhook URL
   - Set notification preference to 'discord' or 'both' via `/acc/notification-preference/`

#### Notification Types
- **Task Due Reminders** - Sent when tasks are approaching their due date
- **Format**: "⏰ Reminder: Task 'Task Name' is due on [Date] (priority: [High/Medium/Low])"

#### Notification Preferences
Users can choose their preferred notification method:
- **'email'** - Receive notifications via email only
- **'discord'** - Receive notifications via Discord only (requires webhook URL)
- **'both'** - Receive notifications via both email and Discord

## Security Features

- **JWT Authentication** - Secure token-based authentication
- **Email Verification** - Mandatory email confirmation
- **CORS Configuration** - Proper cross-origin resource sharing
- **Permission Classes** - Role-based access control
- **Secure File Upload** - AWS S3 integration for file storage
- **Environment Variables** - Sensitive data protection

## Deployment

### Production Environment Variables
```env
DEBUG=False
ALLOWED_HOSTS=your_domain.com,api.your_domain.com
CORS_ALLOWED_ORIGINS=https://your_domain.com,https://api.your_domain.com

# Production URLs
FRONTEND_URL=https://your_domain.com
BACKEND_URL=https://api.your_domain.com

# SSL Configuration
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')
```

### Docker Production Deployment
```bash
# Build for production
docker-compose -f docker-compose.prod.yml up --build -d

# Run migrations
docker-compose exec django python manage.py migrate

# Collect static files
docker-compose exec django python manage.py collectstatic --noinput
```

### Database Configuration
The application supports both local PostgreSQL and AWS RDS:
- **Local Development**: Use Docker PostgreSQL container
- **Production**: Use AWS RDS with environment variables

## Monitoring and Logs

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs django
docker-compose logs celery_worker
docker-compose logs celery_beat
```

