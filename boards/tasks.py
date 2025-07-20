from celery import shared_task
from .sendemail import send_due_date_email_to_user
from .send_discord import send_discord_notification
from logging import getLogger
from accounts.models import CustomUser

logger = getLogger(__name__)


@shared_task
def send_task_due_email(task_id ,email, username, task_name, due_date ,priority):
    logger.debug(f"DEBUG: Celery task triggered")
    logger.info({
        "task_id": task_id,
        "email": email,
        "username": username,
        "task_name": task_name,
        "due_date": due_date,
        "priority": priority
    })
    try:
        from .models import Task
        
        task_exists = Task.objects.filter(id=task_id).exists()
        if not task_exists:
            logger.info(f"Task with ID '{task_id}' no longer exists. Skipping notification.")
            return

        user = CustomUser.objects.filter(email=email).first()
        if user and user.timezone:
            user_timezone = user.timezone
        else:
            user_timezone = 'UTC'

        # Check notification preference
        preference = getattr(user, 'notification_preference', 'email')
        if preference in ['email', 'both']:
            send_due_date_email_to_user(email, username, task_name, due_date, user_timezone, priority)
        if preference in ['discord', 'both'] and user.discord_webhook_url:
            message = f"⏰ Reminder: Task '{task_name}' is due on {due_date} (priority: {priority})"
            send_discord_notification(user.discord_webhook_url, message)
    except Exception as e:
        logger.error(f"ERROR sending notification: {e}")
# ====================================================================

# Django App Logs:
# docker logs -f django_app


# Redis Logs:
# docker logs -f redis


# Celery Worker Logs:
# docker logs -f celery_worker


# Celery Beat Logs (if applicable):
# docker logs -f celery_beat


# ====================================================================
from celery import shared_task
import os
from datetime import datetime
from django.core.management import call_command



@shared_task
def daily_db_dump():
    backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backup_data'))
    os.makedirs(backup_dir, exist_ok=True)
    filename = f"db_dump_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    filepath = os.path.join(backup_dir, filename)
    with open(filepath, 'w') as f:
        call_command('dumpdata', '--natural-foreign', '--natural-primary', '--indent', '2', stdout=f)









