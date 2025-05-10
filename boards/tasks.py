from celery import shared_task
from .sendemail import send_due_date_email_to_user
from logging import getLogger


# Initialize logger
logger = getLogger(__name__)

@shared_task
def send_task_due_email(email, task_name, due_date):
    logger.debug(f"DEBUG: Celery task triggered")
    logger.info(f"Email: {email}")
    logger.info(f"Task name: {task_name}")
    logger.info(f"Due date: {due_date}")
    try:
        send_due_date_email_to_user(email, task_name, due_date)
    except Exception as e:
        print(f"ERROR sending email: {e}")



# docker logs -f celery_worker



# @shared_task
# def send_task_due_email(email, task_name, due_date):
#     logger.debug(f"DEBUG: Celery task triggered============================================================================")
#     logger.info(f"Email ========================>>>: {email}")
#     logger.info(f"Task name ========================>>>:: {task_name}")
#     logger.info(f"Due date ========================>>>:: {due_date}")




# Django App Logs:
# docker logs -f django_app


# Redis Logs:
# docker logs -f redis


# Celery Worker Logs:
# docker logs -f celery_worker


# Celery Beat Logs (if applicable):
# docker logs -f celery_beat