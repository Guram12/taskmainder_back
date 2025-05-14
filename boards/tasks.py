from celery import shared_task
from .sendemail import send_due_date_email_to_user
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
        print(f"Task exists--------------->>>>>>>>>>: {task_exists}")
        if not task_exists:
            logger.info(f"Task with ID '{task_id}' no longer exists. Skipping email.")
            return 

        # Fetch the user's timezone from the database
        user = CustomUser.objects.filter(email=email).first()
        if user and user.timezone:
            logger.info(f"User timezone: {user.timezone}")
            user_timezone = user.timezone  # Use the user's specific timezone
        else:
            user_timezone = 'UTC'  # Fallback to UTC if no timezone is set

        # Pass the user's timezone to the email function
        send_due_date_email_to_user(email, username, task_name, due_date, user_timezone, priority)
    except Exception as e:
        logger.error(f"ERROR sending email: {e}")

# ====================================================================

# Django App Logs:
# docker logs -f django_app


# Redis Logs:
# docker logs -f redis


# Celery Worker Logs:
# docker logs -f celery_worker


# Celery Beat Logs (if applicable):
# docker logs -f celery_beat